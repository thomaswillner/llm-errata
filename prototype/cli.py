"""The `errata` command line, over an on-disk workspace.

    python3 -m prototype.cli --help

ROADMAP.md Phase 2 lists the control plane as a CLI rather than a library,
because the thing being demonstrated is an *inter-organisation* contract. If
the only way to run a repair is to import Python, the contract is not
implementable by anyone who does not already share this codebase.

Exit codes are part of the interface:

    0  the operation succeeded and, where an aggregate applies, it is verified
    1  the operation was refused, or a probe or verification failed
    2  inconclusive: the repair ran but coverage is not verified

`2` is not a lesser `1`. It means the work was done and the result cannot be
called success, which is the whole point of the proposal and the reason it is a
distinct code rather than a warning on stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from prototype.adapters import Coverage, OpaqueAdapter
from prototype.controller import Importer, Phase
from prototype.errata import Erratum, FeedError, Operation, RootRegistry, read_feed
from prototype.lineage import LineageLedger
from prototype.receipts import Receipt
from prototype.schema import load as load_schema, validate as validate_schema
from prototype.signing import Ed25519Signer
from prototype.sqlite_store import SqliteAdapter
from prototype.workspace import Workspace


EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_INCONCLUSIVE = 2


def _importer(ws: Workspace) -> tuple[Importer, SqliteAdapter]:
    ledger = ws.load_lineage()
    store = SqliteAdapter(ws.store_path, ledger, name="sqlite")
    adapters: list[object] = [store]
    if ws.config().get("opaque_store", True):
        adapters.append(OpaqueAdapter(name="prompt_cache"))
    importer = Importer(
        ws.config().get("importer", "importer-1"),
        ledger=ledger,
        adapters=adapters,
        signer=ws.importer_signer(),
        owner=ws.owner_verification_key(),
        roots=RootRegistry(ledger.roots_seen()),
    )
    importer.last_sequence = ws.last_applied_sequence()
    for root, sequence in ws.applied().items():
        importer._applied[root] = sequence
    return importer, store


def cmd_init(ws: Workspace, args: argparse.Namespace) -> int:
    ws.initialise()
    print(f"workspace ready at {ws.root.name}/")
    print("  identity/owner.pub   published verification key")
    print("  feeds/errata.jsonl   the append-only correction channel")
    print("  registry/lineage.jsonl  what descends from what")
    print("  store.sqlite3        the importer's own state")
    return EXIT_OK


def cmd_export(ws: Workspace, args: argparse.Namespace) -> int:
    ws.add_import(args.root, args.artifact or f"fact:{args.root}", args.content)
    print(f"imported {args.root} as an artifact carrying: {args.content!r}")
    return EXIT_OK


def cmd_derive(ws: Workspace, args: argparse.Namespace) -> int:
    ws.add_derivation(args.artifact, tuple(args.inputs), args.content)
    print(f"derived {args.artifact} from {', '.join(args.inputs)}")
    return EXIT_OK


def cmd_publish(ws: Workspace, args: argparse.Namespace) -> int:
    operation = Operation(args.operation)
    postconditions = {"negative": args.negative, "preserve": args.preserve}
    if operation is not Operation.ERASE:
        if not args.positive:
            print(
                "refused: correction and supersession require --positive, because "
                "the positive leg of the repair triad cannot otherwise be checked",
                file=sys.stderr,
            )
            return EXIT_REFUSED
        postconditions["positive"] = args.positive

    erratum = Erratum(
        erratum_id=args.id or f"err_{ws.next_sequence():04d}",
        sequence=args.sequence or ws.next_sequence(),
        target_root=args.root,
        operation=operation,
        valid_from=args.valid_from,
        replacement=args.replacement,
        postconditions=postconditions,
    )
    signed = ws.owner_signer().sign_erratum(erratum)

    errors = validate_schema(signed.signable(), load_schema("erratum"))
    if errors:
        print("refused: the erratum does not satisfy the published schema:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return EXIT_REFUSED

    ws.append_erratum(signed)
    print(f"published {signed.erratum_id} at sequence {signed.sequence}")
    return EXIT_OK


def cmd_pull(ws: Workspace, args: argparse.Namespace) -> int:
    errata = read_feed(ws.feed_path.read_text(encoding="utf-8"))
    pending = [e for e in errata if e.sequence > ws.last_applied_sequence()]
    print(f"{len(errata)} in the feed, {len(pending)} not yet applied")
    for e in pending:
        print(f"  {e.sequence}  {e.operation.value:<9} {e.target_root}  {e.erratum_id}")
    return EXIT_OK


def cmd_plan(ws: Workspace, args: argparse.Namespace) -> int:
    importer, store = _importer(ws)
    try:
        errata = read_feed(ws.feed_path.read_text(encoding="utf-8"))
        pending = [e for e in errata if e.sequence > importer.last_sequence]
        if not pending:
            print("nothing to do")
            return EXIT_OK
        for e in pending:
            descendants = store.enumerate(e.target_root)
            print(f"{e.erratum_id}: {e.operation.value} {e.target_root}")
            for artifact_id in descendants:
                print(f"  would gate and dispose {artifact_id}")
            print("  prompt_cache: cannot enumerate, coverage will be unknown")
        return EXIT_OK
    finally:
        store.close()


def cmd_repair(ws: Workspace, args: argparse.Namespace) -> int:
    importer, store = _importer(ws)
    try:
        errata = read_feed(ws.feed_path.read_text(encoding="utf-8"))
        pending = [e for e in errata if e.sequence > importer.last_sequence]
        if not pending:
            print("nothing to repair")
            return EXIT_OK

        last: Receipt | None = None
        for erratum in pending:
            try:
                last = importer.repair(erratum)
            except FeedError as error:
                print(f"refused: {error}", file=sys.stderr)
                return EXIT_REFUSED
            ws.write_receipt(last)
            ws.record_applied(last.target_root, last.sequence)

        assert last is not None
        for event in importer.journal:
            if event.phase in (Phase.QUARANTINE_COMPLETE, Phase.TEST):
                print(f"  {event.phase.value}: {event.detail}")
        print(f"aggregate: {last.aggregate.value}")
        for limitation in last.limitations:
            print(f"limitation: {limitation}")
        return EXIT_OK if last.aggregate is Coverage.VERIFIED else EXIT_INCONCLUSIVE
    finally:
        store.close()


def cmd_test(ws: Workspace, args: argparse.Namespace) -> int:
    receipt = ws.latest_receipt()
    if receipt is None:
        print("no receipt yet; run repair first", file=sys.stderr)
        return EXIT_REFUSED
    for leg, result in receipt["triad"].items():
        print(f"  {leg:<9} {result}")
    failed = [leg for leg, result in receipt["triad"].items() if result != "pass"]
    return EXIT_REFUSED if failed else EXIT_OK


def cmd_attest(ws: Workspace, args: argparse.Namespace) -> int:
    receipt = ws.latest_receipt()
    if receipt is None:
        print("no receipt yet; run repair first", file=sys.stderr)
        return EXIT_REFUSED
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return EXIT_OK if receipt["aggregate"] == "verified" else EXIT_INCONCLUSIVE


def cmd_audit(ws: Workspace, args: argparse.Namespace) -> int:
    receipt = ws.latest_receipt()
    if receipt is None:
        print("no receipt yet; run repair first", file=sys.stderr)
        return EXIT_REFUSED
    if args.json:
        print(json.dumps(receipt, sort_keys=True))
        return EXIT_OK if receipt["aggregate"] == "verified" else EXIT_INCONCLUSIVE
    print(f"erratum   {receipt['erratum_id']} (sequence {receipt['sequence']})")
    print(f"operation {receipt['operation']}")
    print("stores")
    for store, coverage in sorted(receipt["stores"].items()):
        print(f"  {store:<14} {coverage}")
    print(f"aggregate {receipt['aggregate'].upper()}")
    for limitation in receipt["limitations"]:
        print(f"  {limitation}")
    return EXIT_OK if receipt["aggregate"] == "verified" else EXIT_INCONCLUSIVE


def cmd_verify(ws: Workspace, args: argparse.Namespace) -> int:
    """Check every receipt against the published key and the published schema."""

    receipts = ws.all_receipts()
    if not receipts:
        print("no receipts to verify", file=sys.stderr)
        return EXIT_REFUSED

    key = ws.importer_verification_key()
    schema = load_schema("receipt")
    bad = 0
    for name, payload in receipts:
        errors = validate_schema(payload, schema)
        signature = payload.get("signature")
        rebuilt = Receipt(
            importer=payload["importer"],
            erratum_id=payload["erratum_id"],
            sequence=payload["sequence"],
            target_root=payload["target_root"],
            operation=payload["operation"],
            pre_state_root=payload["pre_state_root"],
            post_state_root=payload["post_state_root"],
            stores={k: Coverage(v) for k, v in payload["stores"].items()},
            dispositions=payload["dispositions"],
            triad=payload["triad"],
            aggregate=Coverage(payload["aggregate"]),
            limitations=payload["limitations"],
            history_retained=payload["history_retained"],
            adapter_versions=payload["adapter_versions"],
            signature=signature,
        )
        ok = rebuilt.verify(key)
        status = "ok" if ok and not errors else "BAD"
        if not ok or errors:
            bad += 1
        print(f"  {name}: signature={'ok' if ok else 'INVALID'} schema="
              f"{'ok' if not errors else errors[0]} -> {status}")
    return EXIT_OK if bad == 0 else EXIT_REFUSED


COMMANDS = {
    "init": cmd_init,
    "export": cmd_export,
    "derive": cmd_derive,
    "publish": cmd_publish,
    "pull": cmd_pull,
    "plan": cmd_plan,
    "repair": cmd_repair,
    "test": cmd_test,
    "attest": cmd_attest,
    "audit": cmd_audit,
    "verify": cmd_verify,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="errata",
        description=(
            "Repair derived AI memory after a correction, supersession, or "
            "erasure. Exit 2 means the repair ran and the result is not verified."
        ),
    )
    parser.add_argument("--workspace", default=".errata", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="create the workspace")

    export = sub.add_parser("export", help="record an imported memory root")
    export.add_argument("--root", required=True)
    export.add_argument("--content", required=True)
    export.add_argument("--artifact")

    derive = sub.add_parser("derive", help="record a derived artifact")
    derive.add_argument("--artifact", required=True)
    derive.add_argument("--inputs", required=True, nargs="+")
    derive.add_argument("--content", required=True)

    publish = sub.add_parser("publish", help="sign and append an erratum")
    publish.add_argument("--root", required=True)
    publish.add_argument(
        "--operation", required=True, choices=[o.value for o in Operation]
    )
    publish.add_argument("--replacement")
    publish.add_argument("--negative", default="the retired value")
    publish.add_argument("--positive")
    publish.add_argument("--preserve", default="unrelated memory")
    publish.add_argument("--valid-from", dest="valid_from", default="2026-08-01T00:00:00Z")
    publish.add_argument("--id")
    publish.add_argument("--sequence", type=int)

    sub.add_parser("pull", help="list errata not yet applied")
    sub.add_parser("plan", help="show what a repair would touch, without touching it")
    sub.add_parser("repair", help="quarantine, rebuild, probe, and attest")
    sub.add_parser("test", help="show the repair triad from the latest receipt")
    sub.add_parser("attest", help="print the latest receipt")

    audit = sub.add_parser("audit", help="summarise the latest receipt")
    audit.add_argument("--json", action="store_true")

    sub.add_parser("verify", help="check every receipt's signature and schema")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    ws = Workspace(args.workspace)
    if args.command != "init" and not ws.exists():
        print(
            f"no workspace at {args.workspace}; run `errata init` first",
            file=sys.stderr,
        )
        return EXIT_REFUSED
    return COMMANDS[args.command](ws, args)


if __name__ == "__main__":
    sys.exit(main())
