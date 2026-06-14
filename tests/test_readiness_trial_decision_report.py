"""Tests for conservative readiness trial backtest decisions."""

import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.backtesting.readiness_trial_decision_report import (
    build_readiness_trial_decision_report,
    render_readiness_trial_decision_report,
)
from broker_agents.backtesting.readiness_trial_export import (
    SAFETY_NOTICE,
    TRIAL_LEDGER_FIELDS,
)
from broker_agents.cli import app

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_PRICES = ROOT / "tests" / "fixtures" / "historical_price_history"


def _trial_row(run_id: str, generated_at: str) -> dict:
    row = {field: "" for field in TRIAL_LEDGER_FIELDS}
    row.update(
        {
            "ticker": "COST",
            "signal_date": "2023-06-30",
            "as_of_date": "2023-06-30",
            "generated_at": generated_at,
            "run_id": run_id,
            "archive_record_id": f"COST-{run_id}",
            "status": "completed",
            "trial_signal_source": "historical_readiness_ledger",
            "record_type": "historical_signal_readiness_candidate",
            "source_run_id": run_id,
            "source_run_folder": f"runs/{run_id}",
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
            "coverage_quality_label": "limited_financials",
            "coverage_quality_severity": "moderate",
            "date_coverage_status": "usable_with_warnings",
            "has_delayed_price_anchor": "False",
            "has_limited_financials": "True",
            "warning_count": "2",
            "coverage_guardrail_status": "research_usable_with_warnings",
            "trial_backtest_label": "readiness_only_trial",
            "trial_backtest_allowed": "True",
            "safety_notice": SAFETY_NOTICE,
        }
    )
    return row


def _write_trial_ledger(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRIAL_LEDGER_FIELDS)
        writer.writeheader()
        writer.writerows(
            [
                _trial_row("first-run", "2023-06-30T00:00:00+00:00"),
                _trial_row("latest-run", "2023-06-30T12:00:00+00:00"),
            ]
        )


def _run_readiness_backtest(ledger: Path, outputs_root: Path):
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


def test_build_report_is_not_decision_grade_for_tiny_sample() -> None:
    manifest = {
        "backtest_run_id": "trial-run",
        "backtest_run_type": "readiness_trial",
        "ledger_path": "trial.csv",
        "total_records_before_dedupe": 4,
        "evaluated_records_after_dedupe": 1,
        "duplicate_records_removed": 3,
        "evaluated_records": 1,
        "skipped_records": 0,
    }
    metrics = {
        "sample_size": 1,
        "evaluated_tickers": ["COST"],
        "small_sample_warning": True,
        "concentration_warning": True,
        "synthetic_data_warning": False,
        "median_forward_return_3m": 0.1,
        "median_forward_return_6m": 0.2,
        "median_forward_return_12m": 0.3,
        "median_relative_return_12m": 0.1,
        "hit_rate_vs_benchmark_12m": 1.0,
        "coverage_guardrail_status_counts": {
            "research_usable_with_warnings": 1
        },
        "clean_record_count": 0,
        "warning_record_count": 1,
        "warning_heavy_record_count": 0,
    }

    report = build_readiness_trial_decision_report(
        manifest=manifest,
        metrics=metrics,
        rows=[{"ticker": "COST"}],
    )

    assert report.statistical_validity == "insufficient_sample"
    assert report.decision_status == "not_decision_grade"
    assert (
        report.next_required_action == "expand_sample_before_interpretation"
    )
    assert "Sample size is too small for inference." in report.warnings
    assert any("concentrated" in warning for warning in report.warnings)
    assert any("Dedupe removed" in warning for warning in report.warnings)
    assert any("Single-ticker result" in warning for warning in report.warnings)
    assert report.missing_metadata_fields

    markdown = render_readiness_trial_decision_report(
        report,
        price_provider="csv",
    )
    for text in (
        "Executive Decision",
        "Statistical Validity",
        "Coverage Quality",
        "Dedupe Impact",
        "What This Means",
        "What This Does Not Mean",
        "Next Required Action",
        "Safety Notice",
        "These metrics are diagnostic only and are not decision-grade.",
        "It does not prove a strategy.",
        "Single-ticker result cannot validate a repeatable process.",
        (
            "not a recommendation, ranking, vote, average score, consensus, "
            "allocation instruction, rebalancing instruction, trade signal, "
            "execution instruction, or investment advice."
        ),
    ):
        assert text in markdown


