"""Tests for BO-003 walk-forward stability repair plan."""

from datetime import datetime, timezone
import csv
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.backtesting.walk_forward_repair_plan import (
    analyze_period_breaks,
    build_walk_forward_repair_plan,
    build_walk_forward_retest_plan,
    load_outlier_repair_manifest,
    write_walk_forward_repair_plan_report,
)
from broker_agents.cli import app


DATES = [
    "2021-06-30",
    "2021-12-31",
    "2022-06-30",
    "2022-12-31",
    "2023-06-30",
]


def _rows() -> list[dict]:
    specs = [
        ("NVDA", "current_core", "Technology", "semiconductor", 0.20),
        ("AAPL", "current_core", "Technology", "consumer_platform", 0.12),
        ("MSFT", "current_core", "Technology", "software_platform", 0.10),
        ("COST", "current_core", "Consumer Staples", "retail", 0.08),
        ("NFLX", "expanded_cohort", "Communication Services", "consumer_platform", -0.22),
        ("ADBE", "expanded_cohort", "Technology", "software_platform", -0.12),
        ("CRM", "expanded_cohort", "Technology", "software_platform", -0.10),
        ("AMZN", "expanded_cohort", "Consumer Discretionary", "consumer_platform", -0.08),
    ]
    effects = {
        "2021-06-30": 0.12,
        "2021-12-31": -0.12,
        "2022-06-30": -0.06,
        "2022-12-31": -0.07,
        "2023-06-30": -0.08,
    }
    rows = []
    for ticker, group, sector, category, base_relative in specs:
        for date in DATES:
            warning_period = date in {"2021-12-31", "2022-12-31"}
            rows.append(
                {
                    "ticker": ticker,
                    "signal_date": date,
                    "coverage_guardrail_status": (
                        "research_usable_with_warnings"
                        if warning_period
                        else "clean"
                    ),
                    "coverage_quality_label": (
                        "delayed_price_anchor" if warning_period else "clean"
                    ),
                    "forward_return_12m": "0.10",
                    "relative_return_12m": str(base_relative + effects[date]),
                    "max_drawdown_12m": "-0.20",
                    "universe_group": group,
                    "sector": sector,
                    "category": category,
                }
            )
    return rows


def _analysis() -> dict:
    return {
        "analysis_run_id": "analysis",
        "ticker_attribution": [
            {
                "ticker": ticker,
                "sector": sector,
                "category": category,
                "universe_group": group,
            }
            for ticker, group, sector, category in [
                ("NVDA", "current_core", "Technology", "semiconductor"),
                ("AAPL", "current_core", "Technology", "consumer_platform"),
                ("MSFT", "current_core", "Technology", "software_platform"),
                ("COST", "current_core", "Consumer Staples", "retail"),
                (
                    "NFLX",
                    "expanded_cohort",
                    "Communication Services",
                    "consumer_platform",
                ),
                ("ADBE", "expanded_cohort", "Technology", "software_platform"),
                ("CRM", "expanded_cohort", "Technology", "software_platform"),
                (
                    "AMZN",
                    "expanded_cohort",
                    "Consumer Discretionary",
                    "consumer_platform",
                ),
            ]
        ],
    }


def _decomposition() -> dict:
    return {
        "decomposition_run_id": "decomp",
        "date_drivers": [
            {"as_of_date": "2021-06-30", "period_label": "supportive_period"},
            {"as_of_date": "2021-12-31", "period_label": "negative_period"},
            {"as_of_date": "2022-06-30", "period_label": "negative_period"},
            {"as_of_date": "2022-12-31", "period_label": "negative_period"},
            {"as_of_date": "2023-06-30", "period_label": "negative_period"},
        ],
    }


