"""Tests for the governance-only Portfolio Manager Readiness Agent."""

import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.backoffice.enrichment_pipeline import (
    fixture_paths_for_known_ticker,
    run_backoffice_enrichment_pipeline,
)
from broker_agents.calculators.decision_candidates import CURRENT_DECISIONS
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
)
from broker_agents.cli import app
from broker_agents.portfolio.portfolio_manager_readiness import (
    generate_portfolio_readiness_items,
)
from broker_agents.reports.portfolio_manager_readiness_report import (
    generate_portfolio_manager_readiness_report,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def _enrich_known_tickers(outputs_root: Path) -> None:
    """Create temporary enriched packs for readiness tests."""
    for ticker in ("MSFT", "AAPL", "NVDA"):
        lower = ticker.lower()
        run_backoffice_enrichment_pipeline(
            ROOT / "examples" / f"{lower}_input.yaml",
            outputs_root / ticker / f"{lower}_enriched_input.yaml",
            **fixture_paths_for_known_ticker(ticker, FIXTURES),
        )


def test_portfolio_readiness_items_require_human_review(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    _enrich_known_tickers(outputs_root)

    items = generate_portfolio_readiness_items(
        ["MSFT", "AAPL", "NVDA"],
        outputs_root,
        ROOT / "examples",
    )

    assert {item.ticker for item in items} == {"MSFT", "AAPL", "NVDA"}
    assert all(item.portfolio_status == "Human Review Required" for item in items)
    assert all(item.readiness_label == "Needs Review" for item in items)
    assert all(item.manual_trigger_required for item in items)
    assert all(
        {
            "no_trade_execution",
            "no_buy_sell_signal",
            "no_final_weights",
            "no_rebalancing",
            "no_auto_promotion",
            "human_review_required",
            "final_decisions_unchanged",
            "not_a_recommendation",
        }.issubset(item.safety_flags)
        for item in items
    )
    for item in items:
        for investor, decision in CURRENT_DECISIONS.items():
            assert f"{investor.title()}: {decision}" in item.final_decision_summary


def test_portfolio_readiness_report_contains_role_and_safety_boundaries(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    _enrich_known_tickers(outputs_root)
    items = generate_portfolio_readiness_items(
        ["MSFT", "AAPL", "NVDA"],
        outputs_root,
        ROOT / "examples",
    )

    report = generate_portfolio_manager_readiness_report(items)

    for heading in (
        "Portfolio Manager Readiness Report",
        "Portfolio Manager Role Boundary",
        "Companies Reviewed",
        "Portfolio Readiness Assessment",
        "Cross-Portfolio Risk Summary",
        "Manual Trigger List",
        "Human Review Dependencies",
        "Not Ready For Execution",
        "Safety Check",
    ):
        assert heading in report
    assert "does not buy or sell" in report
    assert "does not assign final weights" in report
    assert "does not rebalance" in report
    assert "does not enable auto-promotion" in report
    assert "not a recommendation, ranking, vote, average score, consensus" in report
    assert "allocation instruction" in report
    assert "trade signal" in report


def test_portfolio_readiness_cli_writes_markdown_and_json(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    _enrich_known_tickers(outputs_root)
    markdown_path = tmp_path / "portfolio_readiness.md"
    json_path = tmp_path / "portfolio_readiness.json"

    result = CliRunner().invoke(
        app,
        [
            "portfolio-readiness",
            "--tickers",
            "MSFT,AAPL,NVDA",
            "--outputs-root",
            str(outputs_root),
            "--examples-root",
            str(ROOT / "examples"),
            "--output",
            str(markdown_path),
            "--json-output",
            str(json_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert markdown_path.exists()
    assert json_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert len(payload) == 3
    assert all(item["portfolio_status"] == "Human Review Required" for item in payload)
    assert all(item["manual_trigger_required"] is True for item in payload)
    assert all("no_auto_promotion" in item["safety_flags"] for item in payload)


def test_portfolio_readiness_does_not_enable_auto_promotion(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    _enrich_known_tickers(outputs_root)
    for ticker in ("MSFT", "AAPL", "NVDA"):
        lower = ticker.lower()
        import yaml

        pack = yaml.safe_load(
            (outputs_root / ticker / f"{lower}_enriched_input.yaml").read_text(
                encoding="utf-8"
            )
        )
        for investor in CURRENT_DECISIONS:
            assert (
                evaluate_promotion_eligibility(pack, investor)[
                    "auto_promotion_allowed"
                ]
                is False
            )
