"""CSV helpers and project-path utilities."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

MATCH_ID_COLUMN = "match_id"
MATCH_COLUMN = "match"
ROW_TYPE_COLUMN = "row_type"
TEAM_A_WIN_COLUMN = "team_a_win"
DRAW_COLUMN = "draw"
TEAM_B_WIN_COLUMN = "team_b_win"

OUTCOME_ROW = "Outcome"
PROBABILITY_ROW = "Predicted Probability"
NORMALIZED_PROBABILITY_ROW = "Normalized Probability"
PAYOUT_ROW = "Payout"
FULL_KELLY_ROW = "Full Kelly"
HALF_KELLY_ROW = "Half Kelly"
QUARTER_KELLY_ROW = "1/4 Kelly"

INPUT_COLUMNS = [
    MATCH_ID_COLUMN,
    MATCH_COLUMN,
    ROW_TYPE_COLUMN,
    TEAM_A_WIN_COLUMN,
    DRAW_COLUMN,
    TEAM_B_WIN_COLUMN,
]

OUTCOME_COLUMNS = [TEAM_A_WIN_COLUMN, DRAW_COLUMN, TEAM_B_WIN_COLUMN]

TEMPLATE_ROWS = [
    {
        MATCH_ID_COLUMN: "example-001",
        MATCH_COLUMN: "Team A vs Team B",
        ROW_TYPE_COLUMN: OUTCOME_ROW,
        TEAM_A_WIN_COLUMN: "Team A Win",
        DRAW_COLUMN: "Draw",
        TEAM_B_WIN_COLUMN: "Team B Win",
    },
    {
        MATCH_ID_COLUMN: "example-001",
        MATCH_COLUMN: "Team A vs Team B",
        ROW_TYPE_COLUMN: PROBABILITY_ROW,
        TEAM_A_WIN_COLUMN: "1",
        DRAW_COLUMN: "2",
        TEAM_B_WIN_COLUMN: "4",
    },
    {
        MATCH_ID_COLUMN: "example-001",
        MATCH_COLUMN: "Team A vs Team B",
        ROW_TYPE_COLUMN: PAYOUT_ROW,
        TEAM_A_WIN_COLUMN: "2.30",
        DRAW_COLUMN: "3.40",
        TEAM_B_WIN_COLUMN: "3.10",
    },
]


def project_root() -> Path:
    """Return repository root, assuming src/package/utils.py layout."""
    return Path(__file__).resolve().parents[2]


def ensure_directories(root: Path) -> tuple[Path, Path]:
    """Ensure input and output directories exist."""
    input_dir = root / "input"
    output_dir = root / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    return input_dir, output_dir


def create_template_csv(path: Path) -> None:
    """Create user-editable CSV template."""
    write_csv(path, TEMPLATE_ROWS, INPUT_COLUMNS)


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read CSV rows and validate required columns exist."""
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError(f"CSV file is empty: {path}")

        missing = [
            column for column in INPUT_COLUMNS if column not in reader.fieldnames
        ]
        if missing:
            raise ValueError(f"CSV missing required columns: {', '.join(missing)}")

        return list(reader)


def write_csv(
    path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]
) -> None:
    """Write CSV rows with stable column order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_float(row: dict[str, str], column: str, row_number: int) -> float:
    """Parse float with row-aware error message."""
    raw_value = row.get(column, "").strip()
    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"Row {row_number}: column '{column}' must be a number, got {raw_value!r}"
        ) from exc
