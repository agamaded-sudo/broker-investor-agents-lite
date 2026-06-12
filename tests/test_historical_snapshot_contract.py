"""Tests for the point-in-time historical snapshot contract."""

import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.historical.snapshot_contract import (
    SECTIONS,
    build_historical_snapshot_contract,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
HISTORICAL_PRICES = (
    FIXTURES / "historical_price_history"
)
PORTFOLIO_CONTEXT = EXAMPLES / "portfolio_context.yaml"


def test_current_snapshot_contract_has_no_historical_warnings() -> None:
    contract = build_historical_snapshot_contract(
        None,
        price_provider="fixture",
        input_mode="ticker",
        fixtures_root=FIXTURES,
    )

    assert contract.as_of_date is None
    assert contract.historical_mode is False
    assert contract.snapshot_status == "current_analysis"
    assert contract.point_in_time_enforcement == "readiness_only"
    assert contract.warnings == []
    assert len(contract.provider_capabilities) == len(SECTIONS)


def test_historical_snapshot_contract_exposes_capabilities_and_risks() -> None:
    contract = build_historical_snapshot_contract(
        "2023-06-30",
        price_provider="csv",
        input_mode="validation",
        fixtures_root=FIXTURES,
        price_data_root=HISTORICAL_PRICES,
    )
    payload = contract.to_dict()

    assert payload["as_of_date"] == "2023-06-30"
    assert payload["historical_mode"] is True
    assert payload["snapshot_status"] == "readiness_only"
    assert payload["point_in_time_enforcement"] == "readiness_only"
    for field in (
        "supported_sections",
        "unsupported_sections",
        "leakage_risk_sections",
        "provider_capabilities",
        "warnings",
    ):
        assert field in payload
    assert "market_prices" in payload["supported_sections"]
    assert set(payload["leakage_risk_sections"]) == set(SECTIONS)
    assert "Full point-in-time enforcement is not yet guaranteed." in (
        payload["warnings"]
    )

    by_section = {
        item["section"]: item for item in payload["provider_capabilities"]
    }
    prices = by_section["market_prices"]
    assert prices["provider_name"] == "csv"
    assert prices["supports_as_of_date"] is True
    assert prices["enforcement_level"] == "partial"
    assert prices["leakage_risk"] == "medium"
    for section in (
        "official_financials",
        "historical_valuation",
        "growth_peg",
        "market_snapshot",
        "scuttlebutt",
        "management_incentives",
        "index_overlap",
    ):
        assert by_section[section]["enforcement_level"] == "readiness_only"
        assert by_section[section]["leakage_risk"] == "high"


def test_analyze_stock_manifest_and_summary_include_snapshot_contract(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    result = CliRunner().invoke(
        app,
        [
            "analyze-stock",
            "--ticker",
            "COST",
            "--examples-root",
            str(EXAMPLES),
            "--outputs-root",
            str(outputs_root),
            "--fixtures-root",
            str(FIXTURES),
            "--portfolio-context",
            str(PORTFOLIO_CONTEXT),
            "--as-of-date",
            "2023-06-30",
        ],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(
        (
            outputs_root
            / "COST"
            / "runs"
            / "latest_run_manifest.json"
        ).read_text(encoding="utf-8")
    )
    contract = manifest["historical_snapshot_contract"]
    assert contract["snapshot_status"] == "readiness_only"
    assert contract["point_in_time_enforcement"] == "readiness_only"
    assert contract["supported_sections"] == []
    assert contract["unsupported_sections"] == []
    assert contract["leakage_risk_sections"]
    assert len(contract["provider_capabilities"]) == len(SECTIONS)
    assert contract["warnings"]

    summary = (
        outputs_root
        / "COST"
        / "runs"
        / manifest["run_id"]
        / "run_summary.md"
    ).read_text(encoding="utf-8")
    summary_lower = summary.lower()
    for text in (
        "Historical Data Snapshot Contract",
        "Snapshot Status",
        "Point-in-Time Enforcement",
        "Supported Sections",
        "Unsupported Sections",
        "Leakage Risk Sections",
        "Provider Capability Summary",
        "Full point-in-time enforcement is not yet guaranteed.",
        "This historical snapshot contract is not a recommendation",
    ):
        assert text.lower() in summary_lower

    ledger_record = json.loads(
        (
            outputs_root / "signal_archive" / "signal_ledger.jsonl"
        ).read_text(encoding="utf-8").splitlines()[-1]
    )
    assert ledger_record["snapshot_status"] == "readiness_only"
    assert ledger_record["leakage_risk_sections_count"] == len(SECTIONS)


def test_current_analyze_stock_has_contract_without_historical_section(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    result = CliRunner().invoke(
        app,
        [
            "analyze-stock",
            "--ticker",
            "COST",
            "--examples-root",
            str(EXAMPLES),
            "--outputs-root",
            str(outputs_root),
            "--fixtures-root",
            str(FIXTURES),
            "--portfolio-context",
            str(PORTFOLIO_CONTEXT),
        ],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(
        (
            outputs_root
            / "COST"
            / "runs"
            / "latest_run_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["historical_snapshot_contract"]["snapshot_status"] == (
        "current_analysis"
    )
    assert manifest["historical_snapshot_contract"]["warnings"] == []
    summary = (
        outputs_root
        / "COST"
        / "runs"
        / manifest["run_id"]
        / "run_summary.md"
    ).read_text(encoding="utf-8")
    assert "Historical Data Snapshot Contract" not in summary


def test_validate_historical_snapshot_command_is_offline() -> None:
    result = CliRunner().invoke(
        app,
        [
            "validate-historical-snapshot",
            "--as-of-date",
            "2023-06-30",
            "--price-provider",
            "csv",
            "--price-fixtures",
            str(HISTORICAL_PRICES),
        ],
    )

    assert result.exit_code == 0, result.output
    for text in (
        "Historical Data Snapshot Contract",
        "section=market_prices",
        "provider=csv",
        "supports_as_of_date=true",
        "enforcement_level=partial",
        "leakage_risk=medium",
        "section=official_financials",
        "leakage_risk=high",
        "Snapshot Status: readiness_only",
        "Full point-in-time enforcement is not yet guaranteed.",
    ):
        assert text in result.output

    source = (
        ROOT
        / "src"
        / "broker_agents"
        / "historical"
        / "snapshot_contract.py"
    ).read_text(encoding="utf-8").lower()
    for network_call in (
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "urlopen(",
    ):
        assert network_call not in source
