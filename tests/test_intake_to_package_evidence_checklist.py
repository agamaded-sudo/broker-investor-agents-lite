from broker_agents.intake_to_package import (
    EvidenceChecklistStatus,
    EvidenceItemStatus,
    FreshnessStatus,
    VerificationStatus,
    build_evidence_checklist,
)


def test_build_evidence_checklist_incomplete_when_intake_incomplete() -> None:
    checklist = build_evidence_checklist(
        {
            "ticker": "MSFT",
            "exchange": "NASDAQ",
            "as_of_date": "2026-06-24",
            "requested_output": "intake_summary",
        }
    )

    assert checklist.checklist_status is EvidenceChecklistStatus.INCOMPLETE
    assert checklist.human_review_required is True


def test_build_evidence_checklist_contains_required_categories() -> None:
    checklist = build_evidence_checklist(_complete_payload())

    categories = tuple(item.category for item in checklist.evidence_items)

    assert categories == (
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


def test_build_evidence_checklist_ready_for_human_review_when_sources_official() -> None:
    checklist = build_evidence_checklist(_complete_payload())

    assert checklist.checklist_status is EvidenceChecklistStatus.READY_FOR_HUMAN_REVIEW
    assert checklist.missing_evidence_count == 0
    assert checklist.human_review_required is True


def test_build_evidence_checklist_marks_missing_financial_sources() -> None:
    payload = _complete_payload()
    payload.pop("financial_statement_sources")

    checklist = build_evidence_checklist(payload)

    assert checklist.checklist_status is EvidenceChecklistStatus.INCOMPLETE
    assert checklist.missing_evidence_count > 0


def test_build_evidence_checklist_marks_unofficial_sources_partial() -> None:
    payload = _complete_payload()
    payload["financial_statement_sources"] = [
        {
            "title": "Secondary financial summary",
            "reliability_label": "trusted_secondary",
            "publication_date": "2026-01-01",
        }
    ]

    checklist = build_evidence_checklist(payload)

    assert checklist.checklist_status is EvidenceChecklistStatus.PARTIAL
    assert any(
        item.status is EvidenceItemStatus.PARTIAL
        for item in checklist.evidence_items
    )


def test_build_evidence_checklist_tracks_source_freshness_and_verification() -> None:
    checklist = build_evidence_checklist(_complete_payload())

    financial_item = next(
        item
        for item in checklist.evidence_items
        if item.category == "official_financial_statements"
    )

    assert financial_item.freshness_status is FreshnessStatus.CURRENT
    assert financial_item.verification_status is VerificationStatus.VERIFIED


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
        "requested_output": ["evidence_checklist"],
        "official_filings": [official_source],
        "financial_statement_sources": [official_source],
    }

