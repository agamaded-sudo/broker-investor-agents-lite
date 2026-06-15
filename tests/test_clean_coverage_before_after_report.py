"""Tests for clean coverage before/after audit reports."""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.backtesting.clean_coverage_before_after_report import (
    build_clean_coverage_comparison_report,
    find_latest_clean_coverage_runs,
    load_clean_coverage_run_summary,
    render_clean_coverage_comparison_report,
    write_clean_coverage_comparison_report,
)
from broker_agents.cli import app


def _summary(*, clean: int, heavy: int, median: float = 0.3) -> dict:
    available = clean > 0
    return {
        "backtest_run_id": f"run-{clean}-{heavy}",
        "manifest_path": "manifest.json",
        "sample_size": 20,
        "diagnostic_status": "promising_but_unproven",
        "decision_status": "needs_more_samples",
        "statistical_validity": "limited_sample",
        "walk_forward_stability_judgment": "stable_positive",
        "clean_record_count": clean,
        "warning_record_count": 20 - clean,
        "warning_heavy_record_count": heavy,
        "limited_financials_record_count": 20 if not clean else 0,
        "clean_coverage_sensitivity_status": (
            "clean_supported_preliminary" if clean else "clean_not_available"
        ),
        "clean_only_available": available,
        "delayed_anchor_record_count": 8,
        "no_delayed_anchor_record_count": 12,
        "delayed_anchor_impact_status": (
            "delayed_anchor_may_be_lifting_results"
        ),
        "outlier_dependence_status": (
            "nvda_lifts_average_but_result_survives"
        ),
        "nvda_record_count": 5,
        "ex_nvda_positive": True,
        "ex_top_2_positive": True,
        "median_forward_return_12m": median,
        "average_forward_return_12m": 0.55,
        "median_relative_return_12m": 0.12,
        "hit_rate_vs_benchmark_12m": 0.75,
        "worst_max_drawdown_12m": -0.45,
        "clean_subset": {
            "available": available,
            "sample_size": clean,
            "median_forward_return_12m": 0.26 if available else None,
            "median_relative_return_12m": 0.12 if available else None,
            "hit_rate_vs_benchmark_12m": 0.75 if available else None,
            "worst_max_drawdown_12m": -0.4 if available else None,
        },
    }


def _write_run(
    outputs_root: Path,
    run_id: str,
    *,
    clean: int,
    heavy: int,
) -> None:
    folder = outputs_root / "backtests" / run_id
    folder.mkdir(parents=True)
    metrics_path = folder / "backtest_metrics_summary.json"
    sensitivity_path = folder / "clean_coverage_sensitivity_report.json"
    metrics_path.write_text(
        json.dumps(
            {
                "sample_size": 20,
                "median_forward_return_12m": 0.3,
                "average_forward_return_12m": 0.55,
                "median_relative_return_12m": 0.12,
                "hit_rate_vs_benchmark_12m": 0.75,
                "worst_max_drawdown_12m": -0.45,
                "coverage_quality_counts": (
                    {"limited_financials": 20}
                    if clean == 0
                    else {"clean": clean, "delayed_price_anchor": 20 - clean}
                ),
            }
        ),
        encoding="utf-8",
    )
    sensitivity_path.write_text(
        json.dumps(
            {
                "subset_diagnostics": {
                    "clean_records": _summary(
                        clean=clean,
                        heavy=heavy,
                    )["clean_subset"]
                }
            }
        ),
        encoding="utf-8",
    )
    (folder / "backtest_manifest.json").write_text(
        json.dumps(
            {
                "backtest_run_id": run_id,
                "backtest_run_type": "readiness_trial",
                "overall_sample_size": 20,
                "metrics_summary_path": str(metrics_path),
                "clean_coverage_sensitivity_report_json_path": str(
                    sensitivity_path
                ),
                "clean_record_count": clean,
                "warning_record_count": 20 - clean,
                "warning_heavy_record_count": heavy,
                "clean_coverage_sensitivity_status": (
                    "clean_supported_preliminary"
                    if clean
                    else "clean_not_available"
                ),
                "clean_only_available": clean > 0,
                "diagnostic_status": "promising_but_unproven",
                "decision_status": "needs_more_samples",
                "statistical_validity": "limited_sample",
                "walk_forward_stability_judgment": "stable_positive",
                "delayed_anchor_record_count": 8,
                "no_delayed_anchor_record_count": 12,
                "delayed_anchor_impact_status": (
                    "delayed_anchor_may_be_lifting_results"
                ),
                "outlier_dependence_status": (
                    "nvda_lifts_average_but_result_survives"
                ),
                "nvda_record_count": 5,
                "ex_nvda_positive": True,
                "ex_top_2_positive": True,
            }
        ),
        encoding="utf-8",
    )


