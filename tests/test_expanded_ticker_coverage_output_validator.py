"""Tests for final expanded ticker coverage output validation."""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner
import yaml

from broker_agents.backtesting.expanded_ticker_coverage_output_validator import (
    load_latest_expanded_ticker_coverage_manifest,
    render_expanded_ticker_coverage_output_validation_report,
    validate_expanded_ticker_coverage_outputs,
    write_expanded_ticker_coverage_output_validation_report,
)
from broker_agents.cli import app

CORE = ["MSFT", "AAPL", "NVDA", "COST"]
EXPANDED = ["GOOGL", "AMZN", "META", "AVGO", "ORCL", "CRM", "ADBE", "NFLX"]
TICKERS = CORE + EXPANDED


def _write_source(
    outputs_root: Path,
    run_id: str = "20260101_000000",
) -> dict:
    folder = outputs_root / "expanded_ticker_coverage" / run_id
    folder.mkdir(parents=True)
    matrix = []
    summaries = []
    for ticker in TICKERS:
        for index in range(3):
            matrix.append(
                {
                    "ticker": ticker,
                    "as_of_date": f"202{index + 1}-06-30",
                    "eligibility": "eligible_clean",
                    "coverage_quality": "clean",
                }
            )
        for index in range(2):
            matrix.append(
                {
                    "ticker": ticker,
                    "as_of_date": f"202{index + 1}-12-31",
                    "eligibility": "eligible_with_warnings",
                    "coverage_quality": "delayed_price_anchor",
                }
            )
        matrix.append(
            {
                "ticker": ticker,
                "as_of_date": "2023-12-31",
                "eligibility": "not_eligible",
                "coverage_quality": "unsupported",
            }
        )
        summaries.append(
            {
                "ticker": ticker,
                "status": "eligible_for_expanded_trial",
                "clean_records": 3,
                "usable_records": 5,
                "not_eligible_records": 1,
            }
        )
    report_path = folder / "expanded_ticker_coverage_report.json"
    matrix_path = folder / "expanded_ticker_coverage_matrix.csv"
    eligible_path = folder / "expanded_ticker_eligible_universe.yaml"
    report = {
        "validation_run_id": run_id,
        "validation_status": "valid_with_cautions",
        "requested_tickers": TICKERS,
        "eligible_tickers": TICKERS,
        "caution_tickers": [],
        "excluded_tickers": [],
        "ticker_summaries": summaries,
        "coverage_quality_counts": {
            "clean": 36,
            "delayed_price_anchor": 24,
            "unsupported": 12,
        },
        "eligibility_counts": {
            "eligible_clean": 36,
            "eligible_with_warnings": 24,
            "not_eligible": 12,
        },
        "next_research_action": "run_expanded_ticker_readiness_trial",
        "safety_notice": "Research-only coverage validation.",
    }
    report_path.write_text(json.dumps(report), encoding="utf-8")
    with matrix_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "ticker",
                "as_of_date",
                "eligibility",
                "coverage_quality",
            ),
        )
        writer.writeheader()
        writer.writerows(matrix)
    eligible_path.write_text(
        yaml.safe_dump({"tickers": TICKERS}),
        encoding="utf-8",
    )
    latest_path = (
        outputs_root
        / "expanded_ticker_coverage"
        / "latest_expanded_ticker_coverage_manifest.json"
    )
    latest = {
        "validation_run_id": run_id,
        "validation_status": "valid_with_cautions",
        "validation_folder": str(folder),
        "report_json_path": str(report_path),
        "matrix_csv_path": str(matrix_path),
        "eligible_universe_path": str(eligible_path),
        "safety_notice": "Research-only coverage validation.",
        "next_research_action": "run_expanded_ticker_readiness_trial",
    }
    latest_path.write_text(json.dumps(latest), encoding="utf-8")
    return {
        "folder": folder,
        "report_path": report_path,
        "matrix_path": matrix_path,
        "eligible_path": eligible_path,
        "latest_path": latest_path,
        "latest": latest,
    }


def _validate(outputs_root: Path, source: dict):
    return validate_expanded_ticker_coverage_outputs(
        validation_check_run_id="check",
        generated_at="2026-06-15T00:00:00+00:00",
        outputs_root=outputs_root,
        validation_run_id=source["latest"]["validation_run_id"],
        latest_manifest={
            **source["latest"],
            "_manifest_path": str(source["latest_path"]),
        },
    )


def _statuses(report) -> dict:
    return {item["check"]: item["status"] for item in report.checks}


