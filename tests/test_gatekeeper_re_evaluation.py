import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.regate.gatekeeper_re_evaluation import (
    ALLOWED_OUTCOMES,
    build_evidence_change_assessment_matrix,
    build_gatekeeper_re_evaluation,
    build_gatekeeper_re_evaluation_validation_checks,
    build_next_phase_options_matrix,
    build_re_evaluation_summary,
    build_re_gate_decision_record,
    build_re_gate_input_readiness_matrix,
    build_re_gate_rule_evaluation_matrix,
    build_safety_re_evaluation_matrix,
    build_task_124_handoff_manifest,
    load_pre_post_repair_comparison,
    load_pre_post_repair_comparison_manifest,
    write_gatekeeper_re_evaluation_report,
)


def _comparison() -> dict:
    return {
        "pre_post_repair_comparison_run_id": "comparison_run",
        "controlled_re_run_trial_run_id": "trial_run",
        "re_run_input_package_run_id": "input_package_run",
        "re_run_re_gate_plan_run_id": "plan_run",
        "research_audit_trail_run_id": "audit_run",
        "buffett_munger_pack_run_id": "buffett_munger_run",
        "fisher_growth_pack_run_id": "fisher_run",
        "bogle_benchmark_pack_run_id": "bogle_run",
        "persona_evidence_pack_run_id": "persona_pack_run",
        "metadata_diversity_recheck_run_id": "metadata_run",
        "delayed_anchor_repair_run_id": "delayed_anchor_run",
        "walk_forward_repair_run_id": "walk_forward_run",
        "outlier_repair_run_id": "outlier_run",
        "decomposition_run_id": "decomposition_run",
        "backoffice_attribution_run_id": "backoffice_run",
        "investor_persona_attribution_run_id": "persona_attribution_run",
        "gatekeeper_run_id": "previous_gatekeeper_run",
        "scorecard_run_id": "scorecard_run",
        "analysis_run_id": "analysis_run",
        "expanded_trial_run_id": "expanded_trial_run",
        "backtest_run_id": "backtest_run",
        "evidence_delta_matrix": [
            {
                "comparison_code": "full_sample_delta",
                "post_relative_median_12m": -0.05,
            },
            {
                "comparison_code": "current_core_delta",
                "post_relative_median_12m": 0.12,
            },
        ],
        "stability_delta_matrix": [
            {
                "stability_dimension": "walk_forward_stability",
                "remaining_instability_flag": True,
            },
        ],
        "limitation_resolution_matrix": [
            {
                "limitation_code": "metadata_concentration_remaining",
                "still_blocks_interpretation": True,
            },
        ],
    }


def _write_fixture(outputs_root: Path) -> Path:
    comparison = _comparison()
    root = outputs_root / "pre_post_repair_comparisons"
    run_dir = root / comparison["pre_post_repair_comparison_run_id"]
    run_dir.mkdir(parents=True)
    report_path = run_dir / "pre_post_repair_comparison.json"
    report_path.write_text(json.dumps(comparison), encoding="utf-8")
    (root / "latest_pre_post_repair_comparison_manifest.json").write_text(
        json.dumps(
            {
                "pre_post_repair_comparison_run_id": comparison[
                    "pre_post_repair_comparison_run_id"
                ],
                "report_json_path": str(report_path),
            }
        ),
        encoding="utf-8",
    )
    return outputs_root


def _codes(rows: list[dict], key: str) -> set[str]:
    return {str(row[key]) for row in rows}


def test_loads_latest_pre_post_repair_comparison_manifest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_pre_post_repair_comparison_manifest(outputs_root=outputs_root)

    assert manifest["pre_post_repair_comparison_run_id"] == "comparison_run"


def test_loads_explicit_pre_post_repair_comparison_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_pre_post_repair_comparison_manifest(
        outputs_root=outputs_root,
        pre_post_repair_comparison_run_id="comparison_run",
    )
    report = load_pre_post_repair_comparison(
        outputs_root=outputs_root,
        pre_post_repair_comparison_run_id="comparison_run",
    )

    assert manifest["controlled_re_run_trial_run_id"] == "trial_run"
    assert report["gatekeeper_run_id"] == "previous_gatekeeper_run"


def test_handles_missing_pre_post_repair_comparison_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_pre_post_repair_comparison_manifest(outputs_root=tmp_path)


