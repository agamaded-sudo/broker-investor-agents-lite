"""Tests for the research evidence governance gatekeeper."""

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.backtesting.research_gatekeeper import (
    evaluate_gatekeeper_rules,
    load_research_evidence_scorecard_manifest,
    run_research_gatekeeper,
    write_research_gatekeeper_report,
)
from broker_agents.cli import app


def _factor(code: str, status: str, evidence: dict | None = None) -> dict:
    return {
        "factor_code": code,
        "label": code.replace("_", " ").title(),
        "status": status,
        "weight": 1,
        "evidence": evidence or {},
        "interpretation": f"{code} interpretation.",
        "weighted_score": 0,
    }


def _scorecard() -> dict:
    return {
        "scorecard_run_id": "scorecard",
        "analysis_run_id": "analysis",
        "expanded_trial_run_id": "expanded",
        "backtest_run_id": "backtest",
        "scorecard_status": "scorecard_completed_with_warnings",
        "research_evidence_classification": "unstable_research_evidence",
        "research_decision": "hold_for_deeper_analysis",
        "blocker_count": 0,
        "factor_results": [
            _factor(
                "benchmark_relative_performance",
                "negative",
                {
                    "median_relative_return_12m": -0.05,
                    "hit_rate_vs_benchmark_12m": 0.38,
                },
            ),
            _factor("walk_forward_stability", "negative"),
            _factor("diagnostic_status", "negative"),
            _factor("expanded_cohort_effect", "negative"),
            _factor("period_sensitivity", "negative"),
            _factor("outlier_dependence", "negative"),
            _factor("delayed_anchor_effect", "negative"),
            _factor("data_quality_integrity", "strong_positive"),
            _factor("clean_evidence_strength", "positive"),
            _factor(
                "warning_evidence_control",
                "positive",
                {"warning_heavy_record_count": 0},
            ),
        ],
    }


def _write_fixture(outputs: Path) -> Path:
    scorecard = _scorecard()
    folder = outputs / "research_evidence_scorecards" / "scorecard"
    folder.mkdir(parents=True)
    report_path = folder / "research_evidence_scorecard_report.json"
    report_path.write_text(json.dumps(scorecard), encoding="utf-8")
    latest = outputs / "research_evidence_scorecards"
    (latest / "latest_research_evidence_scorecard_manifest.json").write_text(
        json.dumps(
            {
                "scorecard_run_id": "scorecard",
                "analysis_run_id": "analysis",
                "expanded_trial_run_id": "expanded",
                "backtest_run_id": "backtest",
            }
        ),
        encoding="utf-8",
    )
    return report_path


def test_loads_latest_and_explicit_scorecard_manifest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    latest = load_research_evidence_scorecard_manifest(outputs_root=outputs)
    explicit = load_research_evidence_scorecard_manifest(
        outputs_root=outputs,
        scorecard_run_id="scorecard",
    )
    assert latest["scorecard_run_id"] == "scorecard"
    assert explicit["research_decision"] == "hold_for_deeper_analysis"


def test_missing_scorecard_manifest_and_report_raise(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    with pytest.raises(FileNotFoundError, match="artifact not found"):
        load_research_evidence_scorecard_manifest(outputs_root=outputs)
    report_path = _write_fixture(outputs)
    report_path.unlink()
    with pytest.raises(FileNotFoundError, match="artifact not found"):
        write_research_gatekeeper_report(outputs_root=outputs)


def test_all_required_rules_are_built_with_expected_statuses() -> None:
    rules = evaluate_gatekeeper_rules(_scorecard())
    by_code = {rule.rule_code: rule for rule in rules}
    assert set(by_code) == {
        "scorecard_status_rule",
        "classification_rule",
        "research_decision_rule",
        "benchmark_relative_rule",
        "walk_forward_rule",
        "diagnostic_rule",
        "expanded_cohort_rule",
        "period_sensitivity_rule",
        "outlier_dependence_rule",
        "delayed_anchor_rule",
        "data_quality_integrity_rule",
        "clean_evidence_rule",
        "warning_heavy_rule",
        "blocker_factor_rule",
        "progression_safety_rule",
    }
    assert by_code["scorecard_status_rule"].status == "warn"
    for code in (
        "classification_rule",
        "research_decision_rule",
        "benchmark_relative_rule",
        "walk_forward_rule",
        "diagnostic_rule",
        "expanded_cohort_rule",
        "period_sensitivity_rule",
        "outlier_dependence_rule",
        "delayed_anchor_rule",
        "progression_safety_rule",
    ):
        assert by_code[code].status == "hold"
    for code in (
        "data_quality_integrity_rule",
        "clean_evidence_rule",
        "warning_heavy_rule",
        "blocker_factor_rule",
    ):
        assert by_code[code].status == "pass"


def test_current_scorecard_produces_hold_verdict() -> None:
    report = run_research_gatekeeper(
        gatekeeper_run_id="gate",
        generated_at="2026-06-15T00:00:00+00:00",
        scorecard=_scorecard(),
    )
    assert report.gatekeeper_decision == "hold"
    assert report.progression_allowed is False
    assert report.hold_bias is True
    assert report.gatekeeper_status == "completed_with_hold"
    assert report.research_progression_status == "held_for_deeper_research"
    assert report.recommended_next_research_action == (
        "run_deeper_research_or_repair_before_progression"
    )


def test_blocker_factor_produces_block_verdict() -> None:
    scorecard = {**_scorecard(), "blocker_count": 1}
    report = run_research_gatekeeper(
        gatekeeper_run_id="gate",
        generated_at="2026-06-15T00:00:00+00:00",
        scorecard=scorecard,
    )
    assert report.gatekeeper_decision == "block"
    assert report.progression_allowed is False
    assert "blocker_factor_rule" in report.block_rules


def test_writer_outputs_reports_rules_and_latest_manifest(
    tmp_path: Path,
) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    files = write_research_gatekeeper_report(
        outputs_root=outputs,
        scorecard_run_id="scorecard",
        generated_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
    )
    for path in (
        files.markdown_path,
        files.json_path,
        files.rules_csv_path,
        files.latest_manifest_path,
    ):
        assert path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert payload["gatekeeper_decision"] == "hold"
    assert payload["progression_allowed"] is False
    assert payload["hold_bias"] is True
    assert len(payload["rule_results"]) == 15
    markdown = files.markdown_path.read_text(encoding="utf-8")
    for section in (
        "Gatekeeper Verdict",
        "Rule Results",
        "Passing Evidence",
        "Holding Evidence",
        "Required Before Progression",
    ):
        assert section in markdown


@pytest.mark.parametrize("auto_latest", [False, True])
def test_cli_explicit_and_auto_latest(
    tmp_path: Path,
    auto_latest: bool,
) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    args = [
        "run-research-gatekeeper",
        "--outputs-root",
        str(outputs),
    ]
    if auto_latest:
        args.append("--auto-latest")
    else:
        args.extend(["--scorecard-run-id", "scorecard"])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "Research Gatekeeper" in result.output
    assert "gatekeeper_decision=hold" in result.output
    assert "progression_allowed=false" in result.output
    assert "status=completed_with_hold" in result.output