def test_comparison_detects_improvement_and_required_deltas() -> None:
    report = build_clean_coverage_comparison_report(
        comparison_run_id="compare",
        generated_at="2026-06-15T00:00:00+00:00",
        before_summary=_summary(clean=0, heavy=8),
        after_summary=_summary(clean=12, heavy=0),
    )

    assert report.comparison_status == "clean_coverage_improved"
    assert report.comparison_deltas["clean_records_delta"] == 12
    assert report.comparison_deltas["warning_heavy_records_delta"] == -8
    assert report.comparison_deltas["median_12m_delta"] == 0
    assert report.comparison_deltas["limited_financials_removed"] is True
    assert report.comparison_deltas["decision_status_changed"] is False
    markdown = render_clean_coverage_comparison_report(report)
    for heading in (
        "Coverage Quality Comparison",
        "Diagnostic Result Comparison",
        "Clean Subset Comparison",
        "Delayed Anchor and Outlier Context",
        "What This Suggests",
        "What This Does Not Suggest",
        "Safety Notice",
    ):
        assert heading in markdown


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        (_summary(clean=5, heavy=2), _summary(clean=5, heavy=2),
         "clean_coverage_unchanged"),
        (_summary(clean=12, heavy=0), _summary(clean=4, heavy=5),
         "clean_coverage_regressed"),
    ],
)
def test_comparison_detects_unchanged_and_regression(
    before: dict,
    after: dict,
    expected: str,
) -> None:
    report = build_clean_coverage_comparison_report(
        comparison_run_id="compare",
        generated_at="2026-06-15T00:00:00+00:00",
        before_summary=before,
        after_summary=after,
    )
    assert report.comparison_status == expected


@pytest.mark.parametrize(
    ("before", "after"),
    [(None, _summary(clean=12, heavy=0)), (_summary(clean=0, heavy=8), None)],
)
def test_comparison_handles_missing_inputs(
    before: dict | None,
    after: dict | None,
) -> None:
    report = build_clean_coverage_comparison_report(
        comparison_run_id="missing",
        generated_at="2026-06-15T00:00:00+00:00",
        before_summary=before,
        after_summary=after,
    )
    assert report.comparison_status == "insufficient_comparison_inputs"


def test_loader_writer_and_explicit_cli(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    _write_run(outputs_root, "20260101_000000", clean=0, heavy=8)
    _write_run(outputs_root, "20260102_000000", clean=12, heavy=0)

    loaded = load_clean_coverage_run_summary(
        outputs_root=outputs_root,
        run_id="20260102_000000",
    )
    assert loaded["clean_record_count"] == 12
    assert loaded["clean_subset"]["available"] is True

    files = write_clean_coverage_comparison_report(
        outputs_root=outputs_root,
        before_run_id="20260101_000000",
        after_run_id="20260102_000000",
        generated_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
    )
    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.summary_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert "before_summary" in payload
    assert "after_summary" in payload
    assert "comparison_deltas" in payload
    with files.summary_csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert any(row["metric"] == "clean_record_count" for row in rows)

    result = CliRunner().invoke(
        app,
        [
            "compare-clean-coverage-runs",
            "--before-run-id",
            "20260101_000000",
            "--after-run-id",
            "20260102_000000",
            "--outputs-root",
            str(outputs_root),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Clean Coverage Before/After Comparison" in result.output
    assert "clean_coverage_improved" in result.output


def test_auto_latest_and_missing_manifest_error(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    _write_run(outputs_root, "20260101_000000", clean=0, heavy=8)
    _write_run(outputs_root, "20260102_000000", clean=12, heavy=0)
    assert find_latest_clean_coverage_runs(outputs_root) == (
        "20260101_000000",
        "20260102_000000",
    )

    result = CliRunner().invoke(
        app,
        [
            "compare-clean-coverage-runs",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "20260101_000000" in result.output
    assert "20260102_000000" in result.output

    with pytest.raises(FileNotFoundError, match="Backtest manifest not found"):
        load_clean_coverage_run_summary(
            outputs_root=outputs_root,
            run_id="missing",
        )
