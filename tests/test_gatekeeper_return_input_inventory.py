import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.gatekeeper_return.gatekeeper_return_input_inventory import (
    ARTIFACT_MAP,
    build_component_input_inventory_matrix,
    build_evidence_artifact_inventory_matrix,
    build_gatekeeper_return_input_inventory,
    build_gatekeeper_return_input_inventory_checks,
    build_input_inventory_summary,
    build_missing_or_warning_input_matrix,
    build_package_assembly_readiness_matrix,
    build_source_run_traceability_matrix,
    build_task_134_handoff_manifest,
    load_gatekeeper_return_package_plan,
    load_gatekeeper_return_package_plan_manifest,
    write_gatekeeper_return_input_inventory_report,
)


def _plan() -> dict:
    components = [
        "executive_gatekeeper_return_summary",
        "final_gatekeeper_stabilization_decision_record",
        "permission_boundary_summary",
        "blocker_disposition_summary",
        "residual_risk_disclosure",
        "evidence_stabilization_timeline",
        "repaired_evidence_inventory",
        "validation_evidence_inventory",
        "comparison_evidence_inventory",
        "local_artifact_limitation_disclosure",
        "no_persona_review_confirmation",
        "no_investor_agent_execution_confirmation",
        "no_recommendation_output_confirmation",
        "auto_promotion_disabled_confirmation",
        "next_gatekeeper_review_questions",
    ]
    evidence = [
        ("phase_17_closure", 17, 131, "closure_run", "phase_17_closure.json"),
        (
            "gatekeeper_stabilization_re_review",
            17,
            130,
            "review_run",
            "gatekeeper_stabilization_re_review.json",
        ),
        (
            "gatekeeper_stabilized_evidence_comparison",
            17,
            129,
            "comparison_run",
            "gatekeeper_stabilized_evidence_comparison.json",
        ),
        (
            "stabilization_validation_trial",
            17,
            128,
            "validation_run",
            "stabilization_validation_trial.json",
        ),
        (
            "targeted_evidence_repairs",
            17,
            127,
            "repair_run",
            "targeted_evidence_repairs.json",
        ),
        (
            "residual_blocker_work_orders",
            17,
            126,
            "work_order_run",
            "residual_blocker_work_orders.json",
        ),
        (
            "targeted_evidence_stabilization_plan",
            17,
            125,
            "plan_run",
            "targeted_evidence_stabilization_plan.json",
        ),
        ("phase_16_closure", 16, 124, "phase16_run", "phase_16_closure.json"),
        (
            "baseline_gatekeeper_re_evaluation",
            16,
            123,
            "baseline_run",
            "gatekeeper_re_evaluation.json",
        ),
        (
            "pre_post_repair_comparison",
            16,
            122,
            "pre_post_run",
            "pre_post_repair_comparison.json",
        ),
        (
            "controlled_re_run_trial",
            16,
            121,
            "trial_run",
            "controlled_re_run_trial.json",
        ),
        (
            "research_audit_trail",
            15,
            118,
            "audit_run",
            "research_audit_trail_bundle.json",
        ),
    ]
    return {
        "gatekeeper_return_plan_run_id": "return_plan_run",
        "phase_17_closure_run_id": "closure_run",
        "gatekeeper_stabilization_re_review_run_id": "review_run",
        "gatekeeper_stabilized_comparison_run_id": "comparison_run",
        "stabilization_validation_run_id": "validation_run",
        "targeted_repair_run_id": "repair_run",
        "residual_work_order_package_run_id": "work_order_run",
        "stabilization_plan_run_id": "plan_run",
        "phase_16_closure_run_id": "phase16_run",
        "baseline_gatekeeper_re_evaluation_run_id": "baseline_run",
        "pre_post_repair_comparison_run_id": "pre_post_run",
        "controlled_re_run_trial_run_id": "trial_run",
        "re_run_input_package_run_id": "input_run",
        "re_run_re_gate_plan_run_id": "regate_plan_run",
        "research_audit_trail_run_id": "audit_run",
        "gatekeeper_return_plan_summary": {
            "final_gatekeeper_stabilization_outcome": "hold_with_stabilization_progress",
            "final_progression_status": "gatekeeper_return_package_only",
            "final_persona_review_status": "false",
        },
        "return_package_component_matrix": [
            {
                "component_code": code,
                "component_label": code.replace("_", " "),
                "component_purpose": f"{code} purpose",
                "source_artifacts": "Phase 17 closure and linked local artifacts",
                "required_inputs": "Task 132 planned inputs",
                "expected_output": "component input inventory",
                "inclusion_status": "included_with_warnings"
                if code == "next_gatekeeper_review_questions"
                else "included",
                "safety_boundary": "Planning component only.",
            }
            for code in components
        ],
        "return_package_evidence_inventory_matrix": [
            {
                "evidence_code": code,
                "evidence_label": code.replace("_", " "),
                "source_phase": phase,
                "source_task": task,
                "source_run_id": run_id,
                "source_artifact": artifact,
                "evidence_role_in_return_package": "source evidence",
                "inclusion_status": "included",
                "limitation_note": "local artifact only",
                "safety_boundary": "Evidence inventory only.",
            }
            for code, phase, task, run_id, artifact in evidence
        ],
        "safety_notice": "Task 132 safety notice.",
    }


