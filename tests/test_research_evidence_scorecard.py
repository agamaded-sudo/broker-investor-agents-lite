"""Tests for the expanded-trial research evidence scorecard."""

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.backtesting.research_evidence_scorecard import (
    build_research_evidence_scorecard,
    evaluate_scorecard_factors,
    load_expanded_trial_analysis_manifest,
    write_research_evidence_scorecard_report,
)
from broker_agents.cli import app


def _write_fixture(outputs: Path) -> dict:
    analysis_run = "analysis"
    expanded_run = "expanded"
    backtest_run = "backtest"
    prior_run = "prior"
    analysis_folder = outputs / "expanded_trial_analyses" / analysis_run
    expanded_folder = outputs / "expanded_ticker_trials" / expanded_run
    backtest_folder = outputs / "backtests" / backtest_run
    for folder in (analysis_folder, expanded_folder, backtest_folder):
        folder.mkdir(parents=True)

    analysis = {
        "analysis_run_id": analysis_run,
        "expanded_trial_run_id": expanded_run,
        "backtest_run_id": backtest_run,
        "prior_backtest_run_id": prior_run,
        "analysis_status": "instability_explained_preliminary",
        "metadata_diversity_recheck": {
            "metadata_diversity_status": "partially_concentrated",
            "low_diversity_fields": ["buffett_interest_level"],
        },
        "universe_group_attribution": [
            {
                "universe_group": "current_core",
                "median_relative_return_12m": 0.14,
                "hit_rate_vs_benchmark_12m": 0.75,
            },
            {
                "universe_group": "expanded_cohort",
                "median_relative_return_12m": -0.07,
                "hit_rate_vs_benchmark_12m": 0.2,
            },
        ],
        "date_attribution": [
            {"as_of_date": "2021-06-30", "period_label": "supportive_period"},
            {"as_of_date": "2022-06-30", "period_label": "negative_period"},
        ],
        "expanded_trial_instability_explanation": {
            "primary_instability_drivers": [
                "benchmark_underperformance",
                "expanded_cohort_underperformance",
                "period_sensitivity",
            ]
        },
        "prior_trial_comparison": {
            "prior": {"sample_size": 20},
            "expanded": {"sample_size": 60},
        },
    }
    analysis_path = analysis_folder / "expanded_trial_analysis_report.json"
    analysis_path.write_text(json.dumps(analysis), encoding="utf-8")
    latest_path = (
        outputs
        / "expanded_trial_analyses"
        / "latest_expanded_trial_analysis_manifest.json"
    )
    latest_path.write_text(
        json.dumps(
            {
                "analysis_run_id": analysis_run,
                "expanded_trial_run_id": expanded_run,
                "backtest_run_id": backtest_run,
                "prior_backtest_run_id": prior_run,
            }
        ),
        encoding="utf-8",
    )
    expanded = {
        "expanded_trial_run_id": expanded_run,
        "backtest_run_id": backtest_run,
        "sample_size_after_dedupe": 60,
        "clean_record_count": 36,
        "warning_record_count": 24,
        "warning_heavy_record_count": 0,
        "median_forward_return_12m": 0.125658,
        "median_relative_return_12m": -0.050346,
        "hit_rate_vs_benchmark_12m": 0.383333,
        "diagnostic_status": "unstable_needs_deeper_review",
        "decision_status": "needs_more_samples",
        "walk_forward_stability_judgment": "unstable",
        "completed_runs": 60,
        "failed_runs": 0,
        "trial_ledger_validation_status": "valid",
    }
    (expanded_folder / "expanded_ticker_trial_summary.json").write_text(
        json.dumps(expanded), encoding="utf-8"
    )
    manifest = {
        "backtest_run_id": backtest_run,
        "diagnostic_status": "unstable_needs_deeper_review",
        "decision_status": "needs_more_samples",
        "walk_forward_stability_judgment": "unstable",
        "clean_record_count": 36,
        "warning_record_count": 24,
        "warning_heavy_record_count": 0,
        "delayed_anchor_impact_status": (
            "delayed_anchor_present_no_delayed_positive"
        ),
        "no_delayed_anchor_positive": False,
        "outlier_dependence_status": "result_sensitive_to_nvda",
        "ex_nvda_positive": False,
        "ex_top_2_positive": False,
    }
    (backtest_folder / "backtest_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    linked = {
        "readiness_trial_decision_report.json": {
            "decision_status": "needs_more_samples"
        },
        "readiness_trial_diagnostic_report.json": {
            "diagnostic_status": "unstable_needs_deeper_review"
        },
        "clean_coverage_sensitivity_report.json": {
            "sensitivity_status": "mixed_evidence",
            "subset_diagnostics": {
                "clean_records": {
                    "sample_size": 36,
                    "median_relative_return_12m": -0.04,
                }
            },
        },
        "delayed_anchor_impact_report.json": {
            "impact_status": "delayed_anchor_present_no_delayed_positive",
            "impact_assessment": {"no_delayed_anchor_positive": False},
        },
        "outlier_sensitivity_report.json": {
            "outlier_dependence_status": "result_sensitive_to_nvda",
            "outlier_impact_assessment": {
                "ex_nvda_positive": False,
                "ex_top_2_positive": False,
            },
        },
        "walk_forward_metrics.json": {"total_periods": 3},
    }
    for filename, payload in linked.items():
        (backtest_folder / filename).write_text(
            json.dumps(payload), encoding="utf-8"
        )
    return {
        "analysis_run": analysis_run,
        "expanded_run": expanded_run,
        "backtest_run": backtest_run,
        "prior_run": prior_run,
        "analysis": analysis,
        "expanded": expanded,
        "manifest": manifest,
        "analysis_path": analysis_path,
        "latest_path": latest_path,
    }


