"""Tests for outlier and Ex-NVDA readiness sensitivity diagnostics."""

import json
from pathlib import Path

from broker_agents.backtesting.outlier_sensitivity_report import (
    build_outlier_sensitivity_diagnostics,
    build_outlier_sensitivity_report,
    compare_outlier_subsets,
    identify_top_outliers,
    render_outlier_sensitivity_report,
    write_outlier_sensitivity_report,
)


def _row(
    ticker: str,
    signal_date: str,
    forward_12m: float,
    relative_12m: float,
) -> dict:
    return {
        "ticker": ticker,
        "signal_date": signal_date,
        "data_status": "complete_local_csv",
        "forward_return_3m": 0.03,
        "forward_return_6m": 0.08,
        "forward_return_12m": forward_12m,
        "relative_return_12m": relative_12m,
        "max_drawdown_12m": -0.15,
    }


def _rows() -> list[dict]:
    return [
        _row("NVDA", "2021-06-30", 2.10, 1.90),
        _row("NVDA", "2022-06-30", 1.60, 1.35),
        _row("MSFT", "2021-06-30", 0.42, 0.18),
        _row("AAPL", "2021-06-30", 0.36, 0.14),
        _row("COST", "2021-06-30", 0.31, 0.12),
        _row("MSFT", "2022-06-30", 0.28, 0.10),
        _row("AAPL", "2022-06-30", 0.22, 0.08),
        _row("COST", "2022-06-30", 0.18, 0.06),
    ]


def test_outlier_builder_creates_all_requested_subsets() -> None:
    diagnostics = build_outlier_sensitivity_diagnostics(_rows())

    assert set(diagnostics) == {
        "all_records",
        "ex_nvda",
        "nvda_only",
        "ex_top_1_forward_12m",
        "ex_top_2_forward_12m",
        "ex_top_3_forward_12m",
        "capped_top_12m",
        "non_extreme_records",
    }
    assert diagnostics["all_records"]["sample_size"] == 8
    assert diagnostics["ex_nvda"]["sample_size"] == 6
    assert diagnostics["nvda_only"]["sample_size"] == 2
    assert diagnostics["ex_top_1_forward_12m"]["sample_size"] == 7
    assert diagnostics["ex_top_2_forward_12m"]["sample_size"] == 6
    assert diagnostics["ex_top_3_forward_12m"]["sample_size"] == 5
    assert diagnostics["non_extreme_records"]["sample_size"] == 6
    assert diagnostics["nvda_only"]["small_sample_warning"] is True


def test_empty_nvda_subset_has_no_fabricated_metrics() -> None:
    diagnostics = build_outlier_sensitivity_diagnostics(
        [row for row in _rows() if row["ticker"] != "NVDA"]
    )
    nvda = diagnostics["nvda_only"]

    assert nvda["available"] is False
    assert nvda["median_forward_return_12m"] is None
    assert nvda["average_relative_return_12m"] is None
    assert nvda["small_sample_warning"] is True


def test_top_outliers_are_sorted_descending() -> None:
    top = identify_top_outliers(_rows())

    assert [item["ticker"] for item in top[:2]] == ["NVDA", "NVDA"]
    assert [item["forward_return_12m"] for item in top] == [
        2.10,
        1.60,
        0.42,
    ]


def test_assessment_detects_nvda_lift_and_positive_exclusions() -> None:
    diagnostics = build_outlier_sensitivity_diagnostics(_rows())
    assessment = compare_outlier_subsets(
        diagnostics,
        identify_top_outliers(_rows()),
    )

    assert assessment["nvda_present"] is True
    assert assessment["nvda_record_count"] == 2
    assert assessment["nvda_share_of_total"] == 0.25
    assert assessment["ex_nvda_positive"] is True
    assert assessment["ex_top_1_positive"] is True
    assert assessment["ex_top_2_positive"] is True
    assert assessment["ex_top_3_positive"] is True
    assert assessment["average_materially_lifted_by_nvda"] is True
    assert assessment["outlier_dependence_status"] == (
        "nvda_lifts_average_but_result_survives"
    )


def test_small_sample_status_is_conservative() -> None:
    report = build_outlier_sensitivity_report(
        manifest={
            "backtest_run_id": "small",
            "backtest_run_type": "readiness_trial",
        },
        rows=_rows()[:4],
    )

    assert report.outlier_dependence_status == "insufficient_sample"


def test_outlier_report_writes_required_artifacts(tmp_path: Path) -> None:
    files = write_outlier_sensitivity_report(
        output_dir=tmp_path,
        manifest={
            "backtest_run_id": "outlier-run",
            "backtest_run_type": "readiness_trial",
        },
        rows=_rows(),
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert "outlier_impact_assessment" in payload
    assert payload["top_outliers"][0]["ticker"] == "NVDA"
    markdown = render_outlier_sensitivity_report(files.report)
    for heading in (
        "Outlier and Ex-NVDA Sensitivity Report",
        "Ex-NVDA Sensitivity",
        "Top-Outlier Exclusion Sensitivity",
        "Average vs Median Distortion",
        "What This Suggests",
        "What This Does Not Suggest",
        "Safety Notice",
    ):
        assert heading in markdown
    assert (
        "not a recommendation, ranking, vote, average score, consensus"
        in markdown
    )
