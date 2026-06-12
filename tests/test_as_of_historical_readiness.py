"""Tests for as-of-date historical analysis readiness metadata."""

from datetime import date
import json
from pathlib import Path

from typer.testing import CliRunner
import yaml

from broker_agents.cli import app
from broker_agents.deals.analyze_stock_intake import (
    load_analyze_stock_intake,
)
from broker_agents.historical.as_of_context import build_as_of_context

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
PORTFOLIO_CONTEXT = EXAMPLES / "portfolio_context.yaml"
HISTORICAL_INTAKE = (
    EXAMPLES / "deal_intakes" / "cost_historical_as_of_intake.yaml"
)


def _historical_args(outputs_root: Path) -> list[str]:
    """Build the repository's offline historical-readiness CLI arguments."""
    return [
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
    ]


def test_as_of_context_validates_format_and_future_dates() -> None:
    context = build_as_of_context(
        "2023-06-30",
        system_date=date(2026, 6, 12),
    )

    assert context.as_of_date == date(2023, 6, 30)
    assert context.historical_mode is True
    assert context.point_in_time_enforcement == "readiness_only"
    assert "does not yet guarantee" in context.data_cutoff_note
    assert context.leakage_warning

    for invalid in ("2023/06/30", "2023-02-30"):
        try:
            build_as_of_context(invalid, system_date=date(2026, 6, 12))
        except ValueError as exc:
            assert "as_of_date" in str(exc)
        else:
            raise AssertionError(f"Expected invalid as_of_date: {invalid}")

    try:
        build_as_of_context(
            "2027-01-01",
            system_date=date(2026, 6, 12),
        )
    except ValueError as exc:
        assert "future" in str(exc)
    else:
        raise AssertionError("Expected a future as_of_date rejection.")


def test_analyze_stock_historical_readiness_metadata_and_ledger(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"

    result = CliRunner().invoke(app, _historical_args(outputs_root))

    assert result.exit_code == 0, result.output
    for text in (
        "As-Of Date",
        "2023-06-30",
        "Historical Mode",
        "enabled",
        "Point-in-Time Enforcement",
        "readiness_only",
    ):
        assert text in result.output

    latest_manifest_path = (
        outputs_root / "COST" / "runs" / "latest_run_manifest.json"
    )
    manifest = json.loads(
        latest_manifest_path.read_text(encoding="utf-8")
    )
    assert manifest["as_of_date"] == "2023-06-30"
    assert manifest["historical_mode"] is True
    assert manifest["point_in_time_enforcement"] == "readiness_only"
    assert manifest["leakage_warning"]
    assert manifest["data_cutoff_note"]

    run_folder = (
        outputs_root / "COST" / "runs" / manifest["run_id"]
    )
    summary = (run_folder / "run_summary.md").read_text(encoding="utf-8")
    summary_lower = summary.lower()
    for text in (
        "As-Of Date: 2023-06-30",
        "Historical Mode: enabled",
        "Point-in-Time Enforcement: readiness_only",
        "Historical Analysis Warning",
        "full point-in-time data enforcement",
        "not a recommendation",
        "trade signal",
    ):
        assert text.lower() in summary_lower
    assert (
        "This historical analysis readiness mode is not a recommendation"
        in summary
    )

    snapshot = yaml.safe_load(
        (
            outputs_root
            / "COST"
            / "deal_package"
            / "analyze_stock_ticker_snapshot.yaml"
        ).read_text(encoding="utf-8")
    )
    assert snapshot["as_of_date"] == "2023-06-30"

    ledger_path = outputs_root / "signal_archive" / "signal_ledger.jsonl"
    record = json.loads(
        ledger_path.read_text(encoding="utf-8").splitlines()[-1]
    )
    assert record["as_of_date"] == "2023-06-30"
    assert record["historical_mode"] is True
    assert record["point_in_time_enforcement"] == "readiness_only"


def test_current_mode_and_historical_intake_remain_compatible(
    tmp_path: Path,
) -> None:
    intake = load_analyze_stock_intake(HISTORICAL_INTAKE)
    assert intake.ticker == "COST"
    assert intake.as_of_date == "2023-06-30"

    current_outputs = tmp_path / "current_outputs"
    current_result = CliRunner().invoke(
        app,
        [
            "analyze-stock",
            "--ticker",
            "COST",
            "--examples-root",
            str(EXAMPLES),
            "--outputs-root",
            str(current_outputs),
            "--fixtures-root",
            str(FIXTURES),
            "--portfolio-context",
            str(PORTFOLIO_CONTEXT),
        ],
    )
    assert current_result.exit_code == 0, current_result.output
    current_manifest = json.loads(
        (
            current_outputs
            / "COST"
            / "runs"
            / "latest_run_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert current_manifest["as_of_date"] is None
    assert current_manifest["historical_mode"] is False
    assert (
        current_manifest["point_in_time_enforcement"]
        == "readiness_only"
    )
    assert current_manifest["leakage_warning"] is None


def test_analyze_batch_propagates_as_of_date(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    result = CliRunner().invoke(
        app,
        [
            "analyze-batch",
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
            "--as-of-date",
            "2023-06-30",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "As-Of Date: 2023-06-30" in result.output
    assert "Historical Mode: enabled" in result.output
    run_manifest = json.loads(
        (
            outputs_root
            / "COST"
            / "runs"
            / "latest_run_manifest.json"
        ).read_text(encoding="utf-8")
    )
    batch_manifest = json.loads(
        (
            outputs_root
            / "batch_runs"
            / "latest_batch_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert run_manifest["as_of_date"] == "2023-06-30"
    assert run_manifest["historical_mode"] is True
    assert batch_manifest["as_of_date"] == "2023-06-30"
    assert batch_manifest["historical_mode"] is True


def test_as_of_readiness_is_documented_and_network_free() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "As-Of-Date Historical Analysis Readiness" in readme
    assert "--as-of-date 2023-06-30" in readme
    assert "point-in-time" in readme.lower()
    assert HISTORICAL_INTAKE.exists()

    historical_source = (
        ROOT / "src" / "broker_agents" / "historical" / "as_of_context.py"
    ).read_text(encoding="utf-8").lower()
    for network_call in (
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "urlopen(",
    ):
        assert network_call not in historical_source