def _reports(source: dict) -> dict:
    return {
        "manifest": source["manifest"],
        "decision": {"decision_status": "needs_more_samples"},
        "diagnostic": {
            "diagnostic_status": "unstable_needs_deeper_review"
        },
        "clean_coverage": {
            "subset_diagnostics": {
                "clean_records": {
                    "median_relative_return_12m": -0.04,
                }
            }
        },
        "delayed_anchor": {
            "impact_status": "delayed_anchor_present_no_delayed_positive",
            "impact_assessment": {"no_delayed_anchor_positive": False},
        },
        "outlier": {
            "outlier_dependence_status": "result_sensitive_to_nvda",
            "outlier_impact_assessment": {
                "ex_nvda_positive": False,
                "ex_top_2_positive": False,
            },
        },
        "walk_forward": {"total_periods": 3},
    }


def test_loads_latest_and_explicit_analysis_manifest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    source = _write_fixture(outputs)
    latest = load_expanded_trial_analysis_manifest(outputs_root=outputs)
    explicit = load_expanded_trial_analysis_manifest(
        outputs_root=outputs,
        analysis_run_id=source["analysis_run"],
    )
    assert latest["analysis_run_id"] == source["analysis_run"]
    assert explicit["backtest_run_id"] == source["backtest_run"]


