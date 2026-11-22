"""Tests for the statistics scripts bundled with ab-test-design and experiment-readout."""
import importlib.util
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(relative_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sample_size = load("skills/ab-test-design/scripts/sample_size.py", "sample_size")
readout = load("skills/experiment-readout/scripts/readout.py", "readout")


class SampleSizeTest(unittest.TestCase):
    def test_conversion_matches_textbook_value(self):
        # 10% -> 11%, alpha 0.05 two-sided, power 0.8: 14,749 per variant (unpooled normal approximation)
        self.assertEqual(sample_size.sample_size_per_variant(0.05, 0.8, 0.01, baseline=0.10), 14749)

    def test_conversion_close_to_lehr_rule(self):
        n = sample_size.sample_size_per_variant(0.05, 0.8, 0.01, baseline=0.10)
        lehr = 16 * 0.10 * 0.90 / 0.01 ** 2
        self.assertLess(abs(n - lehr) / lehr, 0.05)

    def test_continuous_metric(self):
        self.assertEqual(sample_size.sample_size_per_variant(0.05, 0.8, 3, std=40), 2791)

    def test_run_length_rounds_up_to_whole_weeks(self):
        self.assertEqual(sample_size.run_length(29498, 2000), (15, 21))
        self.assertEqual(sample_size.run_length(100, 2000), (1, 7))

    def test_rejects_rate_above_one(self):
        with self.assertRaises(ValueError):
            sample_size.sample_size_per_variant(0.05, 0.8, 0.2, baseline=0.9)


class ReadoutTest(unittest.TestCase):
    def test_srm_ok_and_mismatch(self):
        _, p_ok = readout.srm_check(10000, 10050)
        _, p_bad = readout.srm_check(50000, 48000)
        self.assertGreater(p_ok, 0.5)
        self.assertLess(p_bad, readout.SRM_THRESHOLD)

    def test_srm_respects_planned_split(self):
        _, p = readout.srm_check(9000, 1000, split=0.9)
        self.assertGreater(p, 0.9)

    def test_two_proportions(self):
        result = readout.compare_rates(10000, 1000, 10050, 1100)
        self.assertAlmostEqual(result["diff"], 1100 / 10050 - 0.1, places=10)
        self.assertAlmostEqual(result["p_value"], 0.0289, places=3)
        low, high = result["diff_ci"]
        self.assertTrue(0 < low < result["diff"] < high)
        lift_low, lift_high = result["lift_ci"]
        self.assertTrue(lift_low < result["lift"] < lift_high)

    def test_means(self):
        result = readout.compare_means(48210, 41.2, 38.5, 48655, 42.0, 39.1)
        se = math.sqrt(38.5 ** 2 / 48210 + 39.1 ** 2 / 48655)
        self.assertAlmostEqual(result["diff_ci"][1] - result["diff"], 1.959964 * se, places=4)
        self.assertLess(result["p_value"], 0.01)

    def test_verdicts(self):
        self.assertTrue(readout.verdict((0.06, 0.10), mde=0.05).startswith("Clear win"))
        self.assertTrue(readout.verdict((0.01, 0.10), mde=0.05).startswith("Positive"))
        self.assertTrue(readout.verdict((-0.02, 0.03), mde=0.05).startswith("Flat"))
        self.assertTrue(readout.verdict((-0.04, 0.09), mde=0.05).startswith("Inconclusive"))
        self.assertTrue(readout.verdict((-0.09, -0.01), mde=0.05).startswith("The change hurts"))
        self.assertTrue(readout.verdict((-0.04, 0.09)).startswith("Not significant"))


if __name__ == "__main__":
    unittest.main()
