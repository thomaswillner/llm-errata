"""The demo is the deliverable, so its headline result is a test.

If a future change ever lets this exit zero, either the opaque adapter stopped
being required or the aggregation rule stopped being honest. Both should be a
loud failure rather than a quietly nicer-looking demo.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from prototype.adapters import Coverage
from prototype.receipts import aggregate_coverage


REPO_ROOT = Path(__file__).resolve().parents[1]

ALL_PASS = {"negative": "pass", "positive": "pass", "preserve": "pass"}


class AggregationRefusesToRoundUp(unittest.TestCase):
    def test_all_verified_aggregates_to_verified(self) -> None:
        stores = {"markdown": Coverage.VERIFIED, "vector": Coverage.VERIFIED}
        self.assertEqual(aggregate_coverage(stores, ALL_PASS), Coverage.VERIFIED)

    def test_one_unknown_store_drops_the_aggregate_to_partial(self) -> None:
        stores = {"markdown": Coverage.VERIFIED, "cache": Coverage.UNKNOWN}
        self.assertEqual(aggregate_coverage(stores, ALL_PASS), Coverage.PARTIAL)

    def test_nothing_observable_at_all_aggregates_to_unknown(self) -> None:
        # `partial` claims some relevant state was handled. When nothing was,
        # saying `partial` would overstate the work done.
        stores = {"cache": Coverage.UNKNOWN, "backup": Coverage.UNKNOWN}
        self.assertEqual(aggregate_coverage(stores, ALL_PASS), Coverage.UNKNOWN)

    def test_a_failed_store_dominates(self) -> None:
        stores = {"markdown": Coverage.VERIFIED, "vector": Coverage.FAILED}
        self.assertEqual(aggregate_coverage(stores, ALL_PASS), Coverage.FAILED)

    def test_a_failed_probe_dominates_even_with_every_store_verified(self) -> None:
        stores = {"markdown": Coverage.VERIFIED, "vector": Coverage.VERIFIED}
        triad = {"negative": "fail", "positive": "pass", "preserve": "pass"}
        self.assertEqual(aggregate_coverage(stores, triad), Coverage.FAILED)

    def test_no_stores_in_scope_is_unknown_not_verified(self) -> None:
        self.assertEqual(aggregate_coverage({}, ALL_PASS), Coverage.UNKNOWN)


class DemoRunsAndRefusesToGoGreen(unittest.TestCase):
    def test_it_runs_from_a_clean_checkout_and_exits_two(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "prototype.demo"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("PARTIAL", result.stdout)
        self.assertIn("prompt_cache", result.stdout)

    def test_it_needs_no_network_and_no_api_key(self) -> None:
        # Nothing in the prototype may import a network module. This is a
        # structural check, not a sandbox: it catches the accidental
        # `import requests` that would make the demo unreproducible.
        forbidden = ("requests", "urllib.request", "http.client", "socket", "openai")
        for path in sorted((REPO_ROOT / "prototype").glob("*.py")):
            source = path.read_text(encoding="utf-8")
            for module in forbidden:
                self.assertNotIn(
                    f"import {module}", source, f"{path.name} imports {module}"
                )



class RequiredScopeIsHonoured(unittest.TestCase):
    """IDEA.md: a store outside the root's required scope is omitted from the
    receipt, not recorded with a flattering result. There is deliberately no
    `not-applicable` value, because nothing distinguishes it from unchecked."""

    def test_a_non_required_store_is_omitted_rather_than_scored(self) -> None:
        from prototype.adapters import OpaqueAdapter
        from prototype.scenario import build_importer
        from prototype.signing import DemoSigner
        from tests.test_regressions import supersede

        owner = DemoSigner(b"owner-secret")
        importer = build_importer(owner, include_opaque=False)
        optional = OpaqueAdapter(name="analytics_mirror")
        optional.required = False
        importer.adapters.append(optional)

        receipt = importer.repair(supersede())
        self.assertNotIn("analytics_mirror", receipt.stores)
        self.assertEqual(receipt.aggregate, Coverage.VERIFIED)

    def test_the_same_store_marked_required_blocks_success(self) -> None:
        from prototype.adapters import OpaqueAdapter
        from prototype.scenario import build_importer
        from prototype.signing import DemoSigner
        from tests.test_regressions import supersede

        owner = DemoSigner(b"owner-secret")
        importer = build_importer(owner, include_opaque=False)
        importer.adapters.append(OpaqueAdapter(name="analytics_mirror"))

        receipt = importer.repair(supersede())
        self.assertIn("analytics_mirror", receipt.stores)
        self.assertEqual(receipt.aggregate, Coverage.PARTIAL)

if __name__ == "__main__":
    unittest.main()
