from broker_agents.intake_to_package import (
    EvidenceChecklistStatus,
    IntakeCompletenessLabel,
    PackageReadinessLabel,
    PackageReadinessSeverity,
    build_package_readiness,
)


def test_build_package_readiness_ready_for_human_review() -> None:
    readiness = build_package_readiness(_complete_payload())

    assert readiness.readiness_label is PackageReadinessLabel.READY_FOR_HUMAN_REVIEW
    assert readiness.checklist_status is EvidenceChecklistStatus.READY_FOR_HUMAN_REVIEW
    assert readiness.allowed_next_step == "human_review"
    assert readiness.human_review_required is True
    assert readiness.blockers == ()


def test_build_package_readiness_not_ready_when_intake_incomplete() -> None:
    readiness = build_package_readiness(
        {
            "ticker": "MSFT",
            "exchange": "NASDAQ",
            "as_of_date": "2026-06-24",
            "requested_output": "intake_summary",
        }
    )

    assert readiness.readiness_label is PackageReadinessLabel.NOT_READY
    assert readiness.intake_completeness_label is IntakeCompletenessLabel.INCOMPLETE
    assert readiness.allowed_next_step == "fix_intake_or_collect_missing_evidence"
    assert any(
        blocker.related_field == "company_name"
        for blocker in readiness.blockers
    )


def test_build_package_readiness_not_ready_when_blocked_output_requested() -> None:
    payload = _complete_payload()
    payload["requested_output"] = ["recommendation"]

    readiness = build_package_readiness(payload)

    assert readiness.readiness_label is PackageReadinessLabel.NOT_READY
    assert any(
        blocker.blocker_code == "blocked_requested_output:recommendation"
        for blocker in readiness.blockers
    )


def test_build_package_readiness_not_ready_when_core_financial_evidence_missing() -> None:
    payload = _complete_payload()
    payload.pop("financial_statement_sources")

    readiness = build_package_readiness(payload)

    assert readiness.readiness_label is PackageReadinessLabel.NOT_READY
    assert any(
        blocker.related_evidence_category == "official_financial_statements"
        for blocker in readiness.blockers
    )
    assert all(
        blocker.severity is PackageReadinessSeverity.BLOCKING
        for blocker in readiness.blockers
    )


def test_build_package_readiness_partial_when_evidence_is_unofficial() -> None:
    payload = _complete_payload()
    payload["financial_statement_sources"] = [
        {
            "title": "Secondary financial summary",
            "reliability_label": "trusted_secondary",
            "publication_date": "2026-01-01",
        }
    ]

    readiness = build_package_readiness(payload)

    assert readiness.readiness_label is PackageReadinessLabel.PARTIAL
    assert readiness.allowed_next_step == (
        "collect_remaining_evidence_or_send_to_human_review_with_gaps"
    )
    assert readiness.blockers == ()
    assert readiness.warnings


def test_build_package_readiness_blocks_investment_next_steps() -> None:
    readiness = build_package_readiness(_complete_payload())

    assert "investor_agent_execution" in readiness.blocked_next_steps
    assert "recommendation" in readiness.blocked_next_steps
    assert "ranking" in readiness.blocked_next_steps
    assert "allocation" in readiness.blocked_next_steps
    assert "trade_signal" in readiness.blocked_next_steps


def _complete_payload() -> dict[str, object]:
    official_source = {
        "title": "Official annual report",
        "url_or_path": "https://example.com/annual-report",
        "source_type": "annual_report",
        "publication_date": "2026-01-01",
        "access_date": "2026-06-24",
        "reliability_label": "official",
    }
    return {
        "company_name": "Microsoft Corporation",
        "ticker": "MSFT",
        "exchange": "NASDAQ",
        "listing_country": "United States",
        "as_of_date": "2026-06-24",
        "requested_output": ["package_readiness"],
        "official_filings": [official_source],
        "financial_statement_sources": [official_source],
    }

