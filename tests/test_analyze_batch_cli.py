"""End-to-end tests for the analyze-batch command."""

import json
from pathlib import Path

from typer.testing import CliRunner
import yaml

from broker_agents.cli import app

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
PORTFOLIO_CONTEXT = EXAMPLES / "portfolio_context.yaml"
TICKERS = ["MSFT", "AAPL", "NVDA", "COST"]


def _invoke_ticker_batch(outputs_root: Path, tickers: str) -> object:
    """Run analyze-batch in ticker mode with the repository fixtures."""
    return CliRunner().invoke(
        app,
        [
            "analyze-batch",
            "--tickers",
            tickers,
            "--batch-label",
            "demo_batch",
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


def _latest_batch(outputs_root: Path) -> tuple[Path, dict]:
    """Return the batch folder and latest manifest payload."""
    latest_path = outputs_root / "batch_runs" / "latest_batch_manifest.json"
    assert latest_path.exists()
    manifest = json.loads(latest_path.read_text(encoding="utf-8"))
    return outputs_root / "batch_runs" / manifest["batch_run_id"], manifest


def test_analyze_batch_generates_four_ticker_archive(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"

    result = _invoke_ticker_batch(outputs_root, ",".join(TICKERS))

    assert result.exit_code == 0, result.output
    for value in (
        "Batch Stock Analysis",
        "Batch Run ID",
        "Batch Folder",
        "Batch Manifest",
        "Batch Summary",
        "Completed: 4",
        *TICKERS,
    ):
        assert value in result.output

    batch_folder, manifest = _latest_batch(outputs_root)
    summary_path = batch_folder / "batch_summary.md"
    manifest_path = batch_folder / "batch_manifest.json"
    assert summary_path.exists()
    assert manifest_path.exists()
    assert "demo_batch" in manifest["batch_run_id"]
    assert manifest["input_mode"] == "tickers"
    assert manifest["requested_tickers"] == TICKERS
    assert manifest["completed_tickers"] == TICKERS
    assert manifest["failed_tickers"] == []
    assert manifest["completed_count"] == 4
    assert len(manifest["results"]) == 4

    for ticker_result in manifest["results"]:
        ticker = ticker_result["ticker"]
        assert ticker_result["status"] == "completed"
        assert Path(ticker_result["run_folder"]).is_dir()
        assert Path(ticker_result["run_manifest_path"]).is_file()
        assert Path(ticker_result["broker_deal_package_path"]).is_file()
        assert ticker_result["readiness_label"]
        assert ticker_result["source_verification_status"]
        assert ticker_result["total_investor_responses"] == 5
        assert ticker_result["total_work_orders"] > 0
        assert (outputs_root / ticker / "deal_package").is_dir()
        assert (outputs_root / ticker / "runs").is_dir()

    summary = summary_path.read_text(encoding="utf-8")
    for value in (*TICKERS, "Completed Count: 4", "Safety Note"):
        assert value in summary
    summary_lower = summary.lower()
    for boundary in (
        "not a recommendation",
        "ranking",
        "vote",
        "average score",
        "consensus",
        "allocation instruction",
        "rebalancing instruction",
        "trade signal",
        "auto-promotion disabled",
    ):
        assert boundary in summary_lower

    cost_package = (
        outputs_root
        / "COST"
        / "deal_package"
        / "cost_broker_deal_package.md"
    ).read_text(encoding="utf-8")
    for section in (
        "Source Verification Matrix",
        "Investor Follow-Up Memos",
        "Backoffice Work Orders",
        "Safety Check",
    ):
        assert section in cost_package


def test_analyze_batch_supports_intake_files(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    intake_path = tmp_path / "cost_batch_intake.yaml"
    intake_path.write_text(
        yaml.safe_dump(
            {
                "ticker": "COST",
                "company_name": "Costco Wholesale Corporation",
                "run_label": "cost_batch",
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
        [
            "analyze-batch",
            "--intake-files",
            str(intake_path),
        ],
    )

    assert result.exit_code == 0, result.output
    _, manifest = _latest_batch(outputs_root)
    assert manifest["input_mode"] == "intake_files"
    assert manifest["requested_tickers"] == ["COST"]
    assert manifest["completed_tickers"] == ["COST"]
    ticker_result = manifest["results"][0]
    assert ticker_result["status"] == "completed"
    assert "cost_batch" in ticker_result["run_id"]


def test_analyze_batch_records_failure_and_keeps_success(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"

    result = _invoke_ticker_batch(outputs_root, "COST,NOTREAL")

    assert result.exit_code == 0, result.output
    _, manifest = _latest_batch(outputs_root)
    assert manifest["completed_tickers"] == ["COST"]
    assert manifest["failed_tickers"] == ["NOTREAL"]
    assert manifest["completed_count"] == 1
    assert manifest["failed_count"] == 1
    failed = next(
        item for item in manifest["results"] if item["ticker"] == "NOTREAL"
    )
    assert failed["status"] == "failed"
    assert failed["error"]
    assert (
        outputs_root
        / "COST"
        / "deal_package"
        / "cost_broker_deal_package.md"
    ).exists()


def test_analyze_batch_is_documented_and_demo_runner_remains() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Batch Analyze Many Tickers" in readme
    assert (
        "python -m broker_agents.cli analyze-batch --tickers "
        "MSFT,AAPL,NVDA,COST"
    ) in readme
    assert "data/outputs/batch_runs/{BATCH_RUN_ID}/" in readme
    assert "latest_batch_manifest.json" in readme

    demo_script = (ROOT / "scripts" / "run_first_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "python -m ruff check ." in demo_script
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in demo_script
    assert "python -m broker_agents.cli deal-intakes" in demo_script
    assert "python -m broker_agents.cli run-deals" in demo_script
