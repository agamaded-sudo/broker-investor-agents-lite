"""Tests for basic backoffice data pack validation."""

from pathlib import Path

import yaml

from broker_agents.backoffice.data_validator import validate_backoffice_pack


def test_validate_backoffice_pack_accepts_minimal_valid_pack() -> None:
    pack = {
        "metadata": {"analysis_date": "2026-06-05"},
        "company_identity": {
            "company_name": "Microsoft Corporation",
            "ticker": "MSFT",
            "exchange": "NASDAQ",
            "market": "US",
            "currency": "USD",
        },
        "business_model": {"summary": "Software and cloud services."},
        "financial_statements_summary": {"periods": []},
        "calculated_financial_metrics": {"metrics": []},
        "sources_confidence_data_gaps": {"source_log": []},
    }

    assert validate_backoffice_pack(pack) == []


def test_validate_backoffice_pack_reports_missing_sections_and_company_fields() -> None:
    pack = {
        "metadata": {"analysis_date": "2026-06-05"},
        "company_identity": {
            "company_name": "Microsoft Corporation",
            "ticker": "",
        },
    }

    messages = validate_backoffice_pack(pack)

    assert "Missing required top-level section: business_model" in messages
    assert "Missing required top-level section: financial_statements_summary" in messages
    assert "Missing required top-level section: calculated_financial_metrics" in messages
    assert "Missing required top-level section: sources_confidence_data_gaps" in messages
    assert "Required company_identity field is empty: ticker" in messages
    assert "Missing required company_identity field: exchange" in messages
    assert "Missing required company_identity field: market" in messages
    assert "Missing required company_identity field: currency" in messages


def test_aapl_manual_input_validates_without_required_section_errors() -> None:
    input_path = Path(__file__).resolve().parents[1] / "examples" / "aapl_input.yaml"
    pack = yaml.safe_load(input_path.read_text(encoding="utf-8"))

    assert validate_backoffice_pack(pack) == []
