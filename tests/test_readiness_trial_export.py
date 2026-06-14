"""Tests for readiness-ledger export to research trial inputs."""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.backtesting.readiness_trial_export import (
    FORBIDDEN_COLUMNS,
    TRIAL_LEDGER_FIELDS,
    export_readiness_ledger_to_trial_ledger,
    validate_readiness_trial_ledger,
)
from broker_agents.cli import app

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
HISTORICAL_FINANCIALS = FIXTURES / "historical_financials"
PORTFOLIO_CONTEXT = EXAMPLES / "portfolio_context.yaml"


def _source_record(**overrides) -> dict:
    record = {
        "record_type": "historical_signal_readiness_candidate",
        "ticker": "COST",
        "as_of_date": "2023-06-30",
        "run_id": "trial_run",
        "run_folder": "outputs/COST/runs/trial_run",
        "candidate_file": "candidate.json",
        "assembly_file": "assembly.json",
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
        "warnings_count": "3",
        "coverage_quality_label": "limited_financials",
        "coverage_quality_severity": "moderate",
        "date_coverage_status": "usable_with_warnings",
        "has_delayed_price_anchor": "False",
        "has_limited_financials": "True",
        "warning_count": "2",
        "coverage_guardrail_status": "research_usable_with_warnings",
        "created_at": "2026-06-13T00:00:00+00:00",
        "source": "analyze_stock_historical_mode",
    }
    record.update(overrides)
    return record


def _write_source(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)


def test_converter_exports_safe_backtester_compatible_trial_rows(
    tmp_path: Path,
) -> None:
    source = tmp_path / "readiness.csv"
    output = tmp_path / "trial.csv"
    metadata = tmp_path / "trial_metadata.json"
    _write_source(source, [_source_record()])

    result = export_readiness_ledger_to_trial_ledger(
        source_ledger=source,
        output_ledger=output,
        metadata_file=metadata,
        generated_at=datetime(2026, 6, 13, tzinfo=timezone.utc),
    )

    assert result.total_input_records == 1
    assert result.total_exported_records == 1
    assert result.skipped_records == 0
    assert output.is_file()
    assert metadata.is_file()
    with output.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert tuple(reader.fieldnames or ()) == TRIAL_LEDGER_FIELDS
    assert len(rows) == 1
    row = rows[0]
    for field in (
        "ticker",
        "signal_date",
        "as_of_date",
        "record_type",
        "signal_generation_status",
        "safe_for_historical_signal_generation",
        "not_trade_signal",
        "not_recommendation",
        "not_allocation_instruction",
        "trial_backtest_label",
        "trial_backtest_allowed",
        "safety_notice",
        "coverage_quality_label",
        "coverage_quality_severity",
        "coverage_guardrail_status",
    ):
        assert field in row
    assert row["signal_date"] == row["as_of_date"] == "2023-06-30"
    assert row["generated_at"] == "2023-06-30T00:00:00+00:00"
    assert row["signal_generation_status"] == "readiness_only"
    assert row["safe_for_historical_signal_generation"] == "False"
    assert row["not_trade_signal"] == "True"
    assert row["not_recommendation"] == "True"
    assert row["not_allocation_instruction"] == "True"
    assert row["trial_backtest_label"] == "readiness_only_trial"
    assert row["trial_backtest_allowed"] == "True"
    assert row["coverage_quality_label"] == "limited_financials"
    assert row["coverage_quality_severity"] == "moderate"
    assert row["coverage_guardrail_status"] == (
        "research_usable_with_warnings"
    )
    assert FORBIDDEN_COLUMNS.isdisjoint(reader.fieldnames or ())

    payload = json.loads(metadata.read_text(encoding="utf-8"))
    assert payload["source_ledger"] == str(source)
    assert payload["output_ledger"] == str(output)
    assert payload["total_input_records"] == 1
    assert payload["total_exported_records"] == 1
    assert payload["skipped_records"] == 0
    assert payload["unsupported_dates_excluded_count"] == 0
    assert "readiness-only research artifacts" in payload["safety_notice"]


def test_converter_skips_invalid_source_records(tmp_path: Path) -> None:
    source = tmp_path / "readiness.csv"
    output = tmp_path / "trial.csv"
    _write_source(
        source,
        [
            _source_record(),
            _source_record(
                ticker="INVALID",
                not_trade_signal="False",
            ),
        ],
    )

    result = export_readiness_ledger_to_trial_ledger(
        source_ledger=source,
        output_ledger=output,
    )

    assert result.total_input_records == 2
    assert result.total_exported_records == 1
    assert result.skipped_records == 1
    assert result.warnings