def test_zero_clean_sensitivity_keeps_decision_conservative(
    tmp_path: Path,
) -> None:
    sensitivity_path = tmp_path / "sensitivity.json"
    sensitivity_path.write_text(
        json.dumps(
            {
                "sensitivity_status": "clean_not_available",
                "subset_diagnostics": {
                    "clean_records": {"available": False}
                },
                "key_findings": [
                    "Clean-only interpretation is not available yet."
                ],
            }
        ),
        encoding="utf-8",
    )
    rows = [
        {
            "ticker": f"TICKER{index}",
            "readiness_label": "Ready",
            "source_verification_status": "partial",
            "buffett_interest_level": "present",
            "munger_interest_level": "present",
            "fisher_interest_level": "present",
            "lynch_interest_level": "present",
            "bogle_interest_level": "present",
        }
        for index in range(10)
    ]
    report = build_readiness_trial_decision_report(
        manifest={
            "backtest_run_id": "clean-gate",
            "backtest_run_type": "readiness_trial",
            "clean_coverage_sensitivity_report_json_path": str(
                sensitivity_path
            ),
        },
        metrics={
            "sample_size": 10,
            "evaluated_tickers": [row["ticker"] for row in rows],
            "small_sample_warning": False,
            "concentration_warning": False,
            "synthetic_data_warning": False,
            "warning_heavy_record_count": 0,
        },
        rows=rows,
    )

    assert report.decision_status == "needs_more_samples"
    assert report.statistical_validity == "limited_sample"
    assert report.clean_only_available is False


def test_readiness_backtest_writes_and_links_decision_report(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "readiness_trial.csv"
    outputs_root = tmp_path / "outputs"
    _write_trial_ledger(ledger)

    result = _run_readiness_backtest(ledger, outputs_root)

    assert result.exit_code == 0, result.output
    for text in (
        "Decision Report",
        "Decision Status",
        "not_decision_grade",
        "Statistical Validity",
        "insufficient_sample",
    ):
        assert text in result.output
    manifest = json.loads(
        (
            outputs_root / "backtests" / "latest_backtest_manifest.json"
        ).read_text(encoding="utf-8")
    )
    report_path = Path(manifest["readiness_trial_decision_report_path"])
    report_json_path = Path(
        manifest["readiness_trial_decision_report_json_path"]
    )
    assert report_path.is_file()
    assert report_json_path.is_file()
    assert manifest["decision_status"] == "not_decision_grade"
    assert manifest["statistical_validity"] == "insufficient_sample"
    assert (
        manifest["next_required_action"]
        == "expand_sample_before_interpretation"
    )

    report = json.loads(report_json_path.read_text(encoding="utf-8"))
    assert report["sample_size"] == 1
    assert report["records_before_dedupe"] == 2
    assert report["records_after_dedupe"] == 1
    assert report["duplicate_records_removed"] == 1
    assert report["concentration_warning"] is True
    assert "readiness_label" in report["missing_metadata_fields"]
    markdown = report_path.read_text(encoding="utf-8")
    assert "The pipeline works end-to-end." in markdown
    assert "Missing metadata limits grouped analysis." in markdown


def test_decision_report_regeneration_command(tmp_path: Path) -> None:
    ledger = tmp_path / "readiness_trial.csv"
    outputs_root = tmp_path / "outputs"
    _write_trial_ledger(ledger)
    initial = _run_readiness_backtest(ledger, outputs_root)
    assert initial.exit_code == 0, initial.output
    manifest = json.loads(
        (
            outputs_root / "backtests" / "latest_backtest_manifest.json"
        ).read_text(encoding="utf-8")
    )
    backtest_folder = Path(manifest["summary_path"]).parent

    result = CliRunner().invoke(
        app,
        [
            "generate-readiness-trial-decision-report",
            "--backtest-folder",
            str(backtest_folder),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "not_decision_grade" in result.output
    assert "insufficient_sample" in result.output
    assert "Status" in result.output
    assert "completed" in result.output


def test_standard_backtest_does_not_create_decision_report(
    tmp_path: Path,
) -> None:
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

    result = _run_readiness_backtest(ledger, outputs_root)

    assert result.exit_code == 0, result.output
    manifest = json.loads(
        (
            outputs_root / "backtests" / "latest_backtest_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["backtest_run_type"] == "standard"
    assert manifest["readiness_trial_decision_report_path"] is None
    assert manifest["readiness_trial_decision_report_json_path"] is None
    assert manifest["decision_status"] is None
    assert not (
        Path(manifest["summary_path"]).parent
        / "readiness_trial_decision_report.md"
    ).exists()


def test_task86_documentation_and_demo_runner_remain() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for text in (
        "readiness trial backtest decision report",
        "sample size",
        "dedupe impact",
        "ticker concentration",
        "missing grouped metadata",
        "diagnostic only",
        "generate-readiness-trial-decision-report",
    ):
        assert text in readme

    demo = (ROOT / "scripts" / "run_first_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "python -m ruff check ." in demo
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in demo
    assert "python -m broker_agents.cli" in demo
