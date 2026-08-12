"""The CLI, end to end through a subprocess.

Driven as a real command, not by importing `main`, because the point of a CLI
here is that the contract is implementable by someone who does not share this
codebase. Exit codes are part of that contract and are asserted everywhere.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SEMANTIC_FIXTURES = REPO_ROOT / "spec" / "semantic"

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_INCONCLUSIVE = 2


class CliCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="errata-cli-")
        self.cwd = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "prototype.cli", "--workspace", ".errata", *args],
            cwd=self.cwd,
            capture_output=True,
            text=True,
            check=False,
            env={"PYTHONPATH": str(REPO_ROOT), "PATH": "/usr/bin:/bin"},
        )

    def seed(self) -> None:
        self.assertEqual(self.run_cli("init").returncode, EXIT_OK)
        self.run_cli("export", "--root", "mem_01HX", "--artifact", "fact:diet",
                     "--content", "is vegetarian")
        self.run_cli("export", "--root", "mem_02KP", "--artifact", "fact:venue",
                     "--content", "prefers quiet restaurants")
        self.run_cli("derive", "--artifact", "summary:dining",
                     "--inputs", "fact:diet", "fact:venue",
                     "--content", "is vegetarian; prefers quiet restaurants")

    def publish_supersession(self) -> subprocess.CompletedProcess[str]:
        return self.run_cli(
            "publish", "--root", "mem_01HX", "--operation", "supersede",
            "--replacement", "eats meat again", "--negative", "vegetarian",
            "--positive", "eats meat again", "--preserve", "quiet restaurants",
        )


class WorkspaceLifecycle(CliCase):
    def test_commands_refuse_before_init(self) -> None:
        result = self.run_cli("repair")
        self.assertEqual(result.returncode, EXIT_REFUSED)
        self.assertIn("errata init", result.stderr)

    def test_init_publishes_only_the_public_key(self) -> None:
        self.run_cli("init")
        published = (self.cwd / ".errata" / "identity" / "owner.pub").read_text().strip()
        self.assertEqual(len(published), 64, "an Ed25519 public key is 32 bytes")
        self.assertNotIn(published, (self.cwd / ".errata" / "identity" / "owner.seed").read_text())


class PublishRefusesIllFormedErrata(CliCase):
    def test_supersession_without_a_positive_postcondition_is_refused(self) -> None:
        self.seed()
        result = self.run_cli(
            "publish", "--root", "mem_01HX", "--operation", "supersede",
            "--replacement", "eats meat again",
        )
        self.assertEqual(result.returncode, EXIT_REFUSED)
        self.assertIn("--positive", result.stderr)

    def test_erasure_needs_no_positive(self) -> None:
        self.seed()
        result = self.run_cli(
            "publish", "--root", "mem_01HX", "--operation", "erase",
            "--negative", "vegetarian", "--preserve", "quiet restaurants",
        )
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)

    def test_the_published_erratum_satisfies_the_published_schema(self) -> None:
        self.seed()
        self.publish_supersession()
        line = (self.cwd / ".errata" / "feeds" / "errata.jsonl").read_text().strip()
        payload = json.loads(line)
        self.assertIn("signature", payload)
        self.assertEqual(len(payload["signature"]), 128)


class RepairReportsHonestly(CliCase):
    def test_repair_exits_inconclusive_rather_than_claiming_success(self) -> None:
        self.seed()
        self.publish_supersession()
        result = self.run_cli("repair")
        self.assertEqual(result.returncode, EXIT_INCONCLUSIVE, result.stdout + result.stderr)
        self.assertIn("prompt_cache", result.stdout)

    def test_all_three_probes_pass_even_though_the_aggregate_does_not(self) -> None:
        # The distinction the whole proposal turns on: the repair worked, and
        # the result is still not `verified`.
        self.seed()
        self.publish_supersession()
        self.run_cli("repair")
        result = self.run_cli("test")
        self.assertEqual(result.returncode, EXIT_OK, result.stdout)
        self.assertNotIn("fail", result.stdout)

    def test_audit_json_is_machine_readable_and_not_green(self) -> None:
        self.seed()
        self.publish_supersession()
        self.run_cli("repair")
        result = self.run_cli("audit", "--json")
        self.assertEqual(result.returncode, EXIT_INCONCLUSIVE)
        payload = json.loads(result.stdout)
        self.assertNotEqual(payload["aggregate"], "verified")
        self.assertEqual(payload["stores"]["prompt_cache"], "unknown")

    def test_the_substrate_scan_reaches_the_receipt(self) -> None:
        # The SQLite store keeps the retired value in its write-ahead log after
        # the row is gone, so a repair that satisfied every probe still cannot
        # report a clean store.
        self.seed()
        self.publish_supersession()
        self.run_cli("repair")
        payload = json.loads(self.run_cli("audit", "--json").stdout)
        self.assertEqual(payload["stores"]["sqlite"], "failed")

    def test_plan_changes_nothing(self) -> None:
        # Asserted on behaviour rather than on file bytes: opening a SQLite
        # database legitimately touches its journal, so comparing bytes would
        # fail for a reason that has nothing to do with whether a repair ran.
        self.seed()
        self.publish_supersession()
        result = self.run_cli("plan")
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertIn("would gate", result.stdout)
        self.assertEqual(list((self.cwd / ".errata" / "receipts").glob("*.json")), [])
        self.assertEqual(
            json.loads((self.cwd / ".errata" / "registry" / "applied.json").read_text()),
            {},
            "plan recorded an applied erratum",
        )
        # And the erratum is still pending afterwards.
        self.assertIn("1 not yet applied", self.run_cli("pull").stdout)


class ReceiptsAreVerifiable(CliCase):
    def test_a_genuine_receipt_verifies(self) -> None:
        self.seed()
        self.publish_supersession()
        self.run_cli("repair")
        self.assertEqual(self.run_cli("verify").returncode, EXIT_OK)

    def test_a_tampered_aggregate_is_caught(self) -> None:
        self.seed()
        self.publish_supersession()
        self.run_cli("repair")
        path = sorted((self.cwd / ".errata" / "receipts").glob("*.json"))[0]
        payload = json.loads(path.read_text())
        payload["aggregate"] = "verified"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True))
        result = self.run_cli("verify")
        self.assertEqual(result.returncode, EXIT_REFUSED)
        self.assertIn("INVALID", result.stdout)

    def test_verify_refuses_when_there_is_nothing_to_verify(self) -> None:
        self.seed()
        self.assertEqual(self.run_cli("verify").returncode, EXIT_REFUSED)


class FeedIntegrityHoldsThroughTheCli(CliCase):
    def test_a_forged_erratum_in_the_feed_is_refused(self) -> None:
        self.seed()
        self.publish_supersession()
        feed = self.cwd / ".errata" / "feeds" / "errata.jsonl"
        payload = json.loads(feed.read_text().strip())
        payload["replacement"] = "eats only pineapple"
        feed.write_text(json.dumps(payload, sort_keys=True) + "\n")
        result = self.run_cli("repair")
        self.assertEqual(result.returncode, EXIT_REFUSED)
        self.assertIn("signature", result.stderr)

    def test_a_second_repair_finds_nothing_to_do(self) -> None:
        self.seed()
        self.publish_supersession()
        self.run_cli("repair")
        result = self.run_cli("repair")
        self.assertEqual(result.returncode, EXIT_OK)
        self.assertIn("nothing to repair", result.stdout)


class SemanticProbeConformance(CliCase):
    def semantic_test(
        self, case: str | None = None, *extra: str
    ) -> subprocess.CompletedProcess[str]:
        arguments = [
            "semantic-test",
            "--probes", str(SEMANTIC_FIXTURES / "probes.json"),
            "--config", str(SEMANTIC_FIXTURES / "verifier-config.json"),
            "--observations", str(SEMANTIC_FIXTURES / "observations.json"),
        ]
        if case is not None:
            arguments.extend(("--case", case))
        return self.run_cli(*arguments, *extra)

    def test_checked_in_cases_return_coverage_exit_codes_and_limitations(self) -> None:
        expected = {
            "verified-correction": (EXIT_OK, "verified", None),
            "failed-supersession": (EXIT_REFUSED, "failed", None),
            "unknown-erasure": (EXIT_INCONCLUSIVE, "unknown", "inconclusive"),
            "provider-error": (EXIT_INCONCLUSIVE, "unknown", "returned error"),
            "missing-response": (EXIT_INCONCLUSIVE, "unknown", "missing required observation"),
            "duplicate-response": (EXIT_INCONCLUSIVE, "unknown", "duplicate observations"),
            "configuration-drift": (EXIT_INCONCLUSIVE, "unknown", "configuration drift"),
            "nonconforming-output": (EXIT_INCONCLUSIVE, "unknown", "operation mismatch"),
        }
        for case, (exit_code, coverage, limitation) in expected.items():
            with self.subTest(case=case):
                result = self.semantic_test(case)
                self.assertEqual(result.returncode, exit_code, result.stderr)
                self.assertEqual(result.stderr, "")
                self.assertNotIn("\n", result.stdout.rstrip("\n"))
                report = json.loads(result.stdout)
                self.assertEqual(report["coverage"], coverage)
                if limitation is not None:
                    self.assertTrue(
                        any(limitation in item for item in report["limitations"]),
                        report["limitations"],
                    )
                self.assertEqual(
                    result.stdout,
                    json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n",
                )

    def test_exact_documented_invocation_defaults_to_verified_correction(self) -> None:
        result = self.semantic_test()
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertEqual(json.loads(result.stdout)["coverage"], "verified")

    def test_semantic_test_refuses_malformed_input_without_traceback(self) -> None:
        bad_observations = self.cwd / "bad-observations.json"
        bad_observations.write_text("{not json", encoding="utf-8")
        result = self.run_cli(
            "semantic-test",
            "--probes", str(SEMANTIC_FIXTURES / "probes.json"),
            "--config", str(SEMANTIC_FIXTURES / "verifier-config.json"),
            "--observations", str(bad_observations),
            "--case", "verified-correction",
        )
        self.assertEqual(result.returncode, EXIT_REFUSED)
        self.assertIn("invalid input", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
