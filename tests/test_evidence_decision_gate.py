"""Tests for the clean-versus-warning research evidence gate."""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.backtesting.evidence_decision_gate import (
    build_evidence_decision_gate,
    find_latest_evidence_gate_backtest,
    load_evidence_gate_inputs,
    render_evidence_decision_gate_report,
    write_evidence_decision_gate_report,
)
from broker_agents.cli import app


def _summary(**overrides: object) -> dict:
    summary = {
        "backtest_run_id": "run-1",
        "manifest_path": "backtest_manifest.json",
        "source_reports": {},
        "missing_inputs": [],
        "sample_size": 20,
        "ticker_count": 4,
        "tickers": ["AAPL", "COST", "MSFT", "NVDA"],
        "concentration_warning": True,
        "clean_record_count": 12,
        "warning_record_count": 8,
        "warning_heavy_record_count": 0,
        "limited_financials_record_count": 0,
        "clean_only_available": True,
        "clean_coverage_sensitivity_status": "clean_supported_preliminary",
        "clean_median_relative_return_12m": 0.1263,
        "clean_hit_rate_vs_benchmark_12m": 0.75,
        "delayed_anchor_impact_status": (
            "delayed_anchor_may_be_lifting_results"
        ),
        "delayed_anchor_materially_stronger": True,
        "no_delayed_anchor_positive": True,
        "outlier_dependence_status": (
            "nvda_lifts_average_but_result_survives"
        ),
        "ex_nvda_positive": True,
        "ex_top_2_positive": True,
        "statistical_validity": "limited_sample",
        "decision_status": "needs_more_samples",
        "diagnostic_status": "promising_but_unproven",
        "comparison_status": "clean_coverage_improved",
    }
    summary.update(overrides)
    return summary


def _build(**overrides: object):
    return build_evidence_decision_gate(
        gate_run_id="gate-1",
        generated_at="2026-06-15T00:00:00+00:00",
        evidence_summary=_summary(**overrides),
    )


def _statuses(report) -> dict:
    return {
        item["criterion"]: item["status"]
        for item in report.criteria_results
    }