def test_handles_missing_pre_post_repair_comparison_report(tmp_path: Path) -> None:
    root = tmp_path / "pre_post_repair_comparisons"
    root.mkdir()
    (root / "latest_pre_post_repair_comparison_manifest.json").write_text(
        json.dumps({"pre_post_repair_comparison_run_id": "missing"}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        load_pre_post_repair_comparison(
            outputs_root=tmp_path,
            pre_post_repair_comparison_run_id="missing",
        )


def test_re_evaluation_summary_is_created() -> None:
    comparison = _comparison()
    inputs = build_re_gate_input_readiness_matrix(comparison)
    safety = build_safety_re_evaluation_matrix(comparison)
    decision = build_re_gate_decision_record(
        gatekeeper_re_evaluation_run_id="re_gate_run",
        comparison=comparison,
        input_rows=inputs,
        safety_rows=safety,
    )

    summary = build_re_evaluation_summary(
        gatekeeper_re_evaluation_run_id="re_gate_run",
        comparison=comparison,
        decision=decision,
    )

    assert summary["current_task_id"] == 123
    assert summary["gatekeeper_re_evaluation_status"] == "completed"
    assert summary["recommended_next_task"].startswith("Task 124")


def test_re_gate_input_readiness_matrix_has_required_inputs() -> None:
    rows = build_re_gate_input_readiness_matrix(_comparison())

    codes = _codes(rows, "input_code")

    assert "controlled_re_run_completed" in codes
    assert "pre_post_repair_comparison_completed" in codes
    assert "evidence_delta_matrix_available" in codes
    assert "safety_validation_available" in codes
    assert all(row["readiness_status"] == "satisfied" for row in rows)


def test_re_gate_rule_evaluation_matrix_has_required_rules() -> None:
    rows = build_re_gate_rule_evaluation_matrix(_comparison())

    codes = _codes(rows, "rule_code")

    assert "re_run_prerequisites_satisfied" in codes
    assert "comparison_prerequisites_satisfied" in codes
    assert "benchmark_relative_evidence_improved_or_explained" in codes
    assert "walk_forward_instability_resolved_or_disclosed" in codes
    assert "outlier_dependence_resolved_or_disclosed" in codes
    assert "safety_ledger_clear" in codes


def test_evidence_change_assessment_matrix_has_required_areas() -> None:
    rows = build_evidence_change_assessment_matrix(_comparison())

    codes = _codes(rows, "evidence_area")

    assert "full_sample" in codes
    assert "benchmark_relative" in codes
    assert "current_core" in codes
    assert "expanded_cohort" in codes
    assert "walk_forward_stability" in codes
    assert "metadata_concentration" in codes


def test_safety_re_evaluation_matrix_has_no_violations() -> None:
    rows = build_safety_re_evaluation_matrix(_comparison())

    codes = _codes(rows, "safety_rule")

    assert "no_investment_decision" in codes
    assert "no_buy_sell_hold_recommendation" in codes
    assert "no_persona_review_run" in codes
    assert "no_network_calls" in codes
    assert all(row["violation_found"] is False for row in rows)


def test_re_gate_decision_record_is_conservative() -> None:
    comparison = _comparison()
    inputs = build_re_gate_input_readiness_matrix(comparison)
    safety = build_safety_re_evaluation_matrix(comparison)

    decision = build_re_gate_decision_record(
        gatekeeper_re_evaluation_run_id="re_gate_run",
        comparison=comparison,
        input_rows=inputs,
        safety_rows=safety,
    )

    assert decision["previous_gatekeeper_decision"] == "hold"
    assert decision["new_gatekeeper_outcome"] in ALLOWED_OUTCOMES
    assert decision["new_gatekeeper_outcome"] == "hold_with_repair_progress"
    assert decision["progression_allowed_after_re_evaluation"] is False
    assert decision["persona_reviews_allowed_after_re_evaluation"] is False


def test_next_phase_options_and_task_124_handoff_are_created() -> None:
    options = build_next_phase_options_matrix()
    handoff = build_task_124_handoff_manifest(
        gatekeeper_re_evaluation_run_id="re_gate_run"
    )

    option_codes = _codes(options, "option_code")

    assert "if_hold_continue_repair" in option_codes
    assert "if_hold_with_repair_progress_plan_targeted_repair" in option_codes
    assert "if_pass_with_warnings_prepare_limited_review_controls" in option_codes
    assert "if_block_archive_or_rebuild" in option_codes
    assert handoff["future_task_id"] == 124
    assert handoff["execution_allowed_now"] is True


def test_gatekeeper_re_evaluation_validation_checks_are_created() -> None:
    rows = build_gatekeeper_re_evaluation_validation_checks()

    codes = _codes(rows, "check_code")

    assert "persona_review_not_run" in codes
    assert "no_recommendation_outputs" in codes
    assert "no_network_calls" in codes
    assert all(row["status"] == "satisfied" for row in rows)


def test_build_gatekeeper_re_evaluation_report_contains_required_sections() -> None:
    report = build_gatekeeper_re_evaluation(
        gatekeeper_re_evaluation_run_id="re_gate_run",
        generated_at="2026-06-18T12:00:00+00:00",
        comparison=_comparison(),
    )
    data = report.to_dict()

    assert data["re_gate_input_readiness_matrix"]
    assert data["re_gate_rule_evaluation_matrix"]
    assert data["evidence_change_assessment_matrix"]
    assert data["safety_re_evaluation_matrix"]
    assert data["re_gate_decision_record"]["persona_reviews_allowed_after_re_evaluation"] is False
    assert data["task_124_handoff_manifest"]["future_task_id"] == 124


def test_write_gatekeeper_re_evaluation_report_writes_files(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    files = write_gatekeeper_re_evaluation_report(
        outputs_root=outputs_root,
        pre_post_repair_comparison_run_id="comparison_run",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.input_readiness_csv_path.is_file()
    assert files.rule_evaluation_csv_path.is_file()
    assert files.evidence_change_csv_path.is_file()
    assert files.safety_re_evaluation_csv_path.is_file()
    assert files.decision_record_path.is_file()
    assert files.next_phase_options_csv_path.is_file()
    assert files.task_124_handoff_manifest_path.is_file()
    assert files.validation_checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Re-Gate Input Readiness Matrix" in markdown
    assert "## Re-Gate Rule Evaluation Matrix" in markdown
    assert "## Evidence Change Assessment Matrix" in markdown
    assert "## Task 124 Handoff" in markdown


def test_cli_works_with_explicit_pre_post_repair_comparison_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "run-gatekeeper-re-evaluation",
            "--pre-post-repair-comparison-run-id",
            "comparison_run",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "gatekeeper_re_evaluation_run_id=" in result.output
    assert "new_gatekeeper_outcome=hold_with_repair_progress" in result.output
    assert "persona_reviews_allowed_after_re_evaluation=false" in result.output


def test_cli_works_with_auto_latest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "run-gatekeeper-re-evaluation",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "pre_post_repair_comparison_run_id=comparison_run" in result.output
    assert "recommended_next_task=Task 124" in result.output
