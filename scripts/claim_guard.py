#!/usr/bin/env python3
"""Anchored guard for the LLM Errata bounded claim.

`validate_repo.py` is a linter: it checks that files, links, encodings, and
metadata are well formed. It deliberately does **not** decide whether the
proposal still says what it is supposed to say.

This guard does. Its checks are anchored to exact sentences in named files and
to affirmative-overclaim patterns, because keyword-presence checks over the
concatenated corpus cannot distinguish a hedge from its inversion: a document
asserting "this is the world first, and it is clearly patentable" still
contains the strings "world first" and "patentability".

Exit codes
    0  every guard passed
    1  a guard failed: the corpus no longer states the bounded claim
    2  inconclusive: a guarded file is missing or unreadable, so the guard
       could not evaluate the claim at all. Never treat this as a pass.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_INCONCLUSIVE = 2


# --------------------------------------------------------------------------
# Anchors: exact text that must survive verbatim in a named file.
# Removing or softening any of these changes the published claim.
# --------------------------------------------------------------------------

ANCHORS: tuple[tuple[str, str, str], ...] = (
    (
        "README.md",
        "**An imported memory is a dependency, not a copy.**",
        "core thesis",
    ),
    (
        "IDEA.md",
        "**An imported memory is a dependency, not a copy.**",
        "core thesis",
    ),
    (
        "AGENTS.md",
        "**An imported memory is a dependency, not a copy.**",
        "core thesis restated as an agent rule",
    ),
    (
        "AGENTS.md",
        "Quarantine always precedes repair.",
        "quarantine-before-repair invariant",
    ),
    (
        "PRIOR_ART.md",
        "This is a **novel synthesis with a narrow, apparently unimplemented "
        "conformance gap**. The public evidence does not support claims of a "
        "world first, patentability, non-infringement, legal priority, or "
        "freedom to operate.",
        "bounded novelty statement",
    ),
    (
        "RESEARCH.md",
        "No reviewed public implementation or normative profile was found to "
        "require that complete conjunction as of 2026-08-01.",
        "dated, falsifiable form of the novelty claim",
    ),
    (
        "IDEA.md",
        "`pending` is a lifecycle state, not a successful coverage result.",
        "pending is not terminal success",
    ),
    (
        "IDEA.md",
        "Aggregate success requires every required store to be `verified`.",
        "no green aggregate over unknown coverage",
    ),
    (
        "IDEA.md",
        "Signature validity authenticates the importer and receipt bytes; it does not establish that the reported coverage is truthful.",
        "signature authenticity boundary",
    ),
    (
        "IDEA.md",
        "Coverage truthfulness requires the signed stores, aggregate, and limitations to match the declared required scope without upgrading missing or opaque evidence.",
        "coverage truthfulness boundary",
    ),
    (
        "PRIOR_ART.md",
        "## What would invalidate the claim",
        "falsifier section",
    ),
    (
        "RESEARCH.md",
        "## Falsifiers and update policy",
        "falsifier section",
    ),
)


# --------------------------------------------------------------------------
# Ordering: quarantine must be specified before repair, not merely mentioned
# in the same document.
# --------------------------------------------------------------------------

ORDERINGS: tuple[tuple[str, str, str, str], ...] = (
    (
        "IDEA.md",
        "2. **Quarantine.**",
        "3. **Rebuild.**",
        "the loop must quarantine before it rebuilds",
    ),
    (
        "README.md",
        "2. **Quarantine:**",
        "3. **Rebuild:**",
        "the summarised loop must quarantine before it rebuilds",
    ),
)


# --------------------------------------------------------------------------
# Forbidden: affirmative overclaims. Written narrowly so that the repository's
# own prohibitions ("Never claim a world first", "not a claim of
# patentability") do not match their own subject matter.
# --------------------------------------------------------------------------

FORBIDDEN: tuple[tuple[str, str], ...] = (
    (
        r"\bis\s+(?:the\s+)?\**\s*world[-\s]first\b",
        "asserts a world first",
    ),
    (
        r"\b(?:is|are)\s+(?:clearly\s+|obviously\s+|certainly\s+|plainly\s+)?"
        r"patentable\b",
        "asserts patentability",
    ),
    (
        r"\b(?:we|this|it)\s+invented\b",
        "asserts invention of a prior-art mechanism",
    ),
    (
        r"\bfreedom\s+to\s+operate\s+(?:is|has\s+been)\s+"
        r"(?:established|confirmed|cleared)\b",
        "asserts freedom to operate",
    ),
    (
        r"\bproves?\s+(?:that\s+)?(?:the\s+)?(?:memory|deletion|erasure)\s+"
        r"(?:is|was)\s+complete\b",
        "asserts proof of complete deletion",
    ),
    (
        r"\bmathematically\s+prove[sd]?\s+(?:semantic\s+)?absence\b",
        "asserts mathematical proof of semantic absence",
    ),
)

GUARDED_FILES = ("README.md", "IDEA.md", "RESEARCH.md", "PRIOR_ART.md", "AGENTS.md")


# Reviewed exceptions: lines that quote forbidden wording in order to reject it.
# Each entry is pinned to its exact text, so editing the line withdraws the
# exception and the guard fires again. Exceptions are printed, never silent.
ALLOWED_QUOTATIONS: tuple[tuple[str, str, str], ...] = (
    (
        "RESEARCH.md",
        "- A claim that behavioral probes can mathematically prove semantic absence.",
        "listed under Excluded scope, i.e. explicitly disclaimed",
    ),
    (
        "RESEARCH.md",
        "- “The concept is patentable, non-infringing, or free to operate.”",
        "quoted in the list of formulations the research does not support",
    ),
)


class Guard:
    def __init__(self) -> None:
        self.passed = 0
        self.failures: list[str] = []
        self.blocked: list[str] = []

    def ok(self, name: str, detail: str) -> None:
        self.passed += 1
        print(f"[PASS] {name}: {detail}")

    def fail(self, name: str, detail: str, fix: str) -> None:
        self.failures.append(name)
        print(f"[FAIL] {name}: {detail}")
        print(f"       Fix: {fix}")

    def block(self, name: str, detail: str) -> None:
        self.blocked.append(name)
        print(f"[INCONCLUSIVE] {name}: {detail}")

    def finish(self) -> int:
        total = self.passed + len(self.failures) + len(self.blocked)
        if self.blocked:
            print(
                f"\nClaim guard inconclusive: {len(self.blocked)} of {total} guards "
                f"could not be evaluated ({', '.join(self.blocked)}). "
                "This is not a pass."
            )
            return EXIT_INCONCLUSIVE
        if self.failures:
            print(
                f"\nClaim guard failed: {len(self.failures)} of {total} guards failed "
                f"({', '.join(self.failures)})."
            )
            return EXIT_FAIL
        print(f"\nClaim guard passed: all {total} guards succeeded.")
        return EXIT_OK


def load(guard: Guard, name: str) -> str | None:
    path = ROOT / name
    if not path.is_file():
        guard.block(f"read {name}", "guarded file is missing")
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        guard.block(f"read {name}", f"guarded file is unreadable: {error}")
        return None


def normalise(text: str) -> str:
    """Collapse whitespace so a reflowed paragraph still matches its anchor."""

    return re.sub(r"\s+", " ", text)


def check_anchors(guard: Guard, documents: dict[str, str]) -> None:
    for name, anchor, why in ANCHORS:
        text = documents.get(name)
        if text is None:
            continue
        if normalise(anchor) in normalise(text):
            guard.ok(f"anchor — {name} ({why})", "exact text is present")
        else:
            guard.fail(
                f"anchor — {name} ({why})",
                "required text is absent or altered",
                f"Restore this text verbatim in {name}: {anchor!r}",
            )


def check_orderings(guard: Guard, documents: dict[str, str]) -> None:
    for name, earlier, later, why in ORDERINGS:
        text = documents.get(name)
        if text is None:
            continue
        first = text.find(earlier)
        second = text.find(later)
        if first == -1 or second == -1:
            guard.fail(
                f"ordering — {name} ({why})",
                f"could not locate {earlier!r} and {later!r}",
                f"Restore the numbered loop steps in {name}.",
            )
        elif first < second:
            guard.ok(f"ordering — {name} ({why})", f"{earlier} precedes {later}")
        else:
            guard.fail(
                f"ordering — {name} ({why})",
                f"{later} appears before {earlier}",
                f"Reorder the loop in {name} so quarantine precedes rebuild.",
            )


def check_forbidden(guard: Guard, documents: dict[str, str]) -> None:
    exceptions = {(name, text) for name, text, _ in ALLOWED_QUOTATIONS}
    used: set[tuple[str, str]] = set()

    for pattern, why in FORBIDDEN:
        compiled = re.compile(pattern, re.IGNORECASE)
        hits: list[str] = []
        for name in GUARDED_FILES:
            text = documents.get(name)
            if text is None:
                continue
            for line_number, line in enumerate(text.splitlines(), start=1):
                if not compiled.search(line):
                    continue
                if (name, line.strip()) in exceptions:
                    used.add((name, line.strip()))
                    continue
                hits.append(f"{name}:{line_number}")
        if hits:
            guard.fail(
                f"overclaim — {why}",
                "matched at " + ", ".join(hits),
                "Restore bounded wording. Public-source research cannot establish "
                "universal nonexistence, patentability, or freedom to operate.",
            )
        else:
            guard.ok(f"overclaim — {why}", "no affirmative overclaim found")

    stale = [
        f"{name}: {text!r}"
        for name, text, _ in ALLOWED_QUOTATIONS
        if (name, text) not in used
    ]
    if stale:
        guard.fail(
            "reviewed exceptions",
            "declared exceptions no longer match any line: " + "; ".join(stale),
            "Remove the obsolete entry from ALLOWED_QUOTATIONS, or restore the "
            "line it was reviewed against. A stale exception silently widens "
            "what the guard permits.",
        )
    else:
        for name, text, why in ALLOWED_QUOTATIONS:
            print(f"[ALLOW] {name}: {why} — {text!r}")
        guard.ok(
            "reviewed exceptions",
            f"{len(ALLOWED_QUOTATIONS)} quotation exceptions all still anchored",
        )


def main() -> int:
    guard = Guard()
    print(f"Guarding the LLM Errata bounded claim: {ROOT.name}\n")

    names = sorted({name for name, *_ in ANCHORS} | {name for name, *_ in ORDERINGS} | set(GUARDED_FILES))
    documents: dict[str, str] = {}
    for name in names:
        text = load(guard, name)
        if text is not None:
            documents[name] = text

    check_anchors(guard, documents)
    check_orderings(guard, documents)
    check_forbidden(guard, documents)
    return guard.finish()


if __name__ == "__main__":
    sys.exit(main())
