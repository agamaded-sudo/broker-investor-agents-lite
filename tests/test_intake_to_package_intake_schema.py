from broker_agents.intake_to_package import (
    IntakeCompletenessLabel,
    blocked_requested_outputs,
    normalize_requested_outputs,
    validate_intake,
)


def test_normalize_requested_outputs_accepts_string_and_list() -> None:
    assert normalize_requested_outputs("Missing Evidence Report") == (
        "missing_evidence_report",
    )
    assert normalize_requested_outputs(["intake-summary", "package readiness"]) == (
        "intake_summary",
        "package_readiness",
    )


def test_blocked_requested_outputs_detects_investment_outputs() -> None:
    assert blocked_requested_outputs(["recommendation", "buy signal"]) == (
        "recommendation",
        "buy_signal",
    )


def test_validate_intake_ready_for_evidence_checklist() -> None:
    result = validate_intake(
        {
            "company_name": "Microsoft Corporation",
            "ticker": "MSFT",
            "exchange": "NASDAQ",
            "listing_country": "United States",
            "as_of_date": "2026-06-24",
            "requested_output": [
                "intake_summary",
                "evidence_checklist",
                "missing_evidence_report",
            ],
        }
    )

    assert result.label is IntakeCompletenessLabel.READY_FOR_EVIDENCE_CHECKLIST
    assert result.can_continue_to_evidence_checklist is True
    assert result.missing_fields == ()
    assert result.blocked_outputs == ()


def test_validate_intake_minimum_identity_complete_without_requested_output() -> None:
    result = validate_intake(
        {
            "company_name": "Microsoft Corporation",
            "ticker": "MSFT",
            "exchange": "NASDAQ",
            "listing_country": "United States",
            "as_of_date": "2026-06-24",
        }
    )

    assert result.label is IntakeCompletenessLabel.MINIMUM_IDENTITY_COMPLETE
    assert result.can_continue_to_evidence_checklist is False


def test_validate_intake_incomplete_when_company_name_missing() -> None:
    result = validate_intake(
        {
            "ticker": "MSFT",
            "exchange": "NASDAQ",
            "as_of_date": "2026-06-24",
            "requested_output": "intake_summary",
        }
    )

    assert result.label is IntakeCompletenessLabel.INCOMPLETE
    assert "company_name" in result.missing_fields


def test_validate_intake_incomplete_when_ticker_has_no_exchange() -> None:
    result = validate_intake(
        {
            "company_name": "Microsoft Corporation",
            "ticker": "MSFT",
            "as_of_date": "2026-06-24",
            "requested_output": "intake_summary",
        }
    )

    assert result.label is IntakeCompletenessLabel.INCOMPLETE
    assert "exchange" in result.missing_fields


def test_validate_intake_rejects_blocked_outputs() -> None:
    result = validate_intake(
        {
            "company_name": "Microsoft Corporation",
            "ticker": "MSFT",
            "exchange": "NASDAQ",
            "as_of_date": "2026-06-24",
            "requested_output": ["recommendation", "allocation"],
        }
    )

    assert result.label is IntakeCompletenessLabel.INCOMPLETE
    assert result.blocked_outputs == ("recommendation", "allocation")


def test_validate_intake_accepts_official_identity_evidence_without_ticker() -> None:
    result = validate_intake(
        {
            "company_name": "Private Example Company",
            "as_of_date": "2026-06-24",
            "official_filings": [
                {
                    "title": "Official company registry record",
                    "reliability_label": "official",
                }
            ],
            "requested_output": "intake_summary",
        }
    )

    assert result.label is IntakeCompletenessLabel.READY_FOR_EVIDENCE_CHECKLIST
    assert result.missing_fields == ()

