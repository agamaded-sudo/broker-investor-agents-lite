"""Tests for category-level source verification in broker outputs."""

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from broker_agents.backoffice.enrichment_pipeline import (
    fixture_paths_for_known_ticker,
    run_backoffice_enrichment_pipeline,
)
from broker_agents.backoffice.portfolio_context import (
    load_portfolio_context,
    merge_portfolio_context_into_pack,
)
from broker_agents.backoffice.source_verification_matrix import (
    summarize_source_verification_matrix,
)
from broker_agents.calculators.decision_candidates import CURRENT_DECISIONS
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
)
from broker_agents.cli import app
from broker_agents.deals.broker_deal_workflow import run_broker_deal_workflow
from broker_agents.reports.post_enrichment_gap_report import (
    generate_post_enrichment_gap_report,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
PORTFOLIO_CONTEXT = EXAMPLES / "portfolio_context.yaml"
REQUIRED_CATEGORIES = {
    "official_financials",
    "market_data",
    "historical_valuation",
    "growth_peg",
    "scuttlebutt",
    "management_incentives",
    "index_overlap",
}


def _enriched_cost_pack(tmp_path: Path) -> dict:
    output = tmp_path / "cost_enriched_input.yaml"
    run_backoffice_enrichment_pipeline(
        EXAMPLES / "cost_input.yaml",
        output,
        **fixture_paths_for_known_ticker("COST", FIXTURES),
    )
    pack = yaml.safe_load(output.read_text(encoding="utf-8"))
    context = load_portfolio_context(PORTFOLIO_CONTEXT)
    return merge_portfolio_context_into_pack(pack, context)


def test_cost_source_verification_matrix_has_all_categories(
    tmp_path: Path,
) -> None:
    summary = summarize_source_verification_matrix(_enriched_cost_pack(tmp_path))
    matrix = {item.category: item for item in summary.categories}

    assert set(matrix) == REQUIRED_CATEGORIES
    assert summary.overall_status == "partially verified"
    assert matrix["official_financials"].status in {
        "verified",
        "partially_verified",
    }
    assert matrix["market_data"].status in {"verified", "partially_verified"}
    assert matrix["historical_valuation"].status in {
        "verified",
        "partially_verified",
    }
    assert matrix["growth_peg"].status in {"verified", "partially_verified"}
    for category in ("scuttlebutt", "management_incentives", "index_overlap"):
        assert matrix[category].status in {
            "missing",
            "placeholder_heavy",
            "partially_verified",
        }
    assert any(
        matrix[category].blocks_promotion
        for category in ("scuttlebutt", "management_incentives", "index_overlap")
    )


def test_cost_broker_package_contains_source_verification_matrix(
    tmp_path: Path,
) -> None:
    result = run_broker_deal_workflow(
        ticker="COST",
        input_pack_path=EXAMPLES / "cost_input.yaml",
        outputs_root=tmp_path / "outputs",
        fixtures_root=FIXTURES,
        portfolio_context_path=PORTFOLIO_CONTEXT,
    )
    package = result.broker_deal_package_path.read_text(encoding="utf-8")
    payload = json.loads(
        (
            result.deal_output_dir / "cost_broker_deal_package.json"
        ).read_text(encoding="utf-8")
    )

    assert "Source Verification Matrix" in package
    for category in REQUIRED_CATEGORIES:
        assert category in package
    assert "Blocks Promotion" in package
    assert set(
        item["category"]
        for item in payload["source_verification_matrix"]["categories"]
    ) == REQUIRED_CATEGORIES


def test_run_deals_cli_writes_cost_source_verification_matrix(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    result = CliRunner().invoke(
        app,
        [
            "run-deals",
            "--tickers",
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
    package_path = (
        outputs_root
        / "COST"
        / "deal_package"
        / "cost_broker_deal_package.md"
    )
    package = package_path.read_text(encoding="utf-8")

    assert "Source Verification Matrix" in package
    assert "Category verification summary" in package
    for category in REQUIRED_CATEGORIES:
        assert f"| {category} |" in package
    matrix_rows = [
        line
        for line in package.splitlines()
        if any(f"| {category} |" in line for category in REQUIRED_CATEGORIES)
    ]
    assert any(row.rstrip().endswith("| Yes |") for row in matrix_rows)
    for boundary in (
        "No recommendation.",
        "No ranking.",
        "No consensus.",
        "No portfolio allocation.",
        "No trade signal.",
        "Auto-promotion disabled.",
    ):
        assert boundary in package
    for decision in (
        "Wait for Better Price / Complete Intrinsic Value Work",
        "Buy Gradually / Wait for Better Evidence on Incentives and Long-Term Durability",
        "Needs More Scuttlebutt / Watch Closely",
        "Follow / Watch",
        "Prefer Broad Index",
    ):
        assert decision in package


def test_post_enrichment_report_contains_compact_source_matrix(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    run_backoffice_enrichment_pipeline(
        EXAMPLES / "cost_input.yaml",
        outputs_root / "COST" / "cost_enriched_input.yaml",
        **fixture_paths_for_known_ticker("COST", FIXTURES),
    )

    report = generate_post_enrichment_gap_report(
        ["COST"],
        outputs_root,
        EXAMPLES,
    )

    assert "Source Verification Matrix After Enrichment" in report
    for category in REQUIRED_CATEGORIES:
        assert category in report


def test_cost_decisions_and_safety_boundaries_remain_unchanged(
    tmp_path: Path,
) -> None:
    result = run_broker_deal_workflow(
        ticker="COST",
        input_pack_path=EXAMPLES / "cost_input.yaml",
        outputs_root=tmp_path / "outputs",
        fixtures_root=FIXTURES,
        portfolio_context_path=PORTFOLIO_CONTEXT,
    )
    package = result.broker_deal_package_path.read_text(encoding="utf-8")
    expected_displayed_decisions = (
        "Wait for Better Price / Complete Intrinsic Value Work",
        "Buy Gradually / Wait for Better Evidence on Incentives and Long-Term Durability",
        "Needs More Scuttlebutt / Watch Closely",
        "Follow / Watch",
        "Prefer Broad Index",
    )
    for decision in expected_displayed_decisions:
        assert decision in package
    for boundary in (
        "No recommendation.",
        "No ranking.",
        "No consensus.",
        "No portfolio allocation.",
        "No trade signal.",
        "Auto-promotion disabled.",
    ):
        assert boundary in package

    pack = _enriched_cost_pack(tmp_path / "eligibility")
    for investor, final_decision in CURRENT_DECISIONS.items():
        eligibility = evaluate_promotion_eligibility(pack, investor)
        assert eligibility["current_final_decision"] == final_decision
        assert eligibility["auto_promotion_allowed"] is False


def test_first_demo_runner_still_uses_python_module_commands() -> None:
    script = (ROOT / "scripts" / "run_first_demo.ps1").read_text(encoding="utf-8")

    assert "python -m ruff check ." in script
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in script
    assert "python -m broker_agents.cli deal-intakes" in script
    assert "python -m broker_agents.cli run-deals" in script
