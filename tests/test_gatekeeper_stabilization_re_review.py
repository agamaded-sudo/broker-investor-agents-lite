import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.stabilization.gatekeeper_stabilization_re_review import (
    build_gatekeeper_stabilization_re_review,
    build_gatekeeper_stabilization_re_review_checks,
    build_permission_boundary_matrix,
    build_re_review_rule_evaluation_matrix,
    build_re_review_summary,
    build_residual_risk_after_re_review_matrix,
    build_stabilization_gatekeeper_decision_record,
    build_stabilized_blocker_status_matrix,
    build_task_131_handoff_manifest,
    load_baseline_gatekeeper_re_evaluation,
    load_gatekeeper_stabilized_comparison,
    load_gatekeeper_stabilized_comparison_manifest,
    write_gatekeeper_stabilization_re_review_report,
)


def _comparison() -> dict:
    blockers = [
        ("progression_not_allowed", "unchanged"),
        ("persona_review_not_allowed", "unchanged"),
        ("evidence_still_unstable_or_not_progression_ready", "partially_improved"),
        ("residual_benchmark_relative_uncertainty", "improved_with_warnings"),
        ("residual_walk_forward_or_period_sensitivity", "improved_with_warnings"),
        ("residual_outlier_dependence", "improved_with_warnings"),
        ("residual_metadata_concentration", "improved_with_warnings"),
        ("residual_clean_warning_or_anchor_uncertainty", "improved_with_warnings"),
        ("residual_current_core_expanded_cohort_gap", "improved_with_warnings"),
        ("local_artifacts_only_limitation", "documented_only"),
    ]
    risks = [
        "benchmark_relative_uncertainty",
        "walk_forward_period_sensitivity",
        "supportive_period_dependence",
        "outlier_dependence",
        "clean_warning_anchor_gap",
        "core_vs_expanded_gap",
        "metadata_concentration",
        "local_artifact_only_limitation",
        "partial_repair_completion",
        "no_gatekeeper_rerun_yet",
    ]
    return {
        "gatekeeper_stabilized_comparison_run_id": "comparison_run",
        "stabilization_validation_run_id": "validation_run",
        "targeted_repair_run_id": "repair_run",
        "residual_work_order_package_run_id": "work_order_run",
        "stabilization_plan_run_id": "plan_run",
        "phase_16_closure_run_id": "closure_run",
        "gatekeeper_re_evaluation_run_id": "re_gate_run",
        "pre_post_repair_comparison_run_id": "pre_post_run",
        "controlled_re_run_trial_run_id": "trial_run",
        "re_run_input_package_run_id": "input_run",
        "re_run_re_gate_plan_run_id": "plan_119_run",
        "research_audit_trail_run_id": "audit_run",
        "comparison_summary": {
            "task_123_gatekeeper_outcome": "hold_with_repair_progress",
            "progression_allowed": False,
            "persona_reviews_allowed": False,
            "blockers_compared": 10,
            "blockers_improved": 0,
            "blockers_partially_improved": 7,
            "blockers_unresolved": 2,
        },
        "gatekeeper_blocker_comparison_matrix": [
            {
                "blocker_code": code,
                "blocker_label": code.replace("_", " "),
                "task_123_state": "hold_with_repair_progress",
                "comparison_status": status,
                "remaining_issue": "Residual issue remains.",
            }
            for code, status in blockers
        ],
        "residual_risk_comparison_matrix": [
            {
                "risk_code": code,
                "risk_label": code.replace("_", " "),
                "stabilized_risk_state": "documented_for_task_130",
                "severity_after_stabilization": "high",
                "required_follow_up": "Carry into phase closure.",
            }
            for code in risks
        ],
    }


def _baseline_gatekeeper() -> dict:
    return {
        "gatekeeper_re_evaluation_run_id": "re_gate_run",
        "re_evaluation_summary": {
            "new_gatekeeper_outcome": "hold_with_repair_progress",
        },
        "re_gate_decision_record": {
            "new_gatekeeper_outcome": "hold_with_repair_progress",
        },
    }


