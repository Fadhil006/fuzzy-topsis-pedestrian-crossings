"""Mathematical and pipeline checks using synthetic values only."""
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from model import fuzzy_topsis, intervalize, normalize_priority, validate_weights, vertex_distance
from run_project import evaluate, load_and_validate

class ModelChecks(unittest.TestCase):
    def test_independently_calculated_two_criterion_case(self):
        # Hand calculation in docs/worked_example.md; guards aggregation choice.
        a = np.array([[[.2, .4, .6], [.5, .7, .9]],
                      [[.7, .8, .9], [.1, .2, .3]]])
        score, dp, dm = fuzzy_topsis(a, [.4, .6])
        self.assertAlmostEqual(dp[0], .4536691234015604, places=12)
        self.assertAlmostEqual(dm[0], .6040969250144994, places=12)
        self.assertAlmostEqual(score[0], .5711063669694236, places=12)

    def test_constant_column_cannot_change_ranking_or_scores(self):
        informative = np.array([[[0, 0, 0]], [[1, 1, 1]]], dtype=float)
        with_constant = np.concatenate([informative, np.zeros_like(informative)], axis=1)
        expected = fuzzy_topsis(informative, [1])[0]
        actual = fuzzy_topsis(with_constant, [.5, .5])[0]
        np.testing.assert_allclose(actual, expected)

    def test_benefit_and_cost_orientation(self):
        x = normalize_priority([[1, 10], [3, 5]], ["benefit", "cost"])
        np.testing.assert_allclose(x, [[0, 0], [1, 1]])
        with self.assertRaises(ValueError):
            normalize_priority([[1], [2]], ["unknown"])

    def test_invalid_and_non_discriminating_input(self):
        with self.assertRaises(ValueError):
            intervalize(np.array([[[2, 1, 3]], [[1, 2, 3]]]))
        with self.assertRaises(ValueError):
            fuzzy_topsis(np.zeros((2, 2, 3)), [.5, .5])
        with self.assertRaises(ValueError):
            validate_weights([0, 0])
        self.assertAlmostEqual(float(vertex_distance([0, 0, 0], [1, 1, 1])), 1)

    def test_large_finite_weights_remain_normalized(self):
        np.testing.assert_allclose(validate_weights([1e308, 1e308]), [.5, .5])

    def test_identifiers_are_trimmed_before_duplicate_check(self):
        data = pd.read_csv(ROOT / "data/hypothetical_demo.csv")
        data.loc[1, "alternative_id"] = " " + data.loc[0, "alternative_id"] + " "
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "duplicate.csv"
            data.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "unique"):
                load_and_validate(path)

    def test_uncertainty_scenarios_and_distance_trace(self):
        _, eligible = load_and_validate(ROOT / "data/hypothetical_demo.csv")
        with tempfile.TemporaryDirectory() as temp:
            tables = evaluate(eligible, Path(temp), prefix="hypothetical_", draws=10)
            self.assertIn("uncertainty_sensitivity", tables)
            scenarios = tables["uncertainty_sensitivity"]
            full = scenarios[scenarios.width_factor == 1].set_index("alternative_id")
            base = tables["base_ranking"].set_index("alternative_id")
            np.testing.assert_allclose(full.loc[base.index, "score"], base.score)
            trace = tables["calculation_trace"]
            totals = trace.groupby("alternative_id").distance_positive.sum()
            np.testing.assert_allclose(totals.loc[base.index], base.distance_positive)
            self.assertTrue(np.isfinite(scenarios.score).all())

    def test_complete_demo_pipeline_and_field_validation(self):
        data = ROOT / "data" / "hypothetical_demo.csv"
        _, eligible = load_and_validate(data)
        with tempfile.TemporaryDirectory() as temp:
            tables = evaluate(eligible, Path(temp), prefix="hypothetical_", draws=20)
            self.assertEqual(len(tables["base_ranking"]), 4)
            self.assertEqual(len(tables["weight_sensitivity_runs"]), 20)
            self.assertTrue((Path(temp) / "hypothetical_extension_ranking.csv").exists())
            bad = pd.read_csv(data)
            bad.loc[0, "ped_low"] = None
            path = Path(temp) / "missing.csv"
            bad.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "missing or nonnumeric ped"):
                load_and_validate(path)

if __name__ == "__main__":
    unittest.main()
