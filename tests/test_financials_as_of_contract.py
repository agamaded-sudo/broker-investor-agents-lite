"""Tests for official-financials point-in-time readiness contracts."""

import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.historical.financials_as_of_contract import (
    REQUIRED_DATE_FIELDS,
    build_financials_as_of_contract,
)
from broker_agents.historical.snapshot_contract import (
    build_historical_snapshot_contract,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
HISTORICAL_PRICES = FIXTURES / "historical_price_history"
PORTFOLIO_CONTEXT = EXAMPLES / "portfolio_context.yaml"
EXPECTED_COST_DECISIONS = {
    "Buffett": "Wait for Better Price / Complete Intrinsic Value Work",
    "Munger": (
        "Buy Gradually / Wait for Better Evidence on Incentives and "
        "Long-Term Durability"
    ),
    "Fisher": "Needs More Scuttlebutt / Watch Closely",
    "Lynch": "Follow / Watch",
    "Bogle": "Prefer Broad Index",
}


def test_current_financials_contract_is_current_analysis() -> None:
    contract = build_financials_as_of_contract(
        None,
        fixtures_root=FIXTURES,
        ticker="COST",
    )

    assert contract.as_of_date is None
    assert contract.historical_mode is False
    assert contract.section == "official_financials"
    assert contract.provider_name == "sec_fixture"
    assert contract.status == "current_analysis"
    assert contract.allowed_filing_cutoff is None
    assert "source_url_or_accession_number" in contract.available_date_fields


def test_historical_financials_contract_reports_readiness_and_missing_dates() -> None:
    contract = build_financials_as_of_contract(
        "2023-06-30",
        fixtures_root=FIXTURES,
        ticker="COST",
    )
    payload = contract.to_dict()

    assert payload["as_of_date"] == "2023-06-30"
    assert payload["historical_mode"] is True
    assert payload["provider_name"] == "sec_fixture"
    assert payload["section"] == "official_financials"
    assert payload["supports_as_of_date"] is False
    assert payload["enforcement_level"] == "readiness_only"
    assert payload["leakage_risk"] == "high"
    assert payload["status"] == "readiness_only"
    assert payload["allowed_filing_cutoff"] == "2023-06-30"
    assert set(payload["required_date_fields"]) == set(REQUIRED_DATE_FIELDS)
    for field in (
        "fiscal_period_end_date",
        "filing_date",
        "accepted_date",
        "statement_type",
        "period_type",
    ):
        assert field in payload["missing_date_fields"]
    assert any(
        "not yet guaranteed point-in-time safe" in warning
        for warning in payload["warnings"]
    )
    capability = payload["provider_capability"]
    assert capability["supports_filing_date"] is False
    assert capability["supports_period_end_date"] is False
    assert capability["supports_accepted_date"] is False
    assert capability["supports_as_of_filtering"] is False


def test_snapshot_contract_uses_financials_as_of_capability() -> None:
    contract = build_historical_snapshot_contract(
        "2023-06-30",
        price_provider="csv",
        input_mode="validation",
        fixtures_root=FIXTURES,
        price_data_root=HISTORICAL_PRICES,
        ticker="COST",
    )
    financials = next(
        item
        for item in contract.provider_capabilities
        if item.section == "official_financials"
    )

    assert financials.provider_name == "sec_fixture"
    assert financials.supports_as_of_date is False
    assert financials.enforcement_level == "readiness_only"
    assert financials.leakage_risk == "high"
    assert "filing-date or accepted-date filtering" in financials.notes


def test_historical_run_includes_financials_contract_without_decision_changes(
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
    manifest_path = (
        outputs_root / "COST" / "runs" / "latest_run_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    contract = manifest["official_financials_as_of_contract"]
    assert contract["section"] == "official_financials"
    assert contract["supports_as_of_date"] is False
    assert contract["enforcement_level"] == "readiness_only"
    assert contract["leakage_risk"] == "high"
    assert contract["required_date_fields"]
    assert contract["missing_date_fields"]
    assert contract["warnings"]

    summary = (
        manifest_path.parent / manifest["run_id"] / "run_summary.md"
    ).read_text(encoding="utf-8")
    for text in (
        "Official Financials As-Of Contract",
        "Official financials are not yet guaranteed point-in-time safe.",
        "Required Date Fields",
        "Missing Date Fields",
        "This official financials as-of contract is not a recommendation",
    ):
        assert text in summary

    package = json.loads(
        (
            outputs_root
            / "COST"
            / "deal_package"
            / "cost_broker_deal_package.json"
        ).read_text(encoding="utf-8")
    )
    decisions = {
        response["investor"]: response.get("broker_facing_final_decision")
        or response["final_decision"]
        for response in package["investor_responses"]
    }
    assert decisions == EXPECTED_COST_DECISIONS
    assert "no_auto_promotion" in package["workflow_result"]["safety_flags"]


def test_financials_validation_commands_are_offline_and_explicit() -> None:
    snapshot = CliRunner().invoke(
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
    financials = CliRunner().invoke(
        app,
        [
            "validate-financials-as-of",
            "--as-of-date",
            "2023-06-30",
            "--fixtures-root",
            str(FIXTURES),
            "--ticker",
            "COST",
        ],
    )

    assert snapshot.exit_code == 0, snapshot.output
    for text in (
        "Official Financials As-Of Readiness",
        "filing-date or accepted-date filtering",
        "Official Financials Status: readiness_only",
        "Official financials are not yet guaranteed point-in-time safe",
    ):
        assert text in snapshot.output
    assert financials.exit_code == 0, financials.output
    for text in (
        "Official Financials As-Of Contract",
        "enforcement_level=readiness_only",
        "leakage_risk=high",
        "status=readiness_only",
        "not yet guaranteed point-in-time safe",
    ):
        assert text in financials.output

    source = (
        ROOT
        / "src"
        / "broker_agents"
        / "historical"
        / "financials_as_of_contract.py"
    ).read_text(encoding="utf-8").lower()
    for network_call in (
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "urlopen(",
    ):
        assert network_call not in source
