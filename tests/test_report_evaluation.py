import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from evaluate_report import DEFAULT_INPUT, build_evaluation


class ReportEvaluationTests(unittest.TestCase):
    def test_generated_contract_trace_and_reproducibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "evaluation"
            result = build_evaluation(DEFAULT_INPUT, out, draws=8)
            again = build_evaluation(DEFAULT_INPUT, Path(tmp) / "repeat", draws=8)
            self.assertEqual(result, again)
            self.assertEqual(result["sensitivity_seed"], 20261009)
            self.assertEqual(len(result["worked_example"]["criteria"]), 5)
            self.assertEqual(len(result["old_demo"]), 4)
            self.assertEqual({row["alternative_id"] for row in result["old_demo"]}, {"HYP-A", "HYP-B", "HYP-C", "HYP-D"})
            self.assertEqual(sum(result["candidate_basis_counts"].values()), result["candidate_count"])
            for counts in result["confidence_counts"].values():
                self.assertEqual(sum(counts.values()), result["candidate_count"])
            self.assertEqual(len(result["all_candidates"]), result["candidate_count"])
            trace = pd.read_csv(out / "five_criterion_calculation_trace.csv")
            self.assertEqual(set(f"weight_{i}" for i in range(1, 6)),
                             set(pd.read_csv(out / "five_criterion_weight_runs.csv").filter(regex="^weight_").columns))
            row = result["worked_example"]
            sums = trace[trace.alternative_id == row["alternative_id"]].groupby("alternative_id").sum(numeric_only=True).iloc[0]
            expected = sums.distance_negative / (sums.distance_positive + sums.distance_negative)
            self.assertAlmostEqual(row["score"], expected, places=12)
            self.assertAlmostEqual(row["score"], result["top_candidates"][0]["score"] if row["alternative_id"] == result["top_candidates"][0]["alternative_id"] else row["score"], places=12)
            self.assertEqual(json.loads((out / "summary.json").read_text()), result)
            self.assertEqual(len(pd.read_csv(out / "five_criterion_uncertainty.csv")), 3)
            expected = pd.read_csv(ROOT / "outputs/synthetic_extension_ranking.csv").set_index("alternative_id")
            actual = pd.DataFrame(result["all_candidates"]).set_index("alternative_id")
            pd.testing.assert_series_equal(actual.score.sort_index(), expected.score.sort_index(), check_names=False, atol=1e-12, rtol=0)


if __name__ == "__main__":
    unittest.main()
