"""Tests for readiness-only trial backtest classification and guardrails."""

import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.backtesting.readiness_trial_export import (
    SAFETY_NOTICE,
    TRIAL_LEDGER_FIELDS,
)
from broker_agents.cli import app

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_PRICES = ROOT / "tests" / "fixtures" / "historical_price_history"


def _trial_row(**overrides) -> dict:
    row = {field: "" for field in TRIAL_LEDGER_FIELDS}
    row.update(
        {
            "ticker": "COST",
            "signal_date": "2023-06-30",
            "as_of_date": "2023-06-30",
            "generated_at": "2023-06-30T00:00:00+00:00",
            "run_id": "readiness-run",
            "archive_record_id": "COST-readiness-run",
            "status": "completed",
            "trial_signal_source": "historical_readiness_ledger",
            "record_type": "historical_signal_readiness_candidate",
            "source_run_id": "source-run",
            "source_run_folder": "runs/source-run",
            "source_candidate_file": "candidate.json",
            "source_assembly_file": "assembly.json",
            "signal_generation_status": "readiness_only",
            "safe_for_historical_signal_generation": "False",
            "not_trade_signal": "True",
            "not_recommendation": "True",
            "not_allocation_instruction": "True",
            "assembly_status": "partial_historical_input",
            "partial_sections_count": "2",
            "readiness_only_sections_count": "8",
            "leakage_risk_sections_count": "10",
            "blocking_reasons_count": "10",
            "warnings_count": "4",
            "trial_backtest_label": "readiness_only_trial",
            "trial_backtest_allowed": "True",
            "safety_notice": SAFETY_NOTICE,
        }
    )
    row.update(overrides)
    return row


def _write_ledger(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRIAL_LEDGER_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _run_backtest(ledger: Path, outputs_root: Path):
    return CliRunner().invoke(
        app,
        [
            "backtest-signals",
            "--ledger",
            str(ledger),
            "--price-provider",
            "csv",
            "--price-fixtures",
            str(HISTORICAL_PRICES),
            "--outputs-root",
            str(outputs_root),
            "--lookback-years",
            "5",
            "--dedupe-mode",
            "latest_per_ticker_per_day",
        ],
    )


def test_readiness_trial_backtest_preserves_labels_and_notice(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "readiness_trial.csv"
    outputs_root = tmp_path / "outputs"
    _write_ledger(ledger, [_trial_row()])

    result = _run_backtest(ledger, outputs_root)

    assert result.exit_code == 0, result.output
    assert "Backtest Run Type" in result.output
    assert "readiness_trial" in result.output
    manifest = json.loads(
        (
            outputs_root / "backtests" / "latest_backtest_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["backtest_run_type"] == "readiness_trial"
    assert manifest["source_ledger_type"] == (
        "historical_readiness_trial_ledger"
    )
    assert manifest["readiness_only"] is True
    assert manifest["not_trade_signal"] is True
    assert manifest["not_recommendation"] is True
    assert manifest["not_allocation_instruction"] is True
    assert manifest["safety_notice"]
    assert manifest["input_rows"] == 1
    assert manifest["evaluated_rows"] == 1
    assert manifest["skipped_rows"] == 0
    assert manifest["invalid_readiness_rows"] == 0
    assert manifest["dedupe_mode"] == "latest_per_ticker_per_day"

    summary = Path(manifest["summary_path"]).read_text(encoding="utf-8")
    for text in (
        "Readiness Trial Backtest Notice",
        "Backtest Run Type: readiness_trial",
        "Readiness Only: Yes",
        "Not Trade Signal: Yes",
        "Not Recommendation: Yes",
        "Not Allocation Instruction: Yes",
        (
            "These results must not be interpreted as investment "
            "recommendations or trading signals."
        ),
    ):
        assert text in summary

    with Path(manifest["results_path"]).open(
        encoding="utf-8",
        newline="",
    ) as handle:
        row = next(csv.DictReader(handle))
    for field in (
        "record_type",
        "signal_generation_status",
        "not_trade_signal",
        "not_recommendation",
        "not_allocation_instruction",
        "source_run_id",
        "assembly_status",
        "partial_sections_count",
        "readiness_only_sections_count",
        "leakage_risk_sections_count",
        "blocking_reasons_count",
        "trial_backtest_label",
    ):
        assert row[field] == _trial_row()[field]
    assert row["data_status"] == "complete_local_csv"


def test_invalid_readiness_rows_are_skipped_with_warning(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "readiness_trial.csv"
    outputs_root = tmp_path / "outputs"
    _write_ledger(
        ledger,
        [
            _trial_row(),
            _trial_row(
                run_id="invalid-run",
                archive_record_id="COST-invalid-run",
                not_trade_signal="False",
            ),
        ],
    )

    result = _run_backtest(ledger, outputs_root)

    assert result.exit_code == 0, result.output
    manifest = json.loads(
        (
            outputs_root / "backtests" / "latest_backtest_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["backtest_run_type"] == "readiness_trial"
    assert manifest["input_rows"] == 2
    assert manifest["evaluated_rows"] == 1
    assert manifest["skipped_rows"] == 1
    assert manifest["invalid_readiness_rows"] == 1
    assert any(
        "Skipped readiness trial row" in warning
        for warning in manifest["quality_warnings"]
    )
    with Path(manifest["results_path"]).open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1


def test_standard_backtest_remains_standard(tmp_path: Path) -> None:
    ledger = tmp_path / "standard.csv"
    outputs_root = tmp_path / "outputs"
    with ledger.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("ticker", "run_id", "generated_at", "status"),
        )
        writer.writeheader()
        writer.writerow(
            {
                "ticker": "COST",
                "run_id": "standard-run",
                "generated_at": "2023-06-30T00:00:00+00:00",
                "status": "completed",
            }
        )

    result = _run_backtest(ledger, outputs_root)

    assert result.exit_code == 0, result.output
    manifest = json.loads(
        (
            outputs_root / "backtests" / "latest_backtest_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["backtest_run_type"] == "standard"
    assert manifest["source_ledger_type"] == "standard_signal_ledger"
    assert manifest["readiness_only"] is False
    assert manifest["not_trade_signal"] is False
    assert manifest["not_recommendation"] is False
    assert manifest["safety_notice"] is None
    summary = Path(manifest["summary_path"]).read_text(encoding="utf-8")
    assert "Readiness Trial Backtest Notice" not in summary


def test_task85_documentation_and_demo_runner_remain() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for text in (
        "readiness trial backtest",
        "not a trading strategy backtest",
        "not a recommendation backtest",
        "deduplication should remain enabled",
        "concentration and small-sample warnings are expected",
        "research diagnostics only",
    ):
        assert text in readme

    demo = (ROOT / "scripts" / "run_first_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "python -m ruff check ." in demo
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in demo
    assert "python -m broker_agents.cli" in demo