def test_converter_excludes_explicitly_unsupported_coverage(
    tmp_path: Path,
) -> None:
    source = tmp_path / "readiness.csv"
    output = tmp_path / "trial.csv"
    _write_source(
        source,
        [
            _source_record(),
            _source_record(
                ticker="AAPL",
                coverage_quality_label="unsupported",
                coverage_quality_severity="unsupported",
                coverage_guardrail_status="unsupported_excluded",
            ),
        ],
    )

    result = export_readiness_ledger_to_trial_ledger(
        source_ledger=source,
        output_ledger=output,
    )

    assert result.total_exported_records == 1
    assert result.skipped_records == 1
    assert any("unsupported coverage" in item for item in result.warnings)


def test_validator_flags_weakened_safety_and_forbidden_columns(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / "invalid.csv"
    fieldnames = [*TRIAL_LEDGER_FIELDS, "action"]
    row = {
        field: ""
        for field in fieldnames
    }
    row.update(
        {
            "ticker": "COST",
            "signal_date": "2023-06-30",
            "as_of_date": "2023-06-30",
            "record_type": "historical_signal_readiness_candidate",
            "signal_generation_status": "readiness_only",
            "safe_for_historical_signal_generation": "False",
            "not_trade_signal": "False",
            "not_recommendation": "True",
            "not_allocation_instruction": "True",
            "trial_backtest_allowed": "True",
            "action": "invalid",
        }
    )
    with ledger.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)

    result = validate_readiness_trial_ledger(ledger)

    assert result.rows == 1
    assert result.invalid_rows == 1
    assert result.status == "invalid"
    assert result.warnings


def test_export_and_validation_cli_commands(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    historical = CliRunner().invoke(
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
            "--as-of-date",
            "2023-06-30",
            "--financials-provider",
            "historical_csv",
            "--financials-root",
            str(HISTORICAL_FINANCIALS),
        ],
    )
    assert historical.exit_code == 0, historical.output
    trial = tmp_path / "inputs" / "trial.csv"
    metadata = tmp_path / "inputs" / "trial_metadata.json"

    exported = CliRunner().invoke(
        app,
        [
            "export-readiness-trial-ledger",
            "--outputs-root",
            str(outputs_root),
            "--output-ledger",
            str(trial),
            "--metadata-file",
            str(metadata),
        ],
    )
    validated = CliRunner().invoke(
        app,
        [
            "validate-readiness-trial-ledger",
            "--ledger",
            str(trial),
        ],
    )

    assert exported.exit_code == 0, exported.output
    for text in (
        "source_ledger=",
        f"output_ledger={trial}",
        "total_exported_records=1",
        "status=completed",
    ):
        assert text in exported.output
    assert validated.exit_code == 0, validated.output
    for text in (
        "rows=1",
        "readiness_only_rows=1",
        "not_trade_signal_rows=1",
        "not_recommendation_rows=1",
        "invalid_rows=0",
        "status=valid",
    ):
        assert text in validated.output


def test_validation_cli_exits_nonzero_for_invalid_rows(tmp_path: Path) -> None:
    ledger = tmp_path / "invalid.csv"
    _write_source(
        ledger,
        [_source_record(not_recommendation="False")],
    )

    result = CliRunner().invoke(
        app,
        ["validate-readiness-trial-ledger", "--ledger", str(ledger)],
    )

    assert result.exit_code != 0
    assert "invalid_rows=1" in result.output
    assert "status=invalid" in result.output


def test_task84_documentation_demo_and_offline_scope() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for text in (
        "readiness ledger to trial backtest input export",
        "export-readiness-trial-ledger",
        "validate-readiness-trial-ledger",
        "signal_date",
        "this task prepares",
        "does not run a backtest",
    ):
        assert text in readme

    demo = (ROOT / "scripts" / "run_first_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "python -m ruff check ." in demo
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in demo
    assert "python -m broker_agents.cli" in demo

    source = (
        ROOT
        / "src"
        / "broker_agents"
        / "backtesting"
        / "readiness_trial_export.py"
    ).read_text(encoding="utf-8").lower()
    for network_call in (
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "urlopen(",
    ):
        assert network_call not in source
