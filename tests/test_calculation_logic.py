import math
import unittest

from KellyCriterionCalculator.gui import (
    OutcomeInput,
    calculate_outcomes,
    fair_odds_to_probabilities,
)
from KellyCriterionCalculator.kelly import (
    full_kelly_fraction,
    full_kelly_market_fractions,
)


class KellyFormulaTests(unittest.TestCase):
    def test_single_outcome_formula_matches_decimal_odds_kelly(self) -> None:
        fraction = full_kelly_fraction(0.55, 2.10)
        self.assertTrue(math.isclose(fraction, 0.14090909090909098))

    def test_market_formula_accepts_bookmaker_overround_odds(self) -> None:
        probabilities = [1 / 7, 2 / 7, 4 / 7]
        odds = [2.30, 3.40, 3.10]
        implied_probability_sum = sum(1 / odd for odd in odds)

        market_fractions = full_kelly_market_fractions(probabilities, odds)

        self.assertGreater(implied_probability_sum, 1.0)
        self.assertTrue(math.isclose(market_fractions[0], 0.0))
        self.assertTrue(math.isclose(market_fractions[1], 0.17609618104667604))
        self.assertTrue(math.isclose(market_fractions[2], 0.4512022630834511))

    def test_market_formula_returns_zero_when_all_outcomes_below_break_even(
        self,
    ) -> None:
        fractions = full_kelly_market_fractions([0.4, 0.3, 0.3], [2.4, 3.2, 3.2])

        self.assertEqual(fractions, [0.0, 0.0, 0.0])

    def test_market_formula_sizes_clear_single_positive_edge(self) -> None:
        fractions = full_kelly_market_fractions([0.5, 0.3, 0.2], [2.2, 3.0, 4.5])

        self.assertTrue(math.isclose(fractions[0], full_kelly_fraction(0.5, 2.2)))
        self.assertEqual(fractions[1:], [0.0, 0.0])

    def test_market_formula_sizes_multiple_positive_edges_together(self) -> None:
        fractions = full_kelly_market_fractions([0.4, 0.3, 0.3], [3.0, 4.0, 4.0])

        self.assertTrue(math.isclose(fractions[0], 0.4))
        self.assertTrue(math.isclose(fractions[1], 0.3))
        self.assertTrue(math.isclose(fractions[2], 0.3))

    def test_market_formula_can_use_negative_ev_hedge_in_underround_market(
        self,
    ) -> None:
        fractions = full_kelly_market_fractions([0.6, 0.4], [2.0, 2.375])

        self.assertLess(0.4 * 2.375, 1.0)
        self.assertTrue(math.isclose(fractions[0], 0.6))
        self.assertTrue(math.isclose(fractions[1], 0.4))

    def test_calculate_outcomes_uses_market_fractions(self) -> None:
        results = calculate_outcomes(
            [
                OutcomeInput("A", 0.4, 3.0),
                OutcomeInput("Draw", 0.3, 4.0),
                OutcomeInput("B", 0.3, 4.0),
            ]
        )

        self.assertTrue(math.isclose(results[0].full_kelly, 0.4))
        self.assertTrue(math.isclose(results[1].half_kelly, 0.15))
        self.assertTrue(math.isclose(results[2].quarter_kelly, 0.075))

    def test_fair_odds_reverse_then_normalize_to_100_percent(self) -> None:
        probabilities = fair_odds_to_probabilities([2.0, 3.0, 4.0])

        self.assertTrue(math.isclose(sum(probabilities), 1.0))
        self.assertTrue(math.isclose(probabilities[0], 6 / 13))
        self.assertTrue(math.isclose(probabilities[1], 4 / 13))
        self.assertTrue(math.isclose(probabilities[2], 3 / 13))


if __name__ == "__main__":
    unittest.main()
