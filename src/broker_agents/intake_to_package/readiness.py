"""Safe package readiness classification for the Intake-to-Package MVP.

This module is preparation-only. It does not run investor agents,
produce recommendations, rank companies, allocate capital, generate
trade signals, or create execution instructions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from broker_agents.intake_to_package.evidence_checklist import (
    EvidenceChecklist,
    EvidenceChecklistStatus,
    EvidenceItemStatus,
    VerificationStatus,
    build_evidence_checklist,
)
from broker_agents.intake_to_package.intake_schema import (
    IntakeCompletenessLabel,
    IntakeValidationResult,
    validate_intake,
)


class PackageReadinessLabel(StrEnum):
    """Non-investment package readiness labels."""

    NOT_READY = "not_ready"
    PARTIAL = "partial"
    READY_FOR_HUMAN_REVIEW = "ready_for_human_review"


class PackageReadinessSeverity(StrEnum):
    """Preparation-only blocker and warning severity labels."""

    BLOCKING = "blocking"
    WARNING = "warning"
    INFORMATIONAL = "informational"


BLOCKED_NEXT_STEPS = (
    "investor_agent_execution",
    "persona_review",
    "investor_decision",
    "recommendation",
    "ranking",
    "allocation",
    "rebalancing",
    "trade_signal",
    "execution_instruction",
    "strategy_validation",
    "auto_promotion",
)


@dataclass(frozen=True)
class PackageReadinessBlocker:
    """Blocking preparation issue that must be handled before readiness."""

    blocker_code: str
    blocker_type: str
    severity: PackageReadinessSeverity
    description: str
    related_field: str
    related_evidence_category: str
    required_human_action: str


@dataclass(frozen=True)
class PackageReadinessWarning:
    """Non-blocking preparation warning for human review."""

    warning_code: str
    description: str
    related_field: str
    related_evidence_category: str
    suggested_review_action: str


@dataclass(frozen=True)
class PackageReadiness:
    """Preparation-only package readiness result."""

    company_name: str
    ticker: str
    exchange: str
    listing_country: str
    as_of_date: str
    intake_completeness_label: IntakeCompletenessLabel
    checklist_status: EvidenceChecklistStatus
    readiness_label: PackageReadinessLabel
    blockers: tuple[PackageReadinessBlocker, ...]
    warnings: tuple[PackageReadinessWarning, ...]
    human_review_required: bool
    allowed_next_step: str
    blocked_next_steps: tuple[str, ...]


def build_package_readiness(payload: dict[str, Any]) -> PackageReadiness:
    """Build a safe non-investment package readiness result.

    The result only describes preparation readiness.
    It does not imply investability, attractiveness, ranking,
    recommendation, allocation, or trade action.
    """

    intake_result = validate_intake(payload)
    checklist = build_evidence_checklist(payload)
    blockers = _build_blockers(intake_result, checklist)
    warnings = _build_warnings(checklist)
    readiness_label = _classify_readiness(
        intake_result=intake_result,
        checklist=checklist,
        blockers=blockers,
    )

    return PackageReadiness(
        company_name=checklist.company_name,
        ticker=checklist.ticker,
        exchange=checklist.exchange,
        listing_country=checklist.listing_country,
        as_of_date=checklist.as_of_date,
        intake_completeness_label=intake_result.label,
        checklist_status=checklist.checklist_status,
        readiness_label=readiness_label,
        blockers=blockers,
        warnings=warnings,
        human_review_required=True,
        allowed_next_step=_allowed_next_step(readiness_label),
        blocked_next_steps=BLOCKED_NEXT_STEPS,
    )


def _build_blockers(
    intake_result: IntakeValidationResult,
    checklist: EvidenceChecklist,
) -> tuple[PackageReadinessBlocker, ...]:
    blockers: list[PackageReadinessBlocker] = []

    for missing_field in intake_result.missing_fields:
        blockers.append(
            PackageReadinessBlocker(
                blocker_code=f"missing_intake_field:{missing_field}",
                blocker_type="intake",
                severity=PackageReadinessSeverity.BLOCKING,
                description=f"Missing required intake field: {missing_field}.",
                related_field=missing_field,
                related_evidence_category="",
                required_human_action="complete_intake_field",
            )
        )

    for blocked_output in intake_result.blocked_outputs:
        blockers.append(
            PackageReadinessBlocker(
                blocker_code=f"blocked_requested_output:{blocked_output}",
                blocker_type="safety",
                severity=PackageReadinessSeverity.BLOCKING,
                description=f"Blocked investment output requested: {blocked_output}.",
                related_field="requested_output",
                related_evidence_category="",
                required_human_action="remove_blocked_requested_output",
            )
        )

    for item in checklist.evidence_items:
        if item.category in {
            "official_financial_statements",
            "operating_revenue",
        } and item.status is EvidenceItemStatus.MISSING:
            blockers.append(
                PackageReadinessBlocker(
                    blocker_code=f"missing_required_evidence:{item.category}",
                    blocker_type="evidence",
                    severity=PackageReadinessSeverity.BLOCKING,
                    description=f"Missing required evidence category: {item.category}.",
                    related_field="",
                    related_evidence_category=item.category,
                    required_human_action="collect_required_evidence",
                )
            )

        if item.verification_status is VerificationStatus.FAILED:
            blockers.append(
                PackageReadinessBlocker(
                    blocker_code=f"source_verification_failed:{item.category}",
                    blocker_type="source_verification",
                    severity=PackageReadinessSeverity.BLOCKING,
                    description=f"Source verification failed for {item.category}.",
                    related_field="",
                    related_evidence_category=item.category,
                    required_human_action="replace_or_verify_source",
                )
            )

    return tuple(blockers)


def _build_warnings(
    checklist: EvidenceChecklist,
) -> tuple[PackageReadinessWarning, ...]:
    warnings: list[PackageReadinessWarning] = []

    for item in checklist.evidence_items:
        if item.category == "missing_evidence_summary":
            continue

        if item.status is EvidenceItemStatus.PARTIAL:
            warnings.append(
                PackageReadinessWarning(
                    warning_code=f"partial_evidence:{item.category}",
                    description=f"Evidence is partial for {item.category}.",
                    related_field="",
                    related_evidence_category=item.category,
                    suggested_review_action="review_or_complete_partial_evidence",
                )
            )

        if item.verification_status is VerificationStatus.PARTIALLY_VERIFIED:
            warnings.append(
                PackageReadinessWarning(
                    warning_code=f"partially_verified_source:{item.category}",
                    description=f"Source is partially verified for {item.category}.",
                    related_field="",
                    related_evidence_category=item.category,
                    suggested_review_action="verify_source_before_human_review",
                )
            )

    return tuple(warnings)


def _classify_readiness(
    intake_result: IntakeValidationResult,
    checklist: EvidenceChecklist,
    blockers: tuple[PackageReadinessBlocker, ...],
) -> PackageReadinessLabel:
    if blockers:
        return PackageReadinessLabel.NOT_READY

    if intake_result.label is IntakeCompletenessLabel.INCOMPLETE:
        return PackageReadinessLabel.NOT_READY

    if checklist.checklist_status is EvidenceChecklistStatus.READY_FOR_HUMAN_REVIEW:
        return PackageReadinessLabel.READY_FOR_HUMAN_REVIEW

    return PackageReadinessLabel.PARTIAL


def _allowed_next_step(readiness_label: PackageReadinessLabel) -> str:
    if readiness_label is PackageReadinessLabel.NOT_READY:
        return "fix_intake_or_collect_missing_evidence"
    if readiness_label is PackageReadinessLabel.PARTIAL:
        return "collect_remaining_evidence_or_send_to_human_review_with_gaps"
    return "human_review"

