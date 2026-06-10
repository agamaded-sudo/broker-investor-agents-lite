"""Tests for the Backoffice-to-investor broker deal workflow."""

import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.calculators.decision_candidates import CURRENT_DECISIONS
from broker_agents.cli import app
from broker_agents.deals.broker_deal_workflow import run_broker_deal_workflow

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
PORTFOLIO_CONTEXT = ROOT / "examples" / "portfolio_context.yaml"


def test_run_broker_deal_workflow_creates_msft_package(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"

    result = run_broker_deal_workflow(
        ticker="MSFT",
        input_pack_path=ROOT / "examples" / "msft_input.yaml",
        outputs_root=outputs_root,
        fixtures_root=FIXTURES,
        portfolio_context_path=PORTFOLIO_CONTEXT,
    )

    assert result.deal_output_dir.exists()
    assert result.enriched_pack_path.exists()
    assert result.backoffice_report_path.exists()
    assert result.investor_summary_path.exists()
    assert result.broker_deal_package_path.exists()
    assert len(result.investor_response_letter_paths) == 5
    assert all(path.exists() for path in result.investor_response_letter_paths.values())
    assert set(result.investor_reports) == set(CURRENT_DECISIONS)
    assert all(path.exists() for path in result.investor_reports.values())
    assert result.applied_enrichment_sources == [
        "official_financials",
        "market_data",
        "historical_valuation",
        "growth_peg",
    ]
    package = result.broker_deal_package_path.read_text(encoding="utf-8")
    assert "Independent Investor Responses" in package
    assert "Investor Response Letters" in package
    for decision in CURRENT_DECISIONS.values():
        assert decision in package
    json_path = result.deal_output_dir / "msft_broker_deal_package.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert len(payload["investor_responses"]) == 5
    assert payload["executive_summary"]["ticker"] == "MSFT"
    assert payload["executive_summary"]["conditional_interest_investors"]
    assert "auto_promotion_disabled" in payload["executive_summary"]["safety_flags"]
    assert len(
        payload["workflow_result"]["investor_response_letter_paths"]
    ) == 5
    assert "no_auto_promotion" in payload["safety_flags"]


def test_run_deals_cli_creates_all_known_packages(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"

    result = CliRunner().invoke(
        app,
        [
            "run-deals",
            "--tickers",
            "MSFT,AAPL,NVDA",
            "--examples-root",
            str(ROOT / "examples"),
            "--outputs-root",
            str(outputs_root),
            "--fixtures-root",
            str(FIXTURES),
            "--portfolio-context",
            str(PORTFOLIO_CONTEXT),
        ],
    )

    assert result.exit_code == 0, result.output
    for ticker in ("MSFT", "AAPL", "NVDA"):
        lower = ticker.lower()
        deal_dir = outputs_root / ticker / "deal_package"
        assert (deal_dir / f"{lower}_broker_deal_package.md").exists()
        assert (deal_dir / f"{lower}_broker_deal_package.json").exists()
        assert (deal_dir / f"{lower}_deal_enriched_input.yaml").exists()
        assert (deal_dir / "investor_outputs" / f"{lower}_agents_summary.md").exists()
        letter_dir = deal_dir / "investor_response_letters"
        assert letter_dir.is_dir()
        assert len(list(letter_dir.glob("*_response_letter.md"))) == 5


def test_missing_fixture_is_skipped_without_failing(tmp_path: Path) -> None:
    empty_fixtures = tmp_path / "fixtures"
    empty_fixtures.mkdir()

    result = run_broker_deal_workflow(
        ticker="MSFT",
        input_pack_path=ROOT / "examples" / "msft_input.yaml",
        outputs_root=tmp_path / "outputs",
        fixtures_root=empty_fixtures,
        portfolio_context_path=PORTFOLIO_CONTEXT,
    )

    assert result.applied_enrichment_sources == []
    assert set(result.skipped_enrichment_sources) == {
        "official_financials",
        "market_data",
        "historical_valuation",
        "growth_peg",
    }
    assert result.broker_deal_package_path.exists()
