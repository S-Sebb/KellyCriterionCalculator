"""PySide6 graphical user interface for Kelly Criterion calculator."""

from __future__ import annotations

import sys
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from KellyCriterionCalculator.kelly import scaled_kelly_fractions

OUTCOME_COUNT = 3
OUTCOME_COLUMN = 0
PROBABILITY_COLUMN = 1
WEIGHT_COLUMN = 2
ODDS_COLUMN = 3
FULL_KELLY_COLUMN = 4
HALF_KELLY_COLUMN = 5
QUARTER_KELLY_COLUMN = 6

DEFAULT_TEAM_A = "Team A"
DEFAULT_TEAM_B = "Team B"
DEFAULT_WEIGHTS = ("1", "2", "4")
DEFAULT_ODDS = ("2.30", "3.40", "3.10")
DEFAULT_BANKROLL = "1000.00"
PROBABILITY_SUM_TOLERANCE = 0.05
PROBABILITY_MATCH_TOLERANCE = 0.0001


@dataclass(frozen=True)
class OutcomeInput:
    """User input for one match outcome."""

    label: str
    probability: float
    decimal_odds: float


@dataclass(frozen=True)
class OutcomeResult:
    """Calculated Kelly output for one match outcome."""

    label: str
    probability: float
    full_kelly: float
    half_kelly: float
    quarter_kelly: float


