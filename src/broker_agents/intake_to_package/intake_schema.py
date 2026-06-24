"""Safe intake validation for the Intake-to-Package MVP.

This module is preparation-only. It does not run investor agents,
produce recommendations, rank companies, allocate capital, generate
trade signals, or create execution instructions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Any

ALLOWED_PREPARATION_OUTPUTS = frozenset(
    {
        "intake_summary",
        "evidence_checklist",
        "missing_evidence_report",
        "source_verification_status",
        "package_readiness",
    }
)

BLOCKED_INVESTMENT_OUTPUTS = frozenset(
    {
        "recommendation",
        "ranking",
        "allocation",
        "buy_signal",
        "sell_signal",
        "investor_decision",
        "portfolio_weight",
        "rebalancing_instruction",
        "trade_signal",
        "execution_instruction",
        "strategy_validation",
        "auto_promotion",
    }
)


class IntakeCompletenessLabel(StrEnum):
    """Non-investment intake completeness labels."""

    INCOMPLETE = "incomplete"
    MINIMUM_IDENTITY_COMPLETE = "minimum_identity_complete"
    READY_FOR_EVIDENCE_CHECKLIST = "ready_for_evidence_checklist"


@dataclass(frozen=True)
class IntakeValidationResult:
    """Result of preparation-only intake validation."""

    label: IntakeCompletenessLabel
    missing_fields: tuple[str, ...]
    blocked_outputs: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def can_continue_to_evidence_checklist(self) -> bool:
        """Return True only for preparation-only evidence checklist readiness."""

        return self.label is IntakeCompletenessLabel.READY_FOR_EVIDENCE_CHECKLIST


def normalize_requested_outputs(value: Any) -> tuple[str, ...]:
    """Normalize requested output values into lowercase snake-like strings."""

    if value is None:
        return ()
    if isinstance(value, str):
        return (_normalize_token(value),)
    if isinstance(value, list | tuple | set):
        return tuple(
            _normalize_token(item)
            for item in value
            if isinstance(item, str) and item.strip()
        )
    return ()


def blocked_requested_outputs(value: Any) -> tuple[str, ...]:
    """Return blocked investment outputs requested by an intake payload."""

    requested_outputs = normalize_requested_outputs(value)
    return tuple(
        output
        for output in requested_outputs
        if output in BLOCKED_INVESTMENT_OUTPUTS
    )


def validate_intake(payload: dict[str, Any]) -> IntakeValidationResult:
    """Validate a company or ticker intake payload.

    The function only returns non-investment completeness labels.
    It does not imply investability, attractiveness, ranking,
    recommendation, allocation, or trade action.
    """

    missing_fields: list[str] = []
    warnings: list[str] = []

    company_name = _clean_string(payload.get("company_name"))
    ticker = _clean_string(payload.get("ticker"))
    exchange = _clean_string(payload.get("exchange"))
    as_of_date = _clean_string(payload.get("as_of_date"))

    blocked_outputs = blocked_requested_outputs(payload.get("requested_output"))
    requested_outputs = normalize_requested_outputs(payload.get("requested_output"))

    if not company_name:
        missing_fields.append("company_name")
    if not ticker and not _has_official_identity_evidence(payload):
        missing_fields.append("ticker_or_official_identity_evidence")
    if ticker and not exchange:
        missing_fields.append("exchange")
    if not as_of_date:
        missing_fields.append("as_of_date")
    elif not _is_valid_iso_date(as_of_date):
        missing_fields.append("as_of_date_valid_iso_format")

    unknown_outputs = tuple(
        output
        for output in requested_outputs
        if output not in ALLOWED_PREPARATION_OUTPUTS
        and output not in BLOCKED_INVESTMENT_OUTPUTS
    )
    for output in unknown_outputs:
        warnings.append(f"unknown_requested_output:{output}")

    if missing_fields or blocked_outputs:
        return IntakeValidationResult(
            label=IntakeCompletenessLabel.INCOMPLETE,
            missing_fields=tuple(missing_fields),
            blocked_outputs=blocked_outputs,
            warnings=tuple(warnings),
        )

    if not requested_outputs:
        return IntakeValidationResult(
            label=IntakeCompletenessLabel.MINIMUM_IDENTITY_COMPLETE,
            missing_fields=(),
            blocked_outputs=(),
            warnings=tuple(warnings),
        )

    return IntakeValidationResult(
        label=IntakeCompletenessLabel.READY_FOR_EVIDENCE_CHECKLIST,
        missing_fields=(),
        blocked_outputs=(),
        warnings=tuple(warnings),
    )


def _clean_string(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _normalize_token(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _is_valid_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _has_official_identity_evidence(payload: dict[str, Any]) -> bool:
    official_filings = payload.get("official_filings")
    if not isinstance(official_filings, list):
        return False

    for source in official_filings:
        if not isinstance(source, dict):
            continue
        reliability_label = _normalize_token(str(source.get("reliability_label", "")))
        title = _clean_string(source.get("title"))
        url_or_path = _clean_string(source.get("url_or_path"))
        if reliability_label == "official" and (title or url_or_path):
            return True
    return False