def test_missing_analysis_manifest_and_report_raise(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    with pytest.raises(FileNotFoundError, match="manifest not found"):
        load_expanded_trial_analysis_manifest(outputs_root=outputs)
    source = _write_fixture(outputs)
    source["analysis_path"].unlink()
    with pytest.raises(FileNotFoundError, match="analysis report not found"):
        write_research_evidence_scorecard_report(
            outputs_root=outputs,
            analysis_run_id=None,
        )


def test_all_required_factors_and_statuses_are_built(
    tmp_path: Path,
) -> None:
    outputs = tmp_path / "outputs"
    source = _write_fixture(outputs)
    factors = evaluate_scorecard_factors(
        analysis=source["analysis"],
        expanded=source["expanded"],
        reports=_reports(source),
    )
    by_code = {factor.factor_code: factor for factor in factors}
    assert set(by_code) == {
        "sample_size_strength",
        "clean_evidence_strength",
        "warning_evidence_control",
        "benchmark_relative_performance",
        "absolute_forward_performance",
        "walk_forward_stability",
        "diagnostic_status",
        "decision_conservatism",
        "expanded_cohort_effect",
        "period_sensitivity",
        "metadata_diversity",
        "delayed_anchor_effect",
        "outlier_dependence",
        "data_quality_integrity",
    }
    assert by_code["sample_size_strength"].status == "positive"
    assert by_code["clean_evidence_strength"].status == "positive"
    assert by_code["warning_evidence_control"].status == "positive"
    assert by_code["benchmark_relative_performance"].status == "negative"
    assert by_code["absolute_forward_performance"].status == "positive"
    assert by_code["walk_forward_stability"].status == "negative"
    assert by_code["diagnostic_status"].status == "negative"
    assert by_code["decision_conservatism"].status == "positive"
    assert by_code["expanded_cohort_effect"].status == "negative"
    assert by_code["period_sensitivity"].status == "negative"
    assert by_code["metadata_diversity"].status == "warning"
    assert by_code["delayed_anchor_effect"].status == "negative"
    assert by_code["outlier_dependence"].status == "negative"
    assert by_code["data_quality_integrity"].status == "strong_positive"


def test_score_and_classification_are_conservative(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    source = _write_fixture(outputs)
    scorecard = build_research_evidence_scorecard(
        scorecard_run_id="scorecard",
        generated_at="2026-06-15T00:00:00+00:00",
        analysis=source["analysis"],
        expanded=source["expanded"],
        reports=_reports(source),
    )
    assert scorecard.raw_score == sum(
        factor["weighted_score"] for factor in scorecard.factor_results
    )
    assert scorecard.max_possible_score == 38
    assert scorecard.normalized_score_percent < 0
    assert (
        scorecard.research_evidence_classification
        == "unstable_research_evidence"
    )
    assert scorecard.research_decision == "hold_for_deeper_analysis"
    assert scorecard.recommended_next_research_action == (
        "prepare_research_gatekeeper_with_hold_bias"
    )
    assert scorecard.scorecard_status == "scorecard_completed_with_warnings"


def test_writer_outputs_json_markdown_csv_and_latest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    source = _write_fixture(outputs)
    files = write_research_evidence_scorecard_report(
        outputs_root=outputs,
        analysis_run_id=source["analysis_run"],
        generated_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
    )
    for path in (
        files.markdown_path,
        files.json_path,
        files.factors_csv_path,
        files.latest_manifest_path,
    ):
        assert path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert len(payload["factor_results"]) == 14
    assert payload["research_evidence_classification"] == (
        "unstable_research_evidence"
    )
    assert payload["research_decision"] == "hold_for_deeper_analysis"
    markdown = files.markdown_path.read_text(encoding="utf-8")
    for section in (
        "Factor Results",
        "Key Strengths",
        "Key Weaknesses",
        "Research Classification",
        "Relationship to Prior Evidence",
    ):
        assert section in markdown


@pytest.mark.parametrize("auto_latest", [False, True])
def test_cli_explicit_and_auto_latest(
    tmp_path: Path,
    auto_latest: bool,
) -> None:
    outputs = tmp_path / "outputs"
    source = _write_fixture(outputs)
    args = [
        "build-research-evidence-scorecard",
        "--outputs-root",
        str(outputs),
    ]
    if auto_latest:
        args.append("--auto-latest")
    else:
        args.extend(["--analysis-run-id", source["analysis_run"]])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "Research Evidence Scorecard" in result.output
    assert "unstable_research_evidence" in result.output
    assert "research_decision=hold_for_deeper_analysis" in result.output