def _write_fixture(outputs_root: Path) -> Path:
    comparison = _comparison()
    baseline = _baseline_gatekeeper()
    comparison_root = outputs_root / "gatekeeper_stabilized_evidence_comparisons"
    comparison_dir = comparison_root / comparison["gatekeeper_stabilized_comparison_run_id"]
    comparison_dir.mkdir(parents=True)
    comparison_path = comparison_dir / "gatekeeper_stabilized_evidence_comparison.json"
    comparison_path.write_text(json.dumps(comparison), encoding="utf-8")
    (comparison_root / "latest_gatekeeper_stabilized_evidence_comparison_manifest.json").write_text(
        json.dumps(
            {
                "gatekeeper_stabilized_comparison_run_id": comparison[
                    "gatekeeper_stabilized_comparison_run_id"
                ],
                "report_json_path": str(comparison_path),
            }
        ),
        encoding="utf-8",
    )
    baseline_dir = (
        outputs_root
        / "gatekeeper_re_evaluations"
        / baseline["gatekeeper_re_evaluation_run_id"]
    )
    baseline_dir.mkdir(parents=True)
    (baseline_dir / "gatekeeper_re_evaluation.json").write_text(
        json.dumps(baseline),
        encoding="utf-8",
    )
    return outputs_root


def _codes(rows: list[dict], key: str) -> set[str]:
    return {str(row[key]) for row in rows}


def test_loads_latest_comparison_manifest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_gatekeeper_stabilized_comparison_manifest(outputs_root=outputs_root)

    assert manifest["gatekeeper_stabilized_comparison_run_id"] == "comparison_run"


def test_loads_explicit_comparison_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_gatekeeper_stabilized_comparison_manifest(
        outputs_root=outputs_root,
        gatekeeper_stabilized_comparison_run_id="comparison_run",
    )
    report = load_gatekeeper_stabilized_comparison(
        outputs_root=outputs_root,
        gatekeeper_stabilized_comparison_run_id="comparison_run",
    )

    assert manifest["gatekeeper_re_evaluation_run_id"] == "re_gate_run"
    assert report["gatekeeper_stabilized_comparison_run_id"] == "comparison_run"


def test_handles_missing_comparison_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_gatekeeper_stabilized_comparison_manifest(outputs_root=tmp_path)