def _write_run(outputs_root: Path, run_id: str) -> None:
    folder = outputs_root / "backtests" / run_id
    folder.mkdir(parents=True)
    clean_path = folder / "clean_coverage_sensitivity_report.json"
    delayed_path = folder / "delayed_anchor_impact_report.json"
    outlier_path = folder / "outlier_sensitivity_report.json"
    decision_path = folder / "readiness_trial_decision_report.json"
    diagnostic_path = folder / "readiness_trial_diagnostic_report.json"
    clean_path.write_text(
        json.dumps(
            {
                "sensitivity_status": "clean_supported_preliminary",
                "subset_diagnostics": {
                    "clean_records": {
                        "available": True,
                        "sample_size": 12,
                        "median_relative_return_12m": 0.1263,
                        "hit_rate_vs_benchmark_12m": 0.75,
                    },
                    "limited_financials": {
                        "available": False,
                        "sample_size": 0,
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    delayed_path.write_text(
        json.dumps(
            {
                "impact_assessment": {
                    "impact_status": (
                        "delayed_anchor_may_be_lifting_results"
                    ),
                    "delayed_anchor_materially_stronger": True,
                    "no_delayed_anchor_positive": True,
                }
            }
        ),
        encoding="utf-8",
    )
    outlier_path.write_text(
        json.dumps(
            {
                "outlier_impact_assessment": {
                    "outlier_dependence_status": (
                        "nvda_lifts_average_but_result_survives"
                    ),
                    "ex_nvda_positive": True,
                    "ex_top_2_positive": True,
                }
            }
        ),
        encoding="utf-8",
    )
    decision_path.write_text(
        json.dumps(
            {
                "sample_size": 20,
                "tickers_evaluated": ["AAPL", "COST", "MSFT", "NVDA"],
                "concentration_warning": True,
                "statistical_validity": "limited_sample",
                "decision_status": "needs_more_samples",
            }
        ),
        encoding="utf-8",
    )
    diagnostic_path.write_text(
        json.dumps(
            {
                "evaluated_tickers": ["AAPL", "COST", "MSFT", "NVDA"],
                "diagnostic_status": "promising_but_unproven",
            }
        ),
        encoding="utf-8",
    )
    (folder / "backtest_manifest.json").write_text(
        json.dumps(
            {
                "backtest_run_id": run_id,
                "backtest_run_type": "readiness_trial",
                "status": "completed",
                "overall_sample_size": 20,
                "clean_record_count": 12,
                "warning_record_count": 8,
                "warning_heavy_record_count": 0,
                "clean_only_available": True,
                "clean_coverage_sensitivity_status": (
                    "clean_supported_preliminary"
                ),
                "clean_coverage_sensitivity_report_json_path": str(
                    clean_path
                ),
                "delayed_anchor_impact_report_json_path": str(delayed_path),
                "outlier_sensitivity_report_json_path": str(outlier_path),
                "readiness_trial_decision_report_json_path": str(
                    decision_path
                ),
                "readiness_trial_diagnostic_report_json_path": str(
                    diagnostic_path
                ),
            }
        ),
        encoding="utf-8",
    )


def test_expected_profile_is_ready_with_warn_only_cautions() -> None:
    report = _build()
    statuses = _statuses(report)

    assert report.gate_outcome == "research_ready_for_broader_trial"
    assert report.gate_status == "pass_with_warnings"
    assert report.block_count == 0
    assert statuses["clean_evidence_available"] == "pass"
    assert statuses["clean_evidence_positive"] == "pass"
    assert statuses["warning_heavy_controlled"] == "pass"
    assert statuses["limited_financials_controlled"] == "pass"
    assert statuses["delayed_anchor_not_blocking"] == "warn"
    assert statuses["outlier_not_blocking"] == "warn"
    assert statuses["sample_size_limited"] == "warn"
    assert statuses["concentration_limited"] == "warn"
    assert statuses["decision_conservatism_preserved"] == "pass"
    assert statuses["diagnostic_promising"] == "pass"
    assert (
        report.next_research_action
        == "expand_ticker_universe_with_coverage_validation"
    )


@pytest.mark.parametrize(
    ("overrides", "outcome", "criterion"),
    [
        (
            {
                "clean_record_count": 0,
                "clean_only_available": False,
                "clean_coverage_sensitivity_status": "clean_not_available",
                "clean_median_relative_return_12m": None,
                "clean_hit_rate_vs_benchmark_12m": None,
            },
            "blocked_by_clean_evidence_absence",
            "clean_evidence_available",
        ),
        (
            {"warning_heavy_record_count": 10},
            "blocked_by_warning_heavy_evidence",
            "warning_heavy_controlled",
        ),
        (
            {"no_delayed_anchor_positive": False},
            "blocked_by_delayed_anchor_dependency",
            "delayed_anchor_not_blocking",
        ),
        (
            {"ex_nvda_positive": False},
            "blocked_by_outlier_dependency",
            "outlier_not_blocking",
        ),
        (
            {"sample_size": 4},
            "insufficient_sample_for_gate",
            "sample_size_limited",
        ),
    ],
)
def test_gate_blocking_precedence(
    overrides: dict,
    outcome: str,
    criterion: str,
) -> None:
    report = _build(**overrides)
    assert report.gate_outcome == outcome
    assert _statuses(report)[criterion] == "block"


def test_clean_positive_and_warning_thresholds_are_conservative() -> None:
    clean_weak = _build(
        clean_median_relative_return_12m=-0.01,
        clean_hit_rate_vs_benchmark_12m=0.4,
    )
    assert clean_weak.gate_outcome == "continue_data_quality_repair"
    assert _statuses(clean_weak)["clean_evidence_positive"] == "block"

    warning_present = _build(warning_heavy_record_count=4)
    assert _statuses(warning_present)["warning_heavy_controlled"] == "warn"
    assert warning_present.gate_outcome == "research_ready_for_broader_trial"


def test_missing_source_report_is_handled_as_insufficient_input(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    _write_run(outputs_root, "20260101_000000")
    manifest_path = (
        outputs_root
        / "backtests"
        / "20260101_000000"
        / "backtest_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    Path(
        manifest["clean_coverage_sensitivity_report_json_path"]
    ).unlink()

    summary = load_evidence_gate_inputs(
        outputs_root=outputs_root,
        backtest_run_id="20260101_000000",
    )
    assert summary["missing_inputs"] == ["clean_coverage"]
    report = build_evidence_decision_gate(
        gate_run_id="gate",
        generated_at="2026-06-15T00:00:00+00:00",
        evidence_summary=summary,
    )
    assert report.gate_outcome == "insufficient_inputs"


def test_writer_report_csv_and_explicit_cli(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    _write_run(outputs_root, "20260101_000000")
    files = write_evidence_decision_gate_report(
        outputs_root=outputs_root,
        backtest_run_id="20260101_000000",
        generated_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
    )
    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.criteria_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert payload["gate_outcome"] == "research_ready_for_broader_trial"
    assert payload["criteria_results"]
    markdown = files.markdown_path.read_text(encoding="utf-8")
    for heading in (
        "Gate Criteria",
        "Blockers",
        "Warnings",
        "Required Next Research Action",
        "What This Suggests",
        "What This Does Not Suggest",
        "Safety Notice",
    ):
        assert heading in markdown
    with files.criteria_csv_path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert any(
        row["criterion"] == "clean_evidence_available" for row in rows
    )

    result = CliRunner().invoke(
        app,
        [
            "run-evidence-decision-gate",
            "--backtest-run-id",
            "20260101_000000",
            "--outputs-root",
            str(outputs_root),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Evidence Decision Gate" in result.output
    assert "research_ready_for_broader_trial" in result.output


def test_auto_latest_cli_and_manifest_loading(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    _write_run(outputs_root, "20260101_000000")
    _write_run(outputs_root, "20260102_000000")
    assert (
        find_latest_evidence_gate_backtest(outputs_root)
        == "20260102_000000"
    )
    loaded = load_evidence_gate_inputs(
        outputs_root=outputs_root,
        backtest_run_id="20260102_000000",
    )
    assert loaded["clean_record_count"] == 12
    assert loaded["ticker_count"] == 4

    result = CliRunner().invoke(
        app,
        [
            "run-evidence-decision-gate",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "20260102_000000" in result.output


def test_render_exposes_no_hard_blockers_for_expected_profile() -> None:
    markdown = render_evidence_decision_gate_report(_build())
    assert "No hard blockers detected for broader research expansion." in markdown
    assert "This is permission to expand the research sample only." in markdown
