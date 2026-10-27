"""
Unit test suite for native Python SPARC Swarm & RuVector in modules/sparc/
"""

import time
import os
import unittest
from modules.sparc import (
    execute_sparc_pipeline,
    format_sparc_report,
    is_sparc_mode,
    RuVectorEngine,
    HardenedCapabilityGateway,
    TransactionalSnapshotManager,
    HybridMemoryRouter
)


class TestNativeSparcBackend(unittest.TestCase):

    def test_mode_detection(self):
        self.assertTrue(is_sparc_mode("/sparc build matching engine"))
        self.assertTrue(is_sparc_mode("analyze portfolio", requested_mode="sparc"))
        self.assertTrue(is_sparc_mode("@sparc run quant screener"))
        self.assertFalse(is_sparc_mode("regular prompt without flag"))

    def test_ruvector_simd(self):
        dim = 384
        engine = RuVectorEngine(dimension=dim)
        v1 = [1.0] + [0.0] * (dim - 1)
        v2 = [0.0, 1.0] + [0.0] * (dim - 2)
        engine.insert("doc1", v1, {"name": "doc1"})
        engine.insert("doc2", v2, {"name": "doc2"})

        t0 = time.perf_counter()
        hits = engine.search(v1, top_k=2)
        dur_ms = (time.perf_counter() - t0) * 1000

        self.assertEqual(len(hits), 2)
        self.assertEqual(hits[0].id, "doc1")
        self.assertAlmostEqual(hits[0].score, 1.0, places=3)
        self.assertLess(dur_ms, 15.0)

    def test_capability_gateway(self):
        gw = HardenedCapabilityGateway(os.getcwd())
        token = gw.mint_token("README.md", 1)
        path = gw.verify_token(token, 1)
        self.assertTrue(path.endswith("README.md"))

        # Test traversal blocking
        with self.assertRaises(PermissionError):
            gw.resolve_canonical_path("../../Windows/System32")

    def test_transactional_rollback(self):
        mgr = TransactionalSnapshotManager()
        test_file = os.path.abspath("test_snapshot_dummy.tmp")
        orphan_file = os.path.abspath("test_orphan_dummy.tmp")

        with open(test_file, "wb") as f:
            f.write(b"ORIGINAL_DATA_12345")

        try:
            mgr.begin_transaction("tx1", [test_file, orphan_file])

            # Mutate existing file
            with open(test_file, "wb") as f:
                f.write(b"CORRUPTED_MUTATED_DATA")

            # Create orphan
            with open(orphan_file, "wb") as f:
                f.write(b"ORPHAN_DATA")

            # Trigger rollback
            mgr.rollback_transaction("tx1")

            with open(test_file, "rb") as f:
                restored = f.read()

            self.assertEqual(restored, b"ORIGINAL_DATA_12345")
            self.assertFalse(os.path.exists(orphan_file))

        finally:
            if os.path.exists(test_file):
                os.remove(test_file)
            if os.path.exists(orphan_file):
                os.remove(orphan_file)

    def test_sparc_pipeline_execution(self):
        description = (
            "# SPECIFICATION: Institutional Matching Engine\n"
            "## PRECONDITIONS\nOrder books must be initialized and non-null.\n"
            "## POSTCONDITIONS\nReturns matched trade executions with price-time priority.\n"
            "## INVARIANTS\nTotal liquidity conservation across limit order book.\n"
            "## BOUNDARIES\nTick size minimum 0.01, maximum quantity 1,000,000 lots.\n\n"
            "# PSEUDOCODE\n"
            "## ALGORITHM\ndef match_order(book, order):\n    pass\n"
            "## COMPLEXITY\nTime Complexity: O(1)\nSpace Complexity: O(n)\n"
            "## LOOP INVARIANT\nUnmatched remainder remains on book.\n"
        )
        content_map = {
            "test_matching.py": (
                "import unittest\n"
                "class TestMatching(unittest.TestCase):\n"
                "    def test_engine_init(self):\n"
                "        self.assertTrue(True)\n"
            )
        }
        res = execute_sparc_pipeline(
            task_id="native-backend-verification",
            description=description,
            files=["modules/sparc/coordinator.py"],
            content_map=content_map
        )
        self.assertEqual(res["status"], "COMPLETED")
        self.assertGreaterEqual(res["finalScore"], 8.5)
        self.assertEqual(len(res["stages"]), 5)

        report = format_sparc_report(res)
        self.assertIn("Aarka SPARC Swarm Verification Report", report)
        self.assertIn("Native In-Process Python", report)


if __name__ == "__main__":
    unittest.main()
