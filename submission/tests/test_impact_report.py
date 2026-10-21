import unittest

from src.impact_report import (
    wilson_interval,
    newcombe_difference_interval,
)


class ImpactReportTests(unittest.TestCase):

    def test_wilson_interval_contains_observed_rate(self):
        interval = wilson_interval(646, 863)
        observed_rate = 646 / 863

        self.assertIsNotNone(interval)
        self.assertLessEqual(interval[0], observed_rate)
        self.assertGreaterEqual(interval[1], observed_rate)

    def test_newcombe_interval_contains_observed_difference(self):
        interval = newcombe_difference_interval(646, 863, 669, 883)
        observed_difference = (646 / 863) - (669 / 883)

        self.assertIsNotNone(interval)
        self.assertLessEqual(interval[0], observed_difference)
        self.assertGreaterEqual(interval[1], observed_difference)

    def test_intervals_handle_empty_samples(self):
        self.assertIsNone(wilson_interval(0, 0))
        self.assertIsNone(newcombe_difference_interval(1, 10, 0, 0))


if __name__ == "__main__":
    unittest.main()