def _write_artifact(outputs_root: Path, code: str, run_id: str) -> None:
    folder_name, stem = ARTIFACT_MAP[code]
    folder = outputs_root / folder_name / run_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{stem}.json").write_text("{}", encoding="utf-8")
    (folder / f"{stem}.md").write_text("# report", encoding="utf-8")


def _write_fixture(outputs_root: Path) -> Path:
    plan = _plan()
    _write_artifact(
        outputs_root,
        "gatekeeper_return_package_plan",
        plan["gatekeeper_return_plan_run_id"],
    )
    for evidence in plan["return_package_evidence_inventory_matrix"]:
        _write_artifact(outputs_root, evidence["evidence_code"], evidence["source_run_id"])
    for code, run_id_key in [
        ("re_run_input_package", "re_run_input_package_run_id"),
        ("re_run_re_gate_plan", "re_run_re_gate_plan_run_id"),
    ]:
        _write_artifact(outputs_root, code, plan[run_id_key])
    plan_dir = (
        outputs_root
        / "gatekeeper_return_package_plans"
        / plan["gatekeeper_return_plan_run_id"]
    )
    plan_path = plan_dir / "gatekeeper_return_package_plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    (outputs_root / "gatekeeper_return_package_plans").mkdir(exist_ok=True)
    (
        outputs_root
        / "gatekeeper_return_package_plans"
        / "latest_gatekeeper_return_package_plan_manifest.json"
    ).write_text(
        json.dumps(
            {
                "gatekeeper_return_plan_run_id": plan["gatekeeper_return_plan_run_id"],
                "report_json_path": str(plan_path),
            }
        ),
        encoding="utf-8",
    )
    return outputs_root


def _codes(rows: list[dict], key: str) -> set[str]:
    return {str(row[key]) for row in rows}


def test_loads_latest_return_plan_manifest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_gatekeeper_return_package_plan_manifest(outputs_root=outputs_root)

    assert manifest["gatekeeper_return_plan_run_id"] == "return_plan_run"


def test_loads_explicit_return_plan_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    manifest = load_gatekeeper_return_package_plan_manifest(
        outputs_root=outputs_root,
        gatekeeper_return_plan_run_id="return_plan_run",
    )
    report = load_gatekeeper_return_package_plan(
        outputs_root=outputs_root,
        gatekeeper_return_plan_run_id="return_plan_run",
    )

    assert manifest["gatekeeper_return_plan_run_id"] == "return_plan_run"
    assert report["gatekeeper_return_plan_run_id"] == "return_plan_run"


def test_handles_missing_return_plan_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_gatekeeper_return_package_plan_manifest(outputs_root=tmp_path)


