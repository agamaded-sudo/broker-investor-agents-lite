"""End-to-end tests for the unified analyze-stock command."""

from pathlib import Path

from typer.testing import CliRunner
import yaml

from broker_agents.cli import app
from broker_agents.deals.analyze_stock_intake import (
    DEFAULT_INVESTORS,
    load_analyze_stock_intake,
)

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
        "Input Mode",
        "ticker",
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


def test_analyze_stock_intake_file_mode_generates_traceable_bundle(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    intake_path = tmp_path / "cost_intake.yaml"
    intake_path.write_text(
        yaml.safe_dump(
            {
                "ticker": "cost",
                "company_name": "Costco Wholesale Corporation",
                "market": "US",
                "exchange": "NASDAQ",
                "sector": "Consumer Staples / Retail",
                "purpose": "broker_review",
                "investor_set": DEFAULT_INVESTORS,
                "evidence_mode": "fixtures",
                "output_mode": "full_bundle",
                "run_label": "cost_demo",
                "examples_root": str(EXAMPLES),
                "outputs_root": str(outputs_root),
                "fixtures_root": str(FIXTURES),
                "portfolio_context": str(PORTFOLIO_CONTEXT),
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        ["analyze-stock", "--intake-file", str(intake_path)],
    )

    assert result.exit_code == 0, result.output
    assert "intake_file" in result.output
    assert str(intake_path) in result.output
    assert "cost_demo" in result.output
    deal_dir = outputs_root / "COST" / "deal_package"
    package_path = deal_dir / "cost_broker_deal_package.md"
    assert package_path.exists()
    assert (deal_dir / "investor_response_letters").is_dir()
    assert (deal_dir / "investor_follow_up_memos").is_dir()
    assert (
        deal_dir
        / "backoffice_work_orders"
        / "cost_backoffice_work_orders.md"
    ).exists()
    snapshot_path = deal_dir / "analyze_stock_intake_snapshot.yaml"
    snapshot = yaml.safe_load(snapshot_path.read_text(encoding="utf-8"))
    assert snapshot["ticker"] == "COST"
    assert snapshot["input_mode"] == "intake_file"
    assert snapshot["purpose"] == "broker_review"
    assert snapshot["evidence_mode"] == "fixtures"
    assert snapshot["output_mode"] == "full_bundle"
    assert snapshot["run_label"] == "cost_demo"
    assert snapshot["intake_file"] == str(intake_path)

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


def test_analyze_stock_rejects_ambiguous_or_missing_file_ticker(
    tmp_path: Path,
) -> None:
    example_intake = (
        ROOT / "examples" / "deal_intakes" / "cost_analyze_stock_intake.yaml"
    )
    ambiguous = CliRunner().invoke(
        app,
        [
            "analyze-stock",
            "--ticker",
            "COST",
            "--intake-file",
            str(example_intake),
        ],
    )
    assert ambiguous.exit_code != 0
    assert "either --ticker or --intake-file, not both" in ambiguous.output

    missing_ticker_path = tmp_path / "missing_ticker.yaml"
    missing_ticker_path.write_text(
        "purpose: broker_review\n",
        encoding="utf-8",
    )
    missing = CliRunner().invoke(
        app,
        ["analyze-stock", "--intake-file", str(missing_ticker_path)],
    )
    assert missing.exit_code != 0
    assert "requires a non-empty ticker" in missing.output


def test_analyze_stock_intake_parser_supports_json_and_defaults(
    tmp_path: Path,
) -> None:
    json_path = tmp_path / "intake.json"
    json_path.write_text('{"ticker": "cost"}', encoding="utf-8")

    intake = load_analyze_stock_intake(json_path)

    assert intake.ticker == "COST"
    assert intake.purpose == "broker_review"
    assert intake.evidence_mode == "fixtures"
    assert intake.output_mode == "full_bundle"
    assert intake.investor_set == DEFAULT_INVESTORS
    assert intake.examples_root == Path("examples")
    assert intake.outputs_root == Path("data/outputs")
    assert intake.fixtures_root == Path("tests/fixtures")
    assert intake.portfolio_context == Path("examples/portfolio_context.yaml")


def test_analyze_stock_is_documented_and_demo_runner_remains() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Unified One-Command Run" in readme
    assert "python -m broker_agents.cli analyze-stock --ticker COST" in readme
    assert "Structured Analyze-Stock Intake" in readme
    assert (
        "python -m broker_agents.cli analyze-stock --intake-file "
        "examples/deal_intakes/cost_analyze_stock_intake.yaml"
    ) in readme
    assert (
        ROOT / "examples" / "deal_intakes" / "cost_analyze_stock_intake.yaml"
    ).exists()

    demo_script = (ROOT / "scripts" / "run_first_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "python -m ruff check ." in demo_script
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in demo_script
    assert "python -m broker_agents.cli deal-intakes" in demo_script
    assert "python -m broker_agents.cli run-deals" in demo_script
