"""End-to-end tests for the unified analyze-stock command."""

from pathlib import Path

from typer.testing import CliRunner

from broker_agents.cli import app

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
PORTFOLIO_CONTEXT = EXAMPLES / "portfolio_context.yaml"
EXPECTED_DECISIONS = (
    "Wait for Better Price / Complete Intrinsic Value Work",
    "Buy Gradually / Wait for Better Evidence on Incentives and Long-Term Durability",
    "Needs More Scuttlebutt / Watch Closely",
    "Follow / Watch",
    "Prefer Broad Index",
)


def test_analyze_stock_generates_complete_cost_output_bundle(
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
    for summary_field in (
        "Unified Stock Analysis",
        "Ticker",
        "Broker Deal Package",
        "Enriched Input",
        "Investor Response Letters",
        "Investor Follow-Up Memos",
        "Backoffice Work Orders",
        "Source Verification Status",
        "Readiness Label",
        "Total Investor Responses",
        "Total Work Orders",
        "Promotion-Blocking Categories",
        "completed",
    ):
        assert summary_field in result.output

    ticker_dir = outputs_root / "COST"
    deal_dir = ticker_dir / "deal_package"
    package_path = deal_dir / "cost_broker_deal_package.md"
    assert (ticker_dir / "deal_intake_report.md").exists()
    assert (ticker_dir / "deal_intake_report.json").exists()
    assert package_path.exists()
    assert (deal_dir / "cost_deal_enriched_input.yaml").exists()
    assert len(
        list((deal_dir / "investor_response_letters").glob("*.md"))
    ) == 5
    assert len(
        list((deal_dir / "investor_follow_up_memos").glob("*.md"))
    ) == 5
    assert (
        deal_dir
        / "backoffice_work_orders"
        / "cost_backoffice_work_orders.md"
    ).exists()

    package = package_path.read_text(encoding="utf-8")
    for section in (
        "Source Verification Matrix",
        "Investor Follow-Up Memos",
        "Backoffice Work Orders",
        "Safety Check",
    ):
        assert section in package
    for decision in EXPECTED_DECISIONS:
        assert decision in package
    package_lower = package.lower()
    for boundary in (
        "not a recommendation",
        "ranking",
        "vote",
        "consensus",
        "allocation instruction",
        "trade signal",
    ):
        assert boundary in package_lower
    assert "Auto-promotion disabled." in package


def test_analyze_stock_is_documented_and_demo_runner_remains() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Unified One-Command Run" in readme
    assert "python -m broker_agents.cli analyze-stock --ticker COST" in readme

    demo_script = (ROOT / "scripts" / "run_first_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "python -m ruff check ." in demo_script
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in demo_script
    assert "python -m broker_agents.cli deal-intakes" in demo_script
    assert "python -m broker_agents.cli run-deals" in demo_script
