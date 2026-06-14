"""Tests for delayed-anchor readiness impact diagnostics."""

import json
from pathlib import Path

from broker_agents.backtesting.delayed_anchor_impact_report import (
    build_delayed_anchor_impact_diagnostics,
    build_delayed_anchor_impact_report,
    compare_delayed_vs_non_delayed,
    render_delayed_anchor_impact_report,
    write_delayed_anchor_impact_report,
)


def _row(
    ticker: str,
    signal_date: str,
    *,
    delayed: bool,
    limited: bool,
    guardrail: str,
    forward_12m: float,
    relative_12m: float,
) -> dict:
    return {
        "ticker": ticker,
        "signal_date": signal_date,
        "data_status": "complete_local_csv",
        "has_delayed_price_anchor": delayed,
        "has_limited_financials": limited,
        "coverage_guardrail_status": guardrail,
        "forward_return_3m": 0.02,
        "forward_return_6m": 0.06,
        "forward_return_12m": forward_12m,
        "relative_return_12m": relative_12m,
        "max_drawdown_12m": -0.15,
    }


def _impact_rows() -> list[dict]:
    rows = []
    for index in range(6):
        rows.append(
            _row(
                f"N{index}",
                f"2022-0{index + 1}-30",
                delayed=False,
                limited=True,
                guardrail="research_usable_with_warnings",
                forward_12m=0.20,
                relative_12m=0.08,
            )
        )
    for index in range(5):
        rows.append(
            _row(
                f"D{index}",
                f"2021-0{index + 1}-30",
                delayed=True,
                limited=True,
                guardrail="warning_heavy",
                forward_12m=0.45,
                relative_12m=0.18,
            )
        )
    return rows


def test_anchor_builder_creates_all_required_subsets() -> None:
    diagnostics = build_delayed_anchor_impact_diagnostics(_impact_rows())

    assert set(diagnostics) == {
        "all_records",
        "delayed_anchor",
        "no_delayed_anchor",
        "delayed_anchor_and_warning_heavy",
        "no_delayed_anchor_but_limited_financials",
    }
    assert diagnostics["all_records"]["sample_size"] == 11
    assert diagnostics["delayed_anchor"]["sample_size"] == 5
    assert diagnostics["no_delayed_anchor"]["sample_size"] == 6
    assert diagnostics["delayed_anchor_and_warning_heavy"][
        "sample_size"
    ] == 5
    assert diagnostics["no_delayed_anchor_but_limited_financials"][
        "sample_size"
    ] == 6
    assert diagnostics["delayed_anchor"]["evaluated_dates"]


def test_empty_anchor_subset_has_no_fabricated_metrics() -> None:
    diagnostics = build_delayed_anchor_impact_diagnostics(
        [_impact_rows()[0]]
    )
    delayed = diagnostics["delayed_anchor"]

    assert delayed["available"] is False
    assert delayed["sample_size"] == 0
    assert delayed["median_forward_return_12m"] is None
    assert delayed["small_sample_warning"] is True


def test_impact_assessment_detects_stronger_delayed_and_positive_non_delayed(
) -> None:
    diagnostics = build_delayed_anchor_impact_diagnostics(_impact_rows())
    assessment = compare_delayed_vs_non_delayed(diagnostics)

    assert assessment["delayed_anchor_present"] is True
    assert assessment["no_delayed_anchor_positive"] is True
    assert assessment["delayed_anchor_materially_stronger"] is True
    assert assessment["relative_median_gap_12m"] == 0.1
    assert assessment["impact_status"] == (
        "delayed_anchor_may_be_lifting_results"
    )
    assert "non-delayed-anchor records remain positive" in assessment[
        "interpretation"
    ]


def test_small_anchor_subset_keeps_status_conservative() -> None:
    rows = _impact_rows()[:6] + [_impact_rows()[-1]]
    report = build_delayed_anchor_impact_report(
        manifest={
            "backtest_run_id": "small-anchor",
            "backtest_run_type": "readiness_trial",
            "clean_only_available": False,
        },
        rows=rows,
    )

    assert report.subset_diagnostics["delayed_anchor"][
        "small_sample_warning"
    ] is True
    assert report.impact_status == "insufficient_sample"


def test_delayed_anchor_report_writes_required_artifacts(
    tmp_path: Path,
) -> None:
    files = write_delayed_anchor_impact_report(
        output_dir=tmp_path,
        manifest={
            "backtest_run_id": "anchor-run",
            "backtest_run_type": "readiness_trial",
            "clean_only_available": False,
        },
        rows=_impact_rows(),
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert "impact_assessment" in payload
    assert payload["impact_status"] == (
        "delayed_anchor_may_be_lifting_results"
    )
    markdown = render_delayed_anchor_impact_report(files.report)
    for heading in (
        "Delayed Anchor Impact Report",
        "Delayed vs Non-Delayed Impact Assessment",
        "Non-Delayed Anchor Evidence",
        "Delayed Anchor Caution",
        "What This Suggests",
        "What This Does Not Suggest",
        "Safety Notice",
    ):
        assert heading in markdown
    assert "do not simulate exact historical execution" in markdown
    assert (
        "not a recommendation, ranking, vote, average score, consensus"
        in markdown
    )