def test_handles_missing_return_plan_report(tmp_path: Path) -> None:
    root = tmp_path / "gatekeeper_return_package_plans"
    root.mkdir()
    (root / "latest_gatekeeper_return_package_plan_manifest.json").write_text(
        json.dumps({"gatekeeper_return_plan_run_id": "missing"}),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        load_gatekeeper_return_package_plan(
            outputs_root=tmp_path,
            gatekeeper_return_plan_run_id="missing",
        )


def test_input_inventory_summary_is_created(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    plan = _plan()
    components = build_component_input_inventory_matrix(plan)
    evidence = build_evidence_artifact_inventory_matrix(
        outputs_root=outputs_root,
        plan=plan,
    )

    summary = build_input_inventory_summary(
        gatekeeper_return_input_inventory_run_id="inventory_run",
        plan=plan,
        component_rows=components,
        evidence_rows=evidence,
    )

    assert summary["phase_id"] == 18
    assert summary["current_task_id"] == 133
    assert summary["final_gatekeeper_stabilization_outcome"] == (
        "hold_with_stabilization_progress"
    )
    assert summary["final_progression_status"] == "gatekeeper_return_package_only"
    assert summary["final_persona_review_status"] == "false"
    assert summary["inventory_status"] in {"completed", "completed_with_warnings"}
    assert summary["recommended_next_task"].startswith("Task 134")


def test_component_input_inventory_has_required_components() -> None:
    rows = build_component_input_inventory_matrix(_plan())
    codes = _codes(rows, "component_code")

    assert "executive_gatekeeper_return_summary" in codes
    assert "final_gatekeeper_stabilization_decision_record" in codes
    assert "permission_boundary_summary" in codes
    assert "blocker_disposition_summary" in codes
    assert "residual_risk_disclosure" in codes
    assert "evidence_stabilization_timeline" in codes
    assert "repaired_evidence_inventory" in codes
    assert "validation_evidence_inventory" in codes
    assert "comparison_evidence_inventory" in codes
    assert "local_artifact_limitation_disclosure" in codes
    assert "no_persona_review_confirmation" in codes
    assert "no_investor_agent_execution_confirmation" in codes
    assert "no_recommendation_output_confirmation" in codes
    assert "auto_promotion_disabled_confirmation" in codes


def test_evidence_artifact_inventory_has_required_sources(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    rows = build_evidence_artifact_inventory_matrix(outputs_root=outputs_root, plan=_plan())
    codes = _codes(rows, "evidence_code")

    assert "phase_17_closure" in codes
    assert "gatekeeper_stabilization_re_review" in codes
    assert "gatekeeper_stabilized_evidence_comparison" in codes
    assert "stabilization_validation_trial" in codes
    assert "targeted_evidence_repairs" in codes
    assert "residual_blocker_work_orders" in codes
    assert "targeted_evidence_stabilization_plan" in codes
    assert "phase_16_closure" in codes
    assert "baseline_gatekeeper_re_evaluation" in codes
    assert "pre_post_repair_comparison" in codes
    assert "controlled_re_run_trial" in codes
    assert "research_audit_trail" in codes
    assert all(row["artifact_exists"] for row in rows)


def test_source_run_traceability_has_required_sources(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    rows = build_source_run_traceability_matrix(outputs_root=outputs_root, plan=_plan())
    codes = _codes(rows, "trace_code")

    assert "gatekeeper_return_package_plan" in codes
    assert "phase_17_closure" in codes
    assert "gatekeeper_stabilization_re_review" in codes
    assert "gatekeeper_stabilized_evidence_comparison" in codes
    assert "stabilization_validation_trial" in codes
    assert "targeted_evidence_repairs" in codes
    assert "residual_blocker_work_orders" in codes
    assert "baseline_gatekeeper_re_evaluation" in codes
    assert "research_audit_trail" in codes


def test_missing_or_warning_matrix_has_required_issues(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    plan = _plan()
    components = build_component_input_inventory_matrix(plan)
    evidence = build_evidence_artifact_inventory_matrix(
        outputs_root=outputs_root,
        plan=plan,
    )
    rows = build_missing_or_warning_input_matrix(
        component_rows=components,
        evidence_rows=evidence,
        plan=plan,
    )
    types = _codes(rows, "issue_type")

    assert "local_artifact_limitation" in types
    assert "unresolved_material_blocker" in types
    assert "persona_review_not_allowed" in types
    assert "investor_agent_execution_not_allowed" in types
    assert "auto_promotion_disabled" in types
    assert "gatekeeper_return_package_only_scope" in types


def test_package_assembly_readiness_matrix_has_required_items(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    plan = _plan()
    components = build_component_input_inventory_matrix(plan)
    evidence = build_evidence_artifact_inventory_matrix(
        outputs_root=outputs_root,
        plan=plan,
    )
    rows = build_package_assembly_readiness_matrix(
        component_rows=components,
        evidence_rows=evidence,
    )
    codes = _codes(rows, "readiness_code")

    assert "component_inventory_available" in codes
    assert "evidence_artifact_inventory_available" in codes
    assert "source_run_traceability_available" in codes
    assert "residual_risk_disclosures_available" in codes
    assert "permission_boundaries_available" in codes
    assert "package_assembly_inputs_ready" in codes
    assert "persona_review_block_preserved" in codes
    assert "investor_agent_block_preserved" in codes
    assert "no_recommendations_preserved" in codes
    assert "auto_promotion_disabled_preserved" in codes


def test_task_134_handoff_manifest_is_created(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    plan = _plan()
    components = build_component_input_inventory_matrix(plan)
    evidence = build_evidence_artifact_inventory_matrix(
        outputs_root=outputs_root,
        plan=plan,
    )
    missing = build_missing_or_warning_input_matrix(
        component_rows=components,
        evidence_rows=evidence,
        plan=plan,
    )
    readiness = build_package_assembly_readiness_matrix(
        component_rows=components,
        evidence_rows=evidence,
    )
    handoff = build_task_134_handoff_manifest(
        gatekeeper_return_input_inventory_run_id="inventory_run",
        plan=plan,
        component_rows=components,
        evidence_rows=evidence,
        missing_rows=missing,
        readiness_rows=readiness,
    )

    assert handoff["future_phase_id"] == 18
    assert handoff["future_task_id"] == 134
    assert handoff["readiness_status"] in {
        "ready_to_assemble_gatekeeper_return_package",
        "ready_with_warnings",
    }
    assert handoff["execution_allowed_now"] is True
    assert "investor agent execution" in handoff["prohibited_outputs"]
    assert "actual persona reviews" in handoff["prohibited_outputs"]
    assert "recommendations" in handoff["prohibited_outputs"]


def test_validation_checks_are_created() -> None:
    rows = build_gatekeeper_return_input_inventory_checks()
    codes = _codes(rows, "check_code")

    assert "final_gatekeeper_stabilization_outcome_preserved" in codes
    assert "final_progression_status_preserved" in codes
    assert "final_persona_review_status_preserved" in codes
    assert "gatekeeper_return_package_only_preserved" in codes
    assert "actual_persona_review_not_allowed" in codes
    assert "investor_agents_not_allowed" in codes
    assert "no_recommendation_outputs" in codes
    assert "auto_promotion_disabled" in codes
    assert all(row["status"] == "satisfied" for row in rows)


def test_build_input_inventory_report_has_sections(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    report = build_gatekeeper_return_input_inventory(
        gatekeeper_return_input_inventory_run_id="inventory_run",
        generated_at="2026-06-19T00:00:00+00:00",
        outputs_root=outputs_root,
        plan=_plan(),
    )
    data = report.to_dict()

    assert data["input_inventory_summary"]
    assert data["component_input_inventory_matrix"]
    assert data["evidence_artifact_inventory_matrix"]
    assert data["source_run_traceability_matrix"]
    assert data["missing_or_warning_input_matrix"]
    assert data["package_assembly_readiness_matrix"]
    assert data["task_134_handoff_manifest"]
    assert data["gatekeeper_return_input_inventory_checks"]


def test_write_input_inventory_report_writes_files(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)

    files = write_gatekeeper_return_input_inventory_report(
        outputs_root=outputs_root,
        gatekeeper_return_plan_run_id="return_plan_run",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.component_csv_path.is_file()
    assert files.evidence_csv_path.is_file()
    assert files.traceability_csv_path.is_file()
    assert files.missing_warning_csv_path.is_file()
    assert files.readiness_csv_path.is_file()
    assert files.task_134_handoff_manifest_path.is_file()
    assert files.checks_csv_path.is_file()
    assert files.latest_manifest_path.is_file()
    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Where We Are Now" in markdown
    assert "## Component Input Inventory Matrix" in markdown
    assert "## Evidence Artifact Inventory Matrix" in markdown
    assert "## Source Run Traceability Matrix" in markdown
    assert "## Missing or Warning Input Matrix" in markdown
    assert "## Package Assembly Readiness Matrix" in markdown
    assert "## Task 134 Handoff" in markdown
    assert "## What This Does Not Suggest" in markdown


def test_cli_works_with_explicit_return_plan_run_id(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "build-gatekeeper-return-input-inventory",
            "--gatekeeper-return-plan-run-id",
            "return_plan_run",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "gatekeeper_return_input_inventory_run_id=" in result.output
    assert "gatekeeper_return_plan_run_id=return_plan_run" in result.output
    assert "current_phase=18 - Gatekeeper Return Package Layer" in result.output
    assert "recommended_next_task=Task 134" in result.output


def test_cli_works_with_auto_latest(tmp_path: Path) -> None:
    outputs_root = _write_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "build-gatekeeper-return-input-inventory",
            "--auto-latest",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "gatekeeper_return_plan_run_id=return_plan_run" in result.output
    assert "status=completed_with_warnings" in result.output