def test_handles_missing_comparison_report(tmp_path: Path) -> None:
    root = tmp_path / "gatekeeper_stabilized_evidence_comparisons"
    root.mkdir()
    (root / "latest_gatekeeper_stabilized_evidence_comparison_manifest.json").write_text(
        json.dumps({"gatekeeper_stabilized_comparison_run_id": "missing"}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        load_gatekeeper_stabilized_comparison(
            outputs_root=tmp_path,
            gatekeeper_stabilized_comparison_run_id="missing",
        )


def test_handles_missing_baseline_gatekeeper_report(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_baseline_gatekeeper_re_evaluation(
            outputs_root=tmp_path,
            gatekeeper_re_evaluation_run_id="missing",
        )


def test_re_review_summary_is_created() -> None:
    summary = build_re_review_summary(
        gatekeeper_stabilization_re_review_run_id="review_run",
        comparison=_comparison(),
        baseline_gatekeeper=_baseline_gatekeeper(),
    )

    assert summary["phase_id"] == 17
    assert summary["current_task_id"] == 130
    assert summary["baseline_gatekeeper_outcome"] == "hold_with_repair_progress"
    assert summary["new_gatekeeper_stabilization_outcome"]
    assert summary["progression_status_after_re_review"]
    assert summary["persona_review_status_after_re_review"]
    assert summary["re_review_status"] in {"completed", "completed_with_warnings"}
    assert summary["recommended_next_task"].startswith("Task 131")


def test_decision_record_is_conservative() -> None:
    summary = build_re_review_summary(
        gatekeeper_stabilization_re_review_run_id="review_run",
        comparison=_comparison(),
        baseline_gatekeeper=_baseline_gatekeeper(),
    )
    decision = build_stabilization_gatekeeper_decision_record(summary)

    assert decision["baseline_gatekeeper_outcome"] == "hold_with_repair_progress"
    assert decision["new_gatekeeper_stabilization_outcome"]
    assert decision["decision_rationale"]
    assert decision["evidence_basis"]
    assert decision["blocker_basis"]
    assert decision["residual_risk_basis"]
    assert decision["auto_promotion_status"] == "disabled"
    assert decision["investor_agent_execution_status"] == "not_allowed"


def test_re_review_rule_evaluation_matrix_has_required_rules() -> None:
    summary = build_re_review_summary(
        gatekeeper_stabilization_re_review_run_id="review_run",
        comparison=_comparison(),
        baseline_gatekeeper=_baseline_gatekeeper(),
    )
    rows = build_re_review_rule_evaluation_matrix(summary)

    codes = _codes(rows, "rule_code")

    assert "no_unrestricted_progression_with_unresolved_blockers" in codes
    assert "no_persona_review_with_unresolved_material_blockers" in codes
    assert "no_auto_promotion" in codes
    assert "no_investor_agent_execution" in codes
    assert "evidence_improvement_must_be_validated" in codes
    assert "partial_improvement_is_not_full_resolution" in codes
    assert "unresolved_blockers_keep_hold_or_limited_status" in codes
    assert "local_artifact_limitations_reduce_confidence" in codes
    assert "recommendations_rankings_trading_outputs_prohibited" in codes


def test_stabilized_blocker_status_matrix_has_required_blockers() -> None:
    rows = build_stabilized_blocker_status_matrix(_comparison())

    codes = _codes(rows, "blocker_code")

    assert "progression_not_allowed" in codes
    assert "persona_review_not_allowed" in codes
    assert "evidence_still_unstable_or_not_progression_ready" in codes
    assert "residual_benchmark_relative_uncertainty" in codes
    assert "residual_walk_forward_or_period_sensitivity" in codes
    assert "residual_outlier_dependence" in codes
    assert "residual_metadata_concentration" in codes
    assert "residual_clean_warning_or_anchor_uncertainty" in codes
    assert "residual_current_core_expanded_cohort_gap" in codes
    assert "local_artifacts_only_limitation" in codes


def test_residual_risk_after_re_review_matrix_has_required_risks() -> None:
    rows = build_residual_risk_after_re_review_matrix(_comparison())

    codes = _codes(rows, "risk_code")

    assert "benchmark_relative_uncertainty" in codes
    assert "walk_forward_period_sensitivity" in codes
    assert "supportive_period_dependence" in codes
    assert "outlier_dependence" in codes
    assert "metadata_concentration" in codes
    assert "no_persona_review_allowed_yet" in codes


def test_permission_boundary_matrix_blocks_investor_actions() -> None:
    summary = build_re_review_summary(
        gatekeeper_stabilization_re_review_run_id="review_run",
        comparison=_comparison(),
        baseline_gatekeeper=_baseline_gatekeeper(),
    )
    rows = build_permission_boundary_matrix(summary)
    by_code = {row["permission_code"]: row for row in rows}

    assert "progression" in by_code
    assert "gatekeeper_return_package_preparation" in by_code
    assert "persona_review_preparation" in by_code
    assert by_code["actual_persona_review"]["status_after_re_review"] == "not_allowed"
    assert by_code["investor_agent_execution"]["status_after_re_review"] == "not_allowed"
    assert by_code["investor_decision_generation"]["status_after_re_review"] == "not_allowed"
    assert by_code["company_ranking"]["status_after_re_review"] == "not_allowed"
    assert by_code["investment_recommendation"]["status_after_re_review"] == "not_allowed"
    assert by_code["allocation_or_rebalancing"]["status_after_re_review"] == "not_allowed"
    assert by_code["trade_signal_generation"]["status_after_re_review"] == "not_allowed"
    assert by_code["auto_promotion"]["status_after_re_review"] == "disabled"


def test_task_131_handoff_manifest_is_created() -> None:
    handoff = build_task_131_handoff_manifest(
        gatekeeper_stabilization_re_review_run_id="review_run",
        comparison=_comparison(),
        baseline_gatekeeper=_baseline_gatekeeper(),
    )

    assert handoff["future_phase_id"] == 17
    assert handoff["future_task_id"] == 131
    assert handoff["readiness_status"] == "ready_for_phase_17_closure"
    assert handoff["execution_allowed_now"] is True
    assert "investor decisions" in handoff["prohibited_outputs"]
    assert "investor agent execution" in handoff["prohibited_outputs"]


def test_validation_checks_are_created() -> None:
    rows = build_gatekeeper_stabilization_re_review_checks()

    codes = _codes(rows, "check_code")

    assert "baseline_gatekeeper_outcome_preserved" in codes
    assert "conservative_re_review_logic_applied" in codes
    assert "actual_persona_review_not_run" in codes
    assert "investor_agents_not_run" in codes
    assert "no_recommendation_outputs" in codes
    assert "auto_promotion_disabled" in codes
    assert all(row["status"] == "satisfied" for row in rows)


def test_build_re_review_report_has_sections() -> None:
    report = build_gatekeeper_stabilization_re_review(
        gatekeeper_stabilization_re_review_run_id="review_run",
        generated_at="2026-06-19T00:00:00+00:00",
        comparison=_comparison(),
        baseline_gatekeeper=_baseline_gatekeeper(),
    )
    data = report.to_dict()

    assert data["re_review_summary"]
    assert data["stabilization_gatekeeper_decision_record"]
    assert data["re_review_rule_evaluation_matrix"]
    assert data["stabilized_blocker_status_matrix"]
    assert data["residual_risk_after_re_review_matrix"]
    assert data["permission_boundary_matrix"]
    assert data["task_131_handoff_manifest"]
    assert data["gatekeeper_stabilization_re_review_checks"]


def test_write_re_review_report_writes_files(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    files = write_gatekeeper_stabilization_re_review_report(
        outputs_root=outputs_root,
        gatekeeper_stabilized_comparison_run_id="comparison_run",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.decision_record_path.is_file()
    assert files.rule_csv_path.is_file()
    assert files.blocker_csv_path.is_file()
    assert files.residual_risk_csv_path.is_file()
    assert files.permission_csv_path.is_file()
    assert files.task_131_handoff_manifest_path.is_file()
    assert files.checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Gatekeeper Decision Record" in markdown
    assert "## Re-Review Rule Evaluation Matrix" in markdown
    assert "## Stabilized Blocker Status Matrix" in markdown
    assert "## Residual Risk After Re-Review" in markdown
    assert "## Permission Boundary Matrix" in markdown
    assert "## Task 131 Handoff" in markdown
    assert "## What This Does Not Suggest" in markdown


def test_cli_works_with_explicit_comparison_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "run-gatekeeper-stabilization-re-review",
            "--gatekeeper-stabilized-comparison-run-id",
            "comparison_run",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "gatekeeper_stabilization_re_review_run_id=" in result.output
    assert "baseline_gatekeeper_outcome=hold_with_repair_progress" in result.output
    assert "recommended_next_task=Task 131" in result.output


def test_cli_works_with_auto_latest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "run-gatekeeper-stabilization-re-review",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "gatekeeper_stabilized_comparison_run_id=comparison_run" in result.output
    assert "status=completed_with_warnings" in result.output