def _outlier() -> dict:
    return {
        "outlier_repair_run_id": "outlier",
        "decomposition_run_id": "decomp",
        "backoffice_attribution_run_id": "backoffice",
        "investor_persona_attribution_run_id": "persona",
        "gatekeeper_run_id": "gatekeeper",
        "scorecard_run_id": "scorecard",
        "analysis_run_id": "analysis",
        "expanded_trial_run_id": "expanded",
        "backtest_run_id": "backtest",
        "scenario_analysis": [
            {
                "scenario_code": "ex_supportive_date_2021_06_30",
                "median_relative_return_12m": -0.08,
                "hit_rate_vs_benchmark_12m": 0.25,
                "scenario_result_label": "fails_outlier_control",
            }
        ],
    }


def _write_fixture(outputs: Path) -> dict:
    outlier_folder = outputs / "outlier_repair_paths" / "outlier"
    outlier_folder.mkdir(parents=True)
    outlier_path = outlier_folder / "outlier_repair_path_report.json"
    outlier_path.write_text(json.dumps(_outlier()), encoding="utf-8")
    (outputs / "outlier_repair_paths" / "latest_outlier_repair_path_manifest.json").write_text(
        json.dumps({"outlier_repair_run_id": "outlier"}),
        encoding="utf-8",
    )
    decomp_folder = outputs / "backtest_driver_decompositions" / "decomp"
    decomp_folder.mkdir(parents=True)
    (decomp_folder / "backtest_driver_decomposition_report.json").write_text(
        json.dumps(_decomposition()),
        encoding="utf-8",
    )
    backoffice_folder = (
        outputs / "backoffice_evidence_quality_attributions" / "backoffice"
    )
    backoffice_folder.mkdir(parents=True)
    (backoffice_folder / "backoffice_evidence_quality_attribution_report.json").write_text(
        json.dumps({"backoffice_attribution_run_id": "backoffice"}),
        encoding="utf-8",
    )
    scorecard_folder = outputs / "research_evidence_scorecards" / "scorecard"
    scorecard_folder.mkdir(parents=True)
    (scorecard_folder / "research_evidence_scorecard_report.json").write_text(
        json.dumps({"scorecard_run_id": "scorecard"}),
        encoding="utf-8",
    )
    analysis_folder = outputs / "expanded_trial_analyses" / "analysis"
    analysis_folder.mkdir(parents=True)
    (analysis_folder / "expanded_trial_analysis_report.json").write_text(
        json.dumps(_analysis()),
        encoding="utf-8",
    )
    backtest_folder = outputs / "backtests" / "backtest"
    backtest_folder.mkdir(parents=True)
    with (backtest_folder / "backtest_results.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(_rows()[0]))
        writer.writeheader()
        writer.writerows(_rows())
    return {"outlier_path": outlier_path}


def test_loads_latest_and_explicit_outlier_manifest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    latest = load_outlier_repair_manifest(outputs_root=outputs)
    explicit = load_outlier_repair_manifest(
        outputs_root=outputs,
        outlier_repair_run_id="outlier",
    )
    assert latest["outlier_repair_run_id"] == "outlier"
    assert explicit["backtest_run_id"] == "backtest"


def test_missing_outlier_manifest_and_report_raise(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    with pytest.raises(FileNotFoundError, match="manifest not found"):
        load_outlier_repair_manifest(outputs_root=outputs)
    source = _write_fixture(outputs)
    source["outlier_path"].unlink()
    with pytest.raises(FileNotFoundError, match="report not found"):
        write_walk_forward_repair_plan_report(outputs_root=outputs)


def test_period_stability_analysis_includes_all_dates_and_labels() -> None:
    periods = analyze_period_breaks(
        _rows(),
        analysis=_analysis(),
        decomposition=_decomposition(),
    )
    dates = {item["as_of_date"] for item in periods}
    assert set(DATES) == dates
    by_date = {item["as_of_date"]: item for item in periods}
    assert by_date["2021-06-30"]["period_label"] == "supportive_period"
    assert by_date["2021-12-31"]["period_label"] == "negative_period"
    assert by_date["2022-06-30"]["period_label"] == "negative_period"
    assert by_date["2022-12-31"]["period_label"] == "negative_period"
    assert by_date["2023-06-30"]["period_label"] == "negative_period"
    assert by_date["2021-06-30"]["instability_driver_label"] == (
        "supportive_outlier_period"
    )


def test_build_report_creates_required_sections() -> None:
    report = build_walk_forward_repair_plan(
        walk_forward_repair_run_id="repair",
        generated_at="2026-06-16T00:00:00+00:00",
        outlier=_outlier(),
        decomposition=_decomposition(),
        backoffice={},
        scorecard={},
        analysis=_analysis(),
        rows=_rows(),
    )
    assert report.work_order_id == "BO-003"
    assert report.period_stability_analysis
    assert report.clean_vs_warning_period_attribution
    assert report.cohort_by_period_analysis
    assert report.ex_nvda_by_period_analysis
    assert report.supportive_date_dependence
    assert report.stability_failure_modes
    assert report.walk_forward_retest_plan
    assert report.recommended_next_work_order == (
        "BO-004 Delayed Anchor Exposure Repair"
    )


def test_failure_modes_and_retest_plan_include_required_controls() -> None:
    report = build_walk_forward_repair_plan(
        walk_forward_repair_run_id="repair",
        generated_at="2026-06-16T00:00:00+00:00",
        outlier=_outlier(),
        decomposition=_decomposition(),
        backoffice={},
        scorecard={},
        analysis=_analysis(),
        rows=_rows(),
    )
    mode_codes = {item["failure_mode_code"] for item in report.stability_failure_modes}
    assert {
        "supportive_date_dependence",
        "post_2021_relative_underperformance",
        "warning_period_weakness",
        "clean_period_not_sufficient",
        "expanded_cohort_period_drag",
        "nvda_or_top_contributor_period_dependence",
        "benchmark_relative_failure",
    } <= mode_codes
    spec_text = json.dumps(report.walk_forward_retest_plan)
    assert "full sample and ex-supportive-date" in spec_text
    assert "clean-date periods separately from warning-date periods" in spec_text
    assert "current_core and expanded_cohort" in spec_text
    assert "ex-NVDA and ex-top-2 by period" in spec_text
    assert "benchmark-relative and absolute evidence separately" in spec_text


def test_standalone_retest_plan_has_safety_constraints() -> None:
    plan = build_walk_forward_retest_plan()
    assert "required_period_controls" in plan
    assert "No future price information" in json.dumps(plan)


def test_writer_outputs_json_markdown_csv_spec_and_latest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    files = write_walk_forward_repair_plan_report(
        outputs_root=outputs,
        outlier_repair_run_id="outlier",
        generated_at=datetime(2026, 6, 16, tzinfo=timezone.utc),
    )
    for path in (
        files.markdown_path,
        files.json_path,
        files.period_csv_path,
        files.cohort_csv_path,
        files.ex_nvda_csv_path,
        files.failure_modes_csv_path,
        files.retest_plan_path,
        files.latest_manifest_path,
    ):
        assert path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert payload["period_stability_analysis"]
    assert payload["clean_vs_warning_period_attribution"]
    assert payload["cohort_by_period_analysis"]
    assert payload["ex_nvda_by_period_analysis"]
    assert payload["stability_failure_modes"]
    assert payload["walk_forward_retest_plan"]
    markdown = files.markdown_path.read_text(encoding="utf-8")
    for section in (
        "Important Boundary",
        "Period Stability Analysis",
        "Clean vs Warning Period Attribution",
        "Current Core vs Expanded Cohort by Period",
        "Ex-NVDA by Period",
        "Walk-Forward Retest Plan",
    ):
        assert section in markdown


@pytest.mark.parametrize("auto_latest", [False, True])
def test_cli_explicit_and_auto_latest(
    tmp_path: Path, auto_latest: bool
) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    args = [
        "build-walk-forward-repair-plan",
        "--outputs-root",
        str(outputs),
    ]
    if auto_latest:
        args.append("--auto-latest")
    else:
        args.extend(["--outlier-repair-run-id", "outlier"])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "Walk-Forward Stability Repair Plan" in result.output
    assert "period_count=5" in result.output
    assert "failure_mode_count=7" in result.output
    assert "recommended_next_work_order=BO-004 Delayed Anchor Exposure Repair" in (
        result.output
    )
