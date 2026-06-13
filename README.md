# KellyCriterionCalculator

Desktop Kelly Criterion calculator for three-outcome matches.

## Features

- User-friendly PySide6 GUI. No CSV input or output required.
- Inputs for two team names, bankroll, predicted probabilities or weights, and decimal odds.
- Outcome labels are generated automatically as `Team A win`, `Draw`, and `Team B win`; users cannot edit them directly.
- Predicted probability and predicted weight are separate columns.
- Enter either all 3 probabilities as percentages that add to `100%`, or all 3 weights. Press **Calculate** and the app fills the other column automatically.
- Shows actual Full, Half, and 1/4 Kelly bet amounts from the entered bankroll.
- Displays clear validation errors for missing values, invalid bankrolls, partial probability/weight columns, probabilities not adding to `100%`, negative weights, zero weight totals, and decimal odds less than or equal to `1`.

## Run

```bash
uv run kelly-calculator
```

The app opens a desktop window with example teams, bankroll, weights, and odds loaded. Edit either the probability column or the weight column, then click **Calculate**.

## Output meaning

Kelly fractions are converted into actual bet amounts using the entered bankroll. Example: with bankroll `1000.00`, a `5%` Kelly recommendation displays as `50.00`.

Negative Kelly values are clamped to `0.00`, meaning no positive expected-value bet under the entered probabilities and odds.
