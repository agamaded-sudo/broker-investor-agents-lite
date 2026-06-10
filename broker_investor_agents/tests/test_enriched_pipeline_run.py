"""Tests for running deterministic investor reports from enriched packs."""

from pathlib import Path

from typer.testing import CliRunner

from broker_agents.backoffice.enrichment_pipeline import (
    fixture_paths_for_known_ticker,
    run_backoffice_enrichment_pipeline,
)
from broker_agents.cli import app

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
PORTFOLIO_CONTEXT = ROOT / "examples" / "portfolio_context.yaml"


def _make_enriched_pack(ticker: str, outputs_root: Path) -> Path:
    """Create a temporary enriched input pack for one ticker."""
    ticker_upper = ticker.upper()
    ticker_lower = ticker.lower()
    output_path = outputs_root / ticker_upper / f"{ticker_lower}_enriched_input.yaml"
    run_backoffice_enrichment_pipeline(
        ROOT / "examples" / f"{ticker_lower}_input.yaml",
        output_path,
        **fixture_paths_for_known_ticker(ticker_upper, FIXTURES),
    )
    return output_path


def test_run_enriched_pipeline_command_generates_msft_reports(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    enriched_input = _make_enriched_pack("MSFT", outputs_root)
    output_dir = outputs_root / "MSFT" / "enriched"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "run-enriched-pipeline",
            "--ticker",
            "MSFT",
            "--input",
            str(enriched_input),
            "--output-dir",
            str(output_dir),
            "--portfolio-context",
            str(PORTFOLIO_CONTEXT),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output_dir.exists()
    expected_files = [
        "msft_backoffice_data_pack.md",
        "msft_buffett_report.md",
        "msft_munger_report.md",
        "msft_fisher_report.md",
        "msft_lynch_report.md",
        "msft_bogle_report.md",
        "msft_agents_summary.md",
        "msft_reports_quality_review.md",
    ]
    for filename in expected_files:
        assert (output_dir / filename).exists()


def test_run_enriched_pipelines_skips_missing_input(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    _make_enriched_pack("MSFT", outputs_root)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "run-enriched-pipelines",
            "--tickers",
            "MSFT,ZZZZ",
            "--outputs-root",
            str(outputs_root),
            "--portfolio-context",
            str(PORTFOLIO_CONTEXT),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Skipping ZZZZ" in result.output
    assert (outputs_root / "MSFT" / "enriched" / "msft_agents_summary.md").exists()