class KellyCalculatorWindow(QMainWindow):
    """Main calculator window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Kelly Criterion Calculator")
        self.resize(1040, 560)

        self.team_a_input = QLineEdit(DEFAULT_TEAM_A)
        self.team_a_input.setPlaceholderText("Example: Arsenal")
        self.team_b_input = QLineEdit(DEFAULT_TEAM_B)
        self.team_b_input.setPlaceholderText("Example: Chelsea")
        self.bankroll_input = QLineEdit(DEFAULT_BANKROLL)
        self.bankroll_input.setPlaceholderText("Example: 1000.00")

        self.table = QTableWidget(OUTCOME_COUNT, 7)
        self.outcome_items: list[QTableWidgetItem] = []
        self.probability_inputs: list[QLineEdit] = []
        self.weight_inputs: list[QLineEdit] = []
        self.odds_inputs: list[QLineEdit] = []
        self.summary = QTextEdit()
        self.summary.setReadOnly(True)

        self._build_ui()
        self.load_example()

    def _build_ui(self) -> None:
        central = QWidget()
        root_layout = QVBoxLayout(central)

        input_group = QGroupBox("Match input")
        input_layout = QGridLayout(input_group)
        input_layout.addWidget(QLabel("Team A"), 0, 0)
        input_layout.addWidget(self.team_a_input, 0, 1)
        input_layout.addWidget(QLabel("Team B"), 1, 0)
        input_layout.addWidget(self.team_b_input, 1, 1)
        input_layout.addWidget(QLabel("Bankroll"), 2, 0)
        input_layout.addWidget(self.bankroll_input, 2, 1)
        input_layout.addWidget(
            QLabel("Enter either all 3 Pred Probabilities (%) or all 3 Pred Weights"),
            3,
            0,
            1,
            2,
        )

        self.table.setHorizontalHeaderLabels(
            [
                "Outcome",
                "Pred Probability (%)",
                "Pred Weight",
                "Decimal Odds",
                "Full Kelly",
                "Half Kelly",
                "1/4 Kelly",
            ]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setAlternatingRowColors(True)

        positive_number_validator = QDoubleValidator(0.0, 1_000_000_000.0, 8, self)
        positive_number_validator.setNotation(
            QDoubleValidator.Notation.StandardNotation
        )
        self.bankroll_input.setValidator(positive_number_validator)
        self.team_a_input.textChanged.connect(self.update_outcomes)
        self.team_b_input.textChanged.connect(self.update_outcomes)

        for row in range(OUTCOME_COUNT):
            outcome_item = QTableWidgetItem("—")
            outcome_item.setFlags(outcome_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            probability_input = QLineEdit()
            probability_input.setPlaceholderText("Example: 25%")
            weight_input = QLineEdit()
            weight_input.setPlaceholderText("Example: 2")
            weight_input.setValidator(positive_number_validator)
            odds_input = QLineEdit()
            odds_input.setValidator(positive_number_validator)

            probability_input.textEdited.connect(self.clear_weight_inputs)
            weight_input.textEdited.connect(self.clear_probability_inputs)

            self.outcome_items.append(outcome_item)
            self.probability_inputs.append(probability_input)
            self.weight_inputs.append(weight_input)
            self.odds_inputs.append(odds_input)

            self.table.setItem(row, OUTCOME_COLUMN, outcome_item)
            self.table.setCellWidget(row, PROBABILITY_COLUMN, probability_input)
            self.table.setCellWidget(row, WEIGHT_COLUMN, weight_input)
            self.table.setCellWidget(row, ODDS_COLUMN, odds_input)

            for column in (FULL_KELLY_COLUMN, HALF_KELLY_COLUMN, QUARTER_KELLY_COLUMN):
                item = QTableWidgetItem("—")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, column, item)

        button_layout = QHBoxLayout()
        calculate_button = QPushButton("Calculate")
        example_button = QPushButton("Load example")
        clear_button = QPushButton("Clear")
        calculate_button.clicked.connect(self.calculate)
        example_button.clicked.connect(self.load_example)
        clear_button.clicked.connect(self.clear_inputs)
        button_layout.addWidget(calculate_button)
        button_layout.addWidget(example_button)
        button_layout.addWidget(clear_button)
        button_layout.addStretch(1)

        root_layout.addWidget(input_group)
        root_layout.addWidget(self.table)
        root_layout.addLayout(button_layout)
        root_layout.addWidget(QLabel("Result summary"))
        root_layout.addWidget(self.summary)
        self.setCentralWidget(central)
        self.update_outcomes()

    def load_example(self) -> None:
        """Fill window with sample values."""
        self.team_a_input.setText(DEFAULT_TEAM_A)
        self.team_b_input.setText(DEFAULT_TEAM_B)
        self.bankroll_input.setText(DEFAULT_BANKROLL)
        for row, (weight, odds) in enumerate(
            zip(DEFAULT_WEIGHTS, DEFAULT_ODDS, strict=True)
        ):
            self.probability_inputs[row].clear()
            self.weight_inputs[row].setText(weight)
            self.odds_inputs[row].setText(odds)
        self.update_outcomes()
        self.calculate()

    def clear_inputs(self) -> None:
        """Clear user inputs and calculated outputs."""
        self.team_a_input.clear()
        self.team_b_input.clear()
        self.bankroll_input.clear()
        for row in range(OUTCOME_COUNT):
            self.probability_inputs[row].clear()
            self.weight_inputs[row].clear()
            self.odds_inputs[row].clear()
            self._set_output(row, "—", "—", "—")
        self.update_outcomes()
        self.summary.clear()

    def clear_probability_inputs(self) -> None:
        """Clear probabilities when user starts entering weights."""
        for probability_input in self.probability_inputs:
            probability_input.clear()

    def clear_weight_inputs(self) -> None:
        """Clear weights when user starts entering probabilities."""
        for weight_input in self.weight_inputs:
            weight_input.clear()

    def update_outcomes(self) -> None:
        """Refresh read-only outcome labels from team names."""
        for row, label in enumerate(self.generated_outcome_labels()):
            self.outcome_items[row].setText(label)

    def generated_outcome_labels(self) -> tuple[str, str, str]:
        """Return outcome labels based on current team names."""
        team_a = self.team_a_input.text().strip() or "Team A"
        team_b = self.team_b_input.text().strip() or "Team B"
        return f"{team_a} Win", "Draw", f"{team_b} Win"

    def match_name(self) -> str:
        """Return generated match name."""
        team_a = self.team_a_input.text().strip() or "Team A"
        team_b = self.team_b_input.text().strip() or "Team B"
        return f"{team_a} vs {team_b}"

    def calculate(self) -> None:
        """Calculate Kelly bet amounts from current UI values."""
        try:
            bankroll = parse_positive_amount(self.bankroll_input.text(), "Bankroll")
            inputs = self._read_inputs_and_fill_missing_column()
            results = calculate_outcomes(inputs)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid input", str(exc))
            return

        for row, result in enumerate(results):
            self._set_output(
                row,
                format_bet_amount(result.full_kelly, bankroll),
                format_bet_amount(result.half_kelly, bankroll),
                format_bet_amount(result.quarter_kelly, bankroll),
            )

        self.summary.setPlainText(self._build_summary(results, bankroll))

    def _read_inputs_and_fill_missing_column(self) -> list[OutcomeInput]:
        labels = self.generated_outcome_labels()
        probability_texts = [field.text().strip() for field in self.probability_inputs]
        weight_texts = [field.text().strip() for field in self.weight_inputs]
        probability_complete = all(probability_texts)
        weight_complete = all(weight_texts)

        if any(probability_texts) and not probability_complete:
            raise ValueError(
                "Enter all 3 probabilities, or leave probability column empty and enter all 3 weights."
            )
        if any(weight_texts) and not weight_complete:
            raise ValueError(
                "Enter all 3 weights, or leave weight column empty and enter all 3 probabilities."
            )
        if not probability_complete and not weight_complete:
            raise ValueError("Enter either all 3 probabilities or all 3 weights.")

        if probability_complete and weight_complete:
            probabilities = self._parse_probability_inputs(labels)
            probabilities_from_weights = normalize_weights(
                self._parse_weight_inputs(labels)
            )
            if not probabilities_match(probabilities, probabilities_from_weights):
                raise ValueError(
                    "Probability and weight columns disagree. Clear one column, then Calculate again."
                )
        elif probability_complete:
            probabilities = self._parse_probability_inputs(labels)
            self._fill_weights(probabilities)
        else:
            probabilities = normalize_weights(self._parse_weight_inputs(labels))
            self._fill_probabilities(probabilities)

        inputs: list[OutcomeInput] = []
        for row, label in enumerate(labels):
            odds = parse_decimal_odds(
                self.odds_inputs[row].text(), f"{label} decimal odds"
            )
            inputs.append(OutcomeInput(label, probabilities[row], odds))
        return inputs

    def _parse_probability_inputs(self, labels: tuple[str, str, str]) -> list[float]:
        probabilities = [
            parse_probability_percent(
                self.probability_inputs[row].text(), f"{label} probability"
            )
            for row, label in enumerate(labels)
        ]
        validate_probability_total(probabilities)
        return probabilities

    def _parse_weight_inputs(self, labels: tuple[str, str, str]) -> list[float]:
        return [
            parse_weight(self.weight_inputs[row].text(), f"{label} weight")
            for row, label in enumerate(labels)
        ]

    def _fill_probabilities(self, probabilities: list[float]) -> None:
        for row, probability in enumerate(probabilities):
            self.probability_inputs[row].setText(format_percent(probability))

    def _fill_weights(self, probabilities: list[float]) -> None:
        for row, probability in enumerate(probabilities):
            self.weight_inputs[row].setText(format_weight(probability * 100))

    def _set_output(
        self, row: int, full_kelly: str, half_kelly: str, quarter_kelly: str
    ) -> None:
        values = {
            FULL_KELLY_COLUMN: full_kelly,
            HALF_KELLY_COLUMN: half_kelly,
            QUARTER_KELLY_COLUMN: quarter_kelly,
        }
        for column, value in values.items():
            item = self.table.item(row, column)
            if item is not None:
                item.setText(value)

    def _build_summary(self, results: list[OutcomeResult], bankroll: float) -> str:
        positive_results = [result for result in results if result.full_kelly > 0]
        lines = [self.match_name(), f"Bankroll: {format_money(bankroll)}", ""]

        if not positive_results:
            lines.append("No positive Kelly bets from these probabilities and odds.")
            return "\n".join(lines)

        lines.append("Positive Kelly recommendations:")
        for result in positive_results:
            lines.append(
                f"- {result.label}: full {format_bet_amount(result.full_kelly, bankroll)}, "
                f"half {format_bet_amount(result.half_kelly, bankroll)}, "
                f"1/4 {format_bet_amount(result.quarter_kelly, bankroll)}"
            )
        return "\n".join(lines)


def calculate_outcomes(inputs: list[OutcomeInput]) -> list[OutcomeResult]:
    """Calculate Kelly fractions for each outcome."""
    results: list[OutcomeResult] = []
    for item in inputs:
        full, half, quarter = scaled_kelly_fractions(
            item.probability, item.decimal_odds
        )
        results.append(OutcomeResult(item.label, item.probability, full, half, quarter))
    return results


def parse_probability_percent(raw_value: str, field_name: str) -> float:
    """Parse probability percent input."""
    text = raw_value.strip()
    if not text:
        raise ValueError(f"{field_name} is required.")
    if text.endswith("%"):
        text = text[:-1].strip()

    try:
        value = float(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a percentage number.") from exc

    if not 0 <= value <= 100:
        raise ValueError(f"{field_name} must be between 0% and 100%.")
    return value / 100


def validate_probability_total(probabilities: list[float]) -> None:
    """Ensure probability percentages add to 100%."""
    total_percent = sum(probabilities) * 100
    if abs(total_percent - 100) > PROBABILITY_SUM_TOLERANCE:
        raise ValueError(f"Probabilities must add to 100%, got {total_percent:.6g}%.")


def parse_weight(raw_value: str, field_name: str) -> float:
    """Parse non-negative outcome weight."""
    text = raw_value.strip()
    if not text:
        raise ValueError(f"{field_name} is required.")

    try:
        value = float(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a number.") from exc

    if value < 0:
        raise ValueError(f"{field_name} cannot be negative.")
    return value


def normalize_weights(weights: list[float]) -> list[float]:
    """Convert weights into probabilities."""
    total = sum(weights)
    if total <= 0:
        raise ValueError("Weights must sum to more than 0.")
    return [weight / total for weight in weights]


def probabilities_match(left: list[float], right: list[float]) -> bool:
    """Return whether two probability sets are effectively equivalent."""
    return all(
        abs(left_value - right_value) <= PROBABILITY_MATCH_TOLERANCE
        for left_value, right_value in zip(left, right, strict=True)
    )


def parse_positive_amount(raw_value: str, field_name: str) -> float:
    """Parse and validate a positive money amount."""
    text = raw_value.strip()
    if not text:
        raise ValueError(f"{field_name} is required.")

    try:
        value = float(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a number.") from exc

    if value <= 0:
        raise ValueError(f"{field_name} must be greater than 0.")
    return value


def parse_decimal_odds(raw_value: str, field_name: str) -> float:
    """Parse and validate decimal odds."""
    text = raw_value.strip()
    if not text:
        raise ValueError(f"{field_name} is required.")

    try:
        value = float(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a number.") from exc

    if value <= 1:
        raise ValueError(f"{field_name} must be greater than 1.")
    return value


def format_percent(value: float) -> str:
    """Format probability as percent text."""
    return f"{value:.6%}"


def format_weight(value: float) -> str:
    """Format generated weight text."""
    return f"{value:.6f}".rstrip("0").rstrip(".")


def format_money(value: float) -> str:
    """Format money amount without assuming a currency symbol."""
    return f"{value:,.2f}"


def format_bet_amount(kelly_fraction: float, bankroll: float) -> str:
    """Format actual bankroll amount to bet."""
    return format_money(kelly_fraction * bankroll)


def main() -> int:
    """Launch GUI application."""
    app = QApplication(sys.argv)
    window = KellyCalculatorWindow()
    window.show()
    return app.exec()
