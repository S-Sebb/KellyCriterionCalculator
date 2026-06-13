"""Kelly Criterion calculations."""

from __future__ import annotations

from itertools import combinations
from math import log


def full_kelly_fraction(probability: float, decimal_odds: float) -> float:
    """Return non-negative Full Kelly stake fraction for decimal odds.

    Formula for decimal odds, where net odds b = decimal_odds - 1:
        f* = (p * decimal_odds - 1) / (decimal_odds - 1)

    Negative Kelly means no +EV bet, so returned value is clamped to 0.
    """
    if not 0 <= probability <= 1:
        raise ValueError("probability must be between 0 and 1")
    if decimal_odds <= 1:
        raise ValueError("decimal_odds must be greater than 1")

    fraction = (probability * decimal_odds - 1) / (decimal_odds - 1)
    return max(0.0, fraction)


def scaled_kelly_fractions(
    probability: float, decimal_odds: float
) -> tuple[float, float, float]:
    """Return Full, Half, and Quarter Kelly stake fractions."""
    full = full_kelly_fraction(probability, decimal_odds)
    return full, full / 2, full / 4


def full_kelly_market_fractions(
    probabilities: list[float], decimal_odds: list[float]
) -> list[float]:
    """Return Full Kelly stake fractions for one mutually-exclusive market.

    For one active outcome this reduces to the standard decimal-odds formula.
    For several positive-edge outcomes, this maximizes expected log growth across
    the whole market instead of sizing each outcome as if it were independent.
    """
    if len(probabilities) != len(decimal_odds):
        raise ValueError("probabilities and decimal_odds must have the same length")
    if not probabilities:
        raise ValueError("at least one outcome is required")
    if any(not 0 <= probability <= 1 for probability in probabilities):
        raise ValueError("probabilities must be between 0 and 1")
    if abs(sum(probabilities) - 1.0) > 1e-9:
        raise ValueError("probabilities must sum to 1")
    if any(odds <= 1 for odds in decimal_odds):
        raise ValueError("decimal_odds must be greater than 1")

    tolerance = 1e-12
    outcome_indexes = range(len(probabilities))
    best_fractions = [0.0 for _ in probabilities]
    best_growth = 0.0

    for active_count in range(1, len(probabilities) + 1):
        for active_tuple in combinations(outcome_indexes, active_count):
            active = set(active_tuple)
            inverse_odds_sum = sum(1 / decimal_odds[index] for index in active)
            inactive_probability = 1 - sum(probabilities[index] for index in active)
            fractions = [0.0 for _ in probabilities]

            if inactive_probability <= tolerance:
                if inverse_odds_sum >= 1 - tolerance:
                    continue
                for index in active:
                    fractions[index] = probabilities[index]
            else:
                denominator = 1 - inverse_odds_sum
                if denominator <= tolerance:
                    continue

                cash_fraction = inactive_probability / denominator
                for index in active:
                    fractions[index] = (
                        probabilities[index] - cash_fraction / decimal_odds[index]
                    )

            if any(fraction < -tolerance for fraction in fractions):
                continue

            fractions = [max(0.0, fraction) for fraction in fractions]
            if sum(fractions) > 1 + tolerance:
                continue

            growth = _expected_log_growth(probabilities, decimal_odds, fractions)
            if growth > best_growth + tolerance:
                best_fractions = fractions
                best_growth = growth

    return best_fractions


def _expected_log_growth(
    probabilities: list[float], decimal_odds: list[float], fractions: list[float]
) -> float:
    """Return expected log growth for stake fractions in one market."""
    total_staked = sum(fractions)
    growth = 0.0
    for probability, odds, fraction in zip(
        probabilities, decimal_odds, fractions, strict=True
    ):
        wealth = 1 - total_staked + odds * fraction
        if wealth <= 0:
            return float("-inf")
        if probability > 0:
            growth += probability * log(wealth)
    return growth
