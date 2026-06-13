"""Kelly Criterion calculations."""

from __future__ import annotations


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
