import unittest
from impact_calculator import calculate_impact


class TestImpactCalculator(unittest.TestCase):
    def test_expected_calculation(self):
        self.assertEqual(calculate_impact(200, 80, 75), {
            "total_waste_kg": 200,
            "collected_kg": 160,
            "recovered_kg": 120,
            "unrecovered_kg": 40,
        })

    def test_zero_waste(self):
        self.assertEqual(calculate_impact(0, 80, 75)["recovered_kg"], 0)

    def test_negative_waste_rejected(self):
        with self.assertRaises(ValueError):
            calculate_impact(-1, 80, 75)

    def test_invalid_rates_rejected(self):
        for collection, recovery in [(-1, 75), (101, 75), (80, -1), (80, 101)]:
            with self.subTest(collection=collection, recovery=recovery):
                with self.assertRaises(ValueError):
                    calculate_impact(200, collection, recovery)


if __name__ == "__main__":
    unittest.main(verbosity=2)