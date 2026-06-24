"""Safe evidence checklist construction for the Intake-to-Package MVP.

This module is preparation-only. It does not run investor agents,
produce recommendations, rank companies, allocate capital, generate
trade signals, or create execution instructions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from broker_agents.intake_to_package.intake_schema import (
    IntakeCompletenessLabel,
    validate_intake,
)


class EvidenceItemStatus(StrEnum):
    """Evidence presence labels only."""

    MISSING = "missing"
    PARTIAL = "partial"
    PRESENT = "present"
    NOT_APPLICABLE = "not_applicable"


class FreshnessStatus(StrEnum):
    """Evidence freshness labels only."""

    CURRENT = "current"
    STALE = "stale"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class VerificationStatus(StrEnum):
    """Source traceability labels only."""

    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNVERIFIED = "unverified"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"


class EvidenceChecklistStatus(StrEnum):
    """Non-investment checklist readiness labels."""

    INCOMPLETE = "incomplete"
    PARTIAL = "partial"
    READY_FOR_HUMAN_REVIEW = "ready_for_human_review"


REQUIRED_EVIDENCE_CATEGORIES = (
    "company_identity",
    "listing_and_exchange",
    "official_financial_statements",
    "operating_revenue",
    "balance_sheet",
    "cash_flow",
    "business_model_or_segments",
    "source_metadata",
    "evidence_freshness",
    "missing_evidence_summary",
)

EVIDENCE_REQUIREMENTS = {
    "company_identity": "Confirm the company identity is clear.",
    "listing_and_exchange": "Confirm listing and organized market context.",
    "official_financial_statements": "Confirm official financial statements are available.",
    "operating_revenue": "Confirm real operating revenue from a clear core activity.",
    "balance_sheet": "Confirm balance sheet evidence is available.",
    "cash_flow": "Confirm cash flow evidence is available.",
    "business_model_or_segments": "Confirm business model or segment evidence is available.",
    "source_metadata": "Confirm sources have traceable metadata.",
    "evidence_freshness": "Confirm evidence freshness can be reviewed.",
    "missing_evidence_summary": "Summarize missing or incomplete evidence.",
}


@dataclass(frozen=True)
class EvidenceChecklistItem:
    """Single preparation-only evidence checklist item."""

    category: str
    requirement: str
    status: EvidenceItemStatus
    source_references: tuple[dict[str, Any], ...]
    freshness_status: FreshnessStatus
    verification_status: VerificationStatus
    notes: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceChecklist:
    """Preparation-only evidence checklist."""

    company_name: str
    ticker: str
    exchange: str
    listing_country: str
    as_of_date: str
    evidence_items: tuple[EvidenceChecklistItem, ...]
    checklist_status: EvidenceChecklistStatus
    missing_evidence_count: int
    human_review_required: bool


def build_evidence_checklist(payload: dict[str, Any]) -> EvidenceChecklist:
    """Build a safe evidence checklist from an intake payload.

    This function only classifies evidence preparation status.
    It does not imply investment quality, attractiveness, ranking,
    recommendation, allocation, or trade action.
    """

    intake_result = validate_intake(payload)
    evidence_items = tuple(
        _build_item(category, payload)
        for category in REQUIRED_EVIDENCE_CATEGORIES
    )
    missing_count = sum(
        1
        for item in evidence_items
        if item.status in {EvidenceItemStatus.MISSING, EvidenceItemStatus.PARTIAL}
    )

    checklist_status = _classify_checklist_status(
        intake_label=intake_result.label,
        evidence_items=evidence_items,
    )

    return EvidenceChecklist(
        company_name=_clean_string(payload.get("company_name")),
        ticker=_clean_string(payload.get("ticker")),
        exchange=_clean_string(payload.get("exchange")),
        listing_country=_clean_string(payload.get("listing_country")),
        as_of_date=_clean_string(payload.get("as_of_date")),
        evidence_items=evidence_items,
        checklist_status=checklist_status,
        missing_evidence_count=missing_count,
        human_review_required=True,
    )


def _build_item(category: str, payload: dict[str, Any]) -> EvidenceChecklistItem:
    sources = _sources_for_category(category, payload)
    status = _status_for_category(category, payload, sources)
    freshness_status = _freshness_status(sources)
    verification_status = _verification_status(sources)
    notes = _notes_for_item(category, status, sources)

    return EvidenceChecklistItem(
        category=category,
        requirement=EVIDENCE_REQUIREMENTS[category],
        status=status,
        source_references=sources,
        freshness_status=freshness_status,
        verification_status=verification_status,
        notes=notes,
    )


def _sources_for_category(
    category: str,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], ...]:
    if category in {
        "company_identity",
        "listing_and_exchange",
        "source_metadata",
        "evidence_freshness",
    }:
        return _tuple_of_dicts(payload.get("official_filings"))

    if category in {
        "official_financial_statements",
        "operating_revenue",
        "balance_sheet",
        "cash_flow",
        "business_model_or_segments",
    }:
        return _tuple_of_dicts(payload.get("financial_statement_sources"))

    return ()


def _status_for_category(
    category: str,
    payload: dict[str, Any],
    sources: tuple[dict[str, Any], ...],
) -> EvidenceItemStatus:
    if category == "company_identity":
        if _clean_string(payload.get("company_name")) and (
            _clean_string(payload.get("ticker")) or sources
        ):
            return EvidenceItemStatus.PRESENT
        return EvidenceItemStatus.MISSING

    if category == "listing_and_exchange":
        if _clean_string(payload.get("ticker")) and _clean_string(payload.get("exchange")):
            return EvidenceItemStatus.PRESENT
        if _clean_string(payload.get("ticker")) or _clean_string(payload.get("exchange")):
            return EvidenceItemStatus.PARTIAL
        return EvidenceItemStatus.MISSING

    if category == "missing_evidence_summary":
        return EvidenceItemStatus.PRESENT

    if not sources:
        return EvidenceItemStatus.MISSING

    if _has_official_source(sources):
        return EvidenceItemStatus.PRESENT

    return EvidenceItemStatus.PARTIAL


def _freshness_status(sources: tuple[dict[str, Any], ...]) -> FreshnessStatus:
    if not sources:
        return FreshnessStatus.UNKNOWN

    publication_dates = tuple(
        _clean_string(source.get("publication_date"))
        for source in sources
        if _clean_string(source.get("publication_date"))
    )
    if publication_dates:
        return FreshnessStatus.CURRENT
    return FreshnessStatus.UNKNOWN


def _verification_status(sources: tuple[dict[str, Any], ...]) -> VerificationStatus:
    if not sources:
        return VerificationStatus.UNVERIFIED
    if _has_official_source(sources):
        return VerificationStatus.VERIFIED
    return VerificationStatus.PARTIALLY_VERIFIED


def _notes_for_item(
    category: str,
    status: EvidenceItemStatus,
    sources: tuple[dict[str, Any], ...],
) -> tuple[str, ...]:
    if category == "missing_evidence_summary":
        return ("summary_item_only",)
    if status is EvidenceItemStatus.MISSING:
        return ("evidence_missing",)
    if status is EvidenceItemStatus.PARTIAL:
        return ("evidence_partial_or_not_official",)
    if not sources:
        return ("identity_or_listing_fields_used",)
    return ()


def _classify_checklist_status(
    intake_label: IntakeCompletenessLabel,
    evidence_items: tuple[EvidenceChecklistItem, ...],
) -> EvidenceChecklistStatus:
    if intake_label is IntakeCompletenessLabel.INCOMPLETE:
        return EvidenceChecklistStatus.INCOMPLETE

    blocking_items = tuple(
        item
        for item in evidence_items
        if item.category != "missing_evidence_summary"
        and item.status is EvidenceItemStatus.MISSING
    )
    partial_items = tuple(
        item
        for item in evidence_items
        if item.category != "missing_evidence_summary"
        and item.status is EvidenceItemStatus.PARTIAL
    )

    if blocking_items:
        return EvidenceChecklistStatus.INCOMPLETE
    if partial_items:
        return EvidenceChecklistStatus.PARTIAL
    return EvidenceChecklistStatus.READY_FOR_HUMAN_REVIEW


def _tuple_of_dicts(value: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, dict))


def _has_official_source(sources: tuple[dict[str, Any], ...]) -> bool:
    return any(
        _clean_string(source.get("reliability_label")).lower() == "official"
        for source in sources
    )


def _clean_string(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()