def test_latest_manifest_and_explicit_run_load(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    source = _write_source(outputs)
    latest = load_latest_expanded_ticker_coverage_manifest(outputs)
    assert latest["validation_run_id"] == "20260101_000000"

    report = _validate(outputs, source)
    assert report.source_validation_run_id == "20260101_000000"
    assert report.output_validation_status == "ready_with_warnings"
    assert report.readiness_for_expanded_trial is True
    assert report.clean_record_total == 36
    assert report.usable_record_total == 60
    assert report.unsupported_record_total == 12
    assert report.fail_count == 0


def test_missing_latest_manifest_raises_clear_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="manifest not found"):
        load_latest_expanded_ticker_coverage_manifest(tmp_path / "outputs")


@pytest.mark.parametrize(
    ("filename_key", "check_name"),
    [
        ("report_path", "report_json_present"),
        ("matrix_path", "matrix_csv_present"),
        ("eligible_path", "eligible_universe_present"),
    ],
)
def test_missing_source_outputs_are_not_ready(
    tmp_path: Path,
    filename_key: str,
    check_name: str,
) -> None:
    outputs = tmp_path / "outputs"
    source = _write_source(outputs)
    source[filename_key].unlink()
    report = _validate(outputs, source)
    assert report.output_validation_status == "not_ready_missing_outputs"
    assert report.readiness_for_expanded_trial is False
    assert _statuses(report)[check_name] == "fail"


def test_required_membership_and_ticker_minimum_checks(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    source = _write_source(outputs)
    payload = json.loads(source["report_path"].read_text(encoding="utf-8"))
    payload["eligible_tickers"] = CORE
    payload["ticker_summaries"][0]["clean_records"] = 1
    payload["ticker_summaries"][1]["usable_records"] = 2
    source["report_path"].write_text(json.dumps(payload), encoding="utf-8")

    report = _validate(outputs, source)
    statuses = _statuses(report)
    assert statuses["eligible_ticker_count"] == "fail"
    assert statuses["current_core_tickers_preserved"] == "pass"
    assert statuses["expanded_tickers_present"] == "fail"
    assert statuses["ticker_clean_record_minimum"] == "fail"
    assert statuses["ticker_usable_record_minimum"] == "fail"


def test_matrix_count_and_unsupported_consistency_checks(
    tmp_path: Path,
) -> None:
    outputs = tmp_path / "outputs"
    source = _write_source(outputs)
    rows = list(csv.DictReader(source["matrix_path"].open(encoding="utf-8")))
    rows[0]["eligibility"] = "not_eligible"
    with source["matrix_path"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    report = _validate(outputs, source)
    statuses = _statuses(report)
    assert statuses["eligibility_counts_consistent"] == "fail"
    assert statuses["unsupported_records_excluded"] == "fail"
    assert report.output_validation_status == "not_ready_inconsistent_outputs"


def test_eligible_yaml_safety_and_next_action_checks(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    source = _write_source(outputs)
    source["eligible_path"].write_text(
        yaml.safe_dump({"tickers": CORE}),
        encoding="utf-8",
    )
    payload = json.loads(source["report_path"].read_text(encoding="utf-8"))
    payload["safety_notice"] = ""
    payload["next_research_action"] = "wait"
    source["report_path"].write_text(json.dumps(payload), encoding="utf-8")

    report = _validate(outputs, source)
    statuses = _statuses(report)
    assert statuses["eligible_universe_matches_report"] == "fail"
    assert statuses["safety_notice_present"] == "fail"
    assert statuses["next_action_ready"] == "fail"


def test_writer_markdown_csv_and_latest_manifest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    source = _write_source(outputs)
    files = write_expanded_ticker_coverage_output_validation_report(
        outputs_root=outputs,
        validation_run_id="20260101_000000",
        latest_manifest={
            **source["latest"],
            "_manifest_path": str(source["latest_path"]),
        },
        generated_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
    )
    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert payload["checks"]
    assert payload["readiness_for_expanded_trial"] is True
    markdown = render_expanded_ticker_coverage_output_validation_report(
        files.report
    )
    for heading in (
        "Validation Checks",
        "Eligible Universe Review",
        "Coverage Consistency",
        "Readiness for Expanded Trial",
        "Safety Notice",
    ):
        assert heading in markdown


def test_cli_explicit_and_auto_latest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_source(outputs)
    runner = CliRunner()
    explicit = runner.invoke(
        app,
        [
            "validate-expanded-ticker-coverage-output",
            "--validation-run-id",
            "20260101_000000",
            "--outputs-root",
            str(outputs),
        ],
    )
    assert explicit.exit_code == 0, explicit.output
    assert "Expanded Ticker Coverage Output Validation" in explicit.output
    assert "ready_with_warnings" in explicit.output

    latest = runner.invoke(
        app,
        [
            "validate-expanded-ticker-coverage-output",
            "--auto-latest",
            "--outputs-root",
            str(outputs),
        ],
    )
    assert latest.exit_code == 0, latest.output
    assert "20260101_000000" in latest.output
