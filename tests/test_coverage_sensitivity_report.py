"""Tests for clean-coverage readiness sensitivity diagnostics."""

import json
from pathlib import Path

from broker_agents.backtesting.coverage_sensitivity_report import (
    build_clean_coverage_sensitivity_report,
    build_coverage_sensitivity_diagnostics,
    render_clean_coverage_sensitivity_report,
    write_clean_coverage_sensitivity_report,
)


def _row(
    ticker: str,
    *,
    guardrail: str,
    quality: str,
    delayed: bool,
    limited: bool,
    return_12m: float,
) -> dict:
    return {
        "ticker": ticker,
        "data_status": "complete_local_csv",
        "coverage_guardrail_status": guardrail,
        "coverage_quality_label": quality,
        "has_delayed_price_anchor": delayed,
        "has_limited_financials": limited,
        "forward_return_3m": 0.02,
        "forward_return_6m": 0.06,
        "forward_return_12m": return_12m,
        "relative_return_12m": return_12m - 0.10,
        "max_drawdown_12m": -0.15,
    }


def test_sensitivity_builder_creates_every_quality_subset() -> None:
    rows = [
        _row(
            "MSFT",
            guardrail="clean",
            quality="clean",
            delayed=False,
            limited=False,
            return_12m=0.20,
        ),
        _row(
            "AAPL",
            guardrail="research_usable_with_warnings",
            quality="limited_financials",
            delayed=False,
            limited=True,
            return_12m=0.25,
        ),
        _row(
            "NVDA",
            guardrail="warning_heavy",
            quality="delayed_anchor_and_limited_financials",
            delayed=True,
            limited=True,
            return_12m=0.60,
        ),
    ]

    diagnostics = build_coverage_sensitivity_diagnostics(rows)

    assert set(diagnostics) == {
        "all_records",
        "clean_records",
        "research_usable_with_warnings",
        "warning_heavy",
        "no_delayed_anchor",
        "delayed_anchor",
        "limited_financials",
        "non_warning_heavy",
    }
    assert diagnostics["all_records"]["sample_size"] == 3
    assert diagnostics["clean_records"]["sample_size"] == 1
    assert diagnostics["warning_heavy"]["sample_size"] == 1
    assert diagnostics["no_delayed_anchor"]["sample_size"] == 2
    assert diagnostics["delayed_anchor"]["sample_size"] == 1
    assert diagnostics["limited_financials"]["sample_size"] == 2
    assert diagnostics["non_warning_heavy"]["sample_size"] == 2
    assert diagnostics["clean_records"]["small_sample_warning"] is True


def test_zero_clean_subset_is_unavailable_without_metrics() -> None:
    rows = [
        _row(
            "COST",
            guardrail="research_usable_with_warnings",
            quality="limited_financials",
            delayed=False,
            limited=True,
            return_12m=0.30,
        )
    ]

    report = build_clean_coverage_sensitivity_report(
        manifest={
            "backtest_run_id": "sensitivity-run",
            "backtest_run_type": "readiness_trial",
        },
        rows=rows,
    )
    clean = report.subset_diagnostics["clean_records"]

    assert clean["available"] is False
    assert clean["sample_size"] == 0
    assert clean["median_forward_return_12m"] is None
    assert clean["small_sample_warning"] is True
    assert clean["interpretation"] == (
        "Clean-only sensitivity is not available yet."
    )
    assert report.sensitivity_status == "clean_not_available"
    assert report.next_research_action == (
        "add_clean_historical_fixture_coverage"
    )
    assert any(
        "warning-bearing records" in finding
        for finding in report.key_findings
    )


def test_sensitivity_report_writes_json_and_markdown(tmp_path: Path) -> None:
    rows = [
        _row(
            "MSFT",
            guardrail="research_usable_with_warnings",
            quality="limited_financials",
            delayed=False,
            limited=True,
            return_12m=0.25,
        ),
        _row(
            "NVDA",
            guardrail="warning_heavy",
            quality="delayed_anchor_and_limited_financials",
            delayed=True,
            limited=True,
            return_12m=0.65,
        ),
    ]
    manifest = {
        "backtest_run_id": "sensitivity-run",
        "backtest_run_type": "readiness_trial",
    }

    files = write_clean_coverage_sensitivity_report(
        output_dir=tmp_path,
        manifest=manifest,
        rows=rows,
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert "subset_diagnostics" in payload
    assert payload["sensitivity_status"] == "clean_not_available"
    markdown = files.markdown_path.read_text(encoding="utf-8")
    for heading in (
        "Clean-Coverage Sensitivity Report",
        "Clean-Only Sensitivity",
        "Warning-Heavy Sensitivity",
        "Delayed Anchor Sensitivity",
        "Limited Financials Sensitivity",
        "What This Suggests",
        "What This Does Not Suggest",
        "Safety Notice",
    ):
        assert heading in markdown
    assert "Clean-only sensitivity is not available yet." in markdown
    assert (
        "not a recommendation, ranking, vote, average score, consensus"
        in markdown
    )


def test_rendered_report_preserves_small_sample_warning() -> None:
    report = build_clean_coverage_sensitivity_report(
        manifest={
            "backtest_run_id": "small-run",
            "backtest_run_type": "readiness_trial",
        },
        rows=[
            _row(
                "MSFT",
                guardrail="clean",
                quality="clean",
                delayed=False,
                limited=False,
                return_12m=0.15,
            )
        ],
    )

    assert report.subset_diagnostics["clean_records"][
        "small_sample_warning"
    ] is True
    assert "small-sample limited" in render_clean_coverage_sensitivity_report(
        report
    )
