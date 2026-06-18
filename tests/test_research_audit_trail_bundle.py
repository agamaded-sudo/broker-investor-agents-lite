"""Tests for BO-010 research audit trail bundle."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.backoffice.research_audit_trail_bundle import (
    build_artifact_traceability_matrix,
    build_phase_closure_summary,
    build_re_gate_prerequisites,
    build_repair_work_order_audit_index,
    build_research_audit_trail_bundle,
    build_safety_non_actionability_ledger,
    load_bogle_benchmark_pack_report,
    load_buffett_munger_pack_manifest,
    load_buffett_munger_pack_report,
    load_fisher_growth_pack_report,
    load_persona_evidence_pack_report,
    write_research_audit_trail_bundle_report,
)
from broker_agents.cli import app


def _buffett_munger_pack() -> dict:
    return {
        "buffett_munger_pack_run_id": "bm",
        "fisher_growth_pack_run_id": "fisher",
        "bogle_benchmark_pack_run_id": "bogle",
        "persona_evidence_pack_run_id": "persona_pack",
        "metadata_diversity_recheck_run_id": "metadata",
        "delayed_anchor_repair_run_id": "delayed",
        "walk_forward_repair_run_id": "walk",
        "outlier_repair_run_id": "outlier",
        "decomposition_run_id": "decomp",
        "backoffice_attribution_run_id": "backoffice",
        "investor_persona_attribution_run_id": "persona",
        "gatekeeper_run_id": "gatekeeper",
        "scorecard_run_id": "scorecard",
        "analysis_run_id": "analysis",
        "expanded_trial_run_id": "expanded",
        "backtest_run_id": "backtest",
    }


def _write_fixture(outputs: Path) -> None:
    bm_folder = outputs / "buffett_munger_quality_risk_packs" / "bm"
    bm_folder.mkdir(parents=True)
    (bm_folder / "buffett_munger_quality_risk_pack.json").write_text(
        json.dumps(_buffett_munger_pack()),
        encoding="utf-8",
    )
    (
        outputs
        / "buffett_munger_quality_risk_packs"
        / "latest_buffett_munger_quality_risk_pack_manifest.json"
    ).write_text(
        json.dumps({"buffett_munger_pack_run_id": "bm"}),
        encoding="utf-8",
    )
    linked = (
        (
            outputs / "fisher_qualitative_growth_packs" / "fisher",
            "fisher_qualitative_growth_evidence_pack.json",
            {"fisher_growth_pack_run_id": "fisher"},
        ),
        (
            outputs / "bogle_benchmark_index_packs" / "bogle",
            "bogle_benchmark_index_comparison_pack.json",
            {"bogle_benchmark_pack_run_id": "bogle"},
        ),
        (
            outputs / "persona_evidence_pack_requirements" / "persona_pack",
            "persona_evidence_pack_requirements_report.json",
            {"persona_evidence_pack_run_id": "persona_pack"},
        ),
        (
            outputs / "metadata_diversity_rechecks" / "metadata",
            "metadata_diversity_recheck_report.json",
            {"metadata_diversity_recheck_run_id": "metadata"},
        ),
        (
            outputs / "delayed_anchor_repairs" / "delayed",
            "delayed_anchor_repair_report.json",
            {"delayed_anchor_repair_run_id": "delayed"},
        ),
        (
            outputs / "walk_forward_repair_plans" / "walk",
            "walk_forward_repair_plan_report.json",
            {"walk_forward_repair_run_id": "walk"},
        ),
        (
            outputs / "outlier_repair_paths" / "outlier",
            "outlier_repair_path_report.json",
            {"outlier_repair_run_id": "outlier"},
        ),
        (
            outputs / "backtest_driver_decompositions" / "decomp",
            "backtest_driver_decomposition_report.json",
            {"decomposition_run_id": "decomp"},
        ),
        (
            outputs / "backoffice_evidence_quality_attributions" / "backoffice",
            "backoffice_evidence_quality_attribution_report.json",
            {"backoffice_attribution_run_id": "backoffice"},
        ),
        (
            outputs / "investor_persona_attributions" / "persona",
            "investor_persona_attribution_report.json",
            {"attribution_run_id": "persona"},
        ),
        (
            outputs / "research_gatekeepers" / "gatekeeper",
            "research_gatekeeper_report.json",
            {"gatekeeper_run_id": "gatekeeper"},
        ),
        (
            outputs / "research_evidence_scorecards" / "scorecard",
            "research_evidence_scorecard_report.json",
            {"scorecard_run_id": "scorecard"},
        ),
    )
    for folder, filename, payload in linked:
        folder.mkdir(parents=True)
        (folder / filename).write_text(json.dumps(payload), encoding="utf-8")


def test_loads_latest_and_explicit_buffett_munger_manifest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    latest = load_buffett_munger_pack_manifest(outputs_root=outputs)
    explicit = load_buffett_munger_pack_manifest(
        outputs_root=outputs,
        buffett_munger_pack_run_id="bm",
    )
    assert latest["buffett_munger_pack_run_id"] == "bm"
    assert explicit["backtest_run_id"] == "backtest"


def test_missing_buffett_munger_manifest_and_report_raise(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    with pytest.raises(FileNotFoundError, match="Buffett/Munger pack manifest"):
        load_buffett_munger_pack_manifest(outputs_root=outputs)
    _write_fixture(outputs)
    (
        outputs
        / "buffett_munger_quality_risk_packs"
        / "bm"
        / "buffett_munger_quality_risk_pack.json"
    ).unlink()
    with pytest.raises(FileNotFoundError, match="Buffett/Munger pack report"):
        write_research_audit_trail_bundle_report(outputs_root=outputs)


def test_loads_linked_reports(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    assert load_buffett_munger_pack_report(
        outputs_root=outputs, buffett_munger_pack_run_id="bm"
    )
    assert load_fisher_growth_pack_report(
        outputs_root=outputs, fisher_growth_pack_run_id="fisher"
    )
    assert load_bogle_benchmark_pack_report(
        outputs_root=outputs, bogle_benchmark_pack_run_id="bogle"
    )
    assert load_persona_evidence_pack_report(
        outputs_root=outputs, persona_evidence_pack_run_id="persona_pack"
    )


def test_repair_work_order_audit_index_includes_bo_001_through_bo_010() -> None:
    rows = build_repair_work_order_audit_index(
        audit_run_id="audit",
        buffett_munger=_buffett_munger_pack(),
    )
    ids = {row["work_order_id"] for row in rows}
    assert {f"BO-{index:03d}" for index in range(1, 11)} <= ids
    assert len(rows) == 10


def test_artifact_traceability_matrix_includes_required_categories() -> None:
    rows = build_artifact_traceability_matrix(
        audit_run_id="audit",
        buffett_munger=_buffett_munger_pack(),
    )
    categories = {row["artifact_category"] for row in rows}
    assert {
        "gatekeeper",
        "scorecard",
        "backoffice_attribution",
        "driver_decomposition",
        "outlier_repair",
        "walk_forward_repair",
        "delayed_anchor_repair",
        "metadata_diversity_recheck",
        "persona_evidence_requirements",
        "bogle_benchmark_index_pack",
        "fisher_qualitative_growth_pack",
        "buffett_munger_quality_risk_pack",
    } <= categories


def test_phase_closure_summary_marks_phase_15_complete_and_phase_16_next() -> None:
    summary = build_phase_closure_summary()
    assert summary["current_phase_id"] == 15
    assert summary["next_phase_id"] == 16
    assert summary["phase_status"] == "completed_after_audit_bundle"
    assert summary["completed_work_orders"] == 10
    assert summary["open_work_orders"] == 0


def test_re_gate_prerequisites_include_required_gatekeeper_blocks() -> None:
    codes = {row["prerequisite_code"] for row in build_re_gate_prerequisites()}
    assert "gatekeeper_rerun_required" in codes
    assert "no_persona_review_before_gatekeeper_allows" in codes


def test_safety_ledger_has_required_rules_and_no_violations() -> None:
    ledger = build_safety_non_actionability_ledger()
    rules = {row["safety_rule"] for row in ledger}
    assert {
        "no_investment_decision",
        "no_buy_sell_hold_recommendation",
        "no_ranking",
        "no_allocation",
        "no_trade_signal",
        "gatekeeper_hold_respected",
    } <= rules
    assert all(not row["violation_found"] for row in ledger)


def test_audit_bundle_json_sections_are_created() -> None:
    report = build_research_audit_trail_bundle(
        research_audit_trail_run_id="audit",
        generated_at="2026-06-18T00:00:00+00:00",
        buffett_munger=_buffett_munger_pack(),
        fisher={},
        bogle={},
        persona={},
        metadata={},
        delayed_anchor={},
        walk_forward={},
        outlier={},
        decomposition={},
        backoffice_attribution={},
        investor_persona={},
        gatekeeper={},
        scorecard={},
    )
    payload = report.to_dict()
    assert payload["repair_work_order_audit_index"]
    assert payload["artifact_traceability_matrix"]
    assert payload["phase_closure_summary"]
    assert payload["re_gate_prerequisites"]
    assert payload["safety_non_actionability_ledger"]


def test_writer_outputs_requested_files_and_latest_manifest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    files = write_research_audit_trail_bundle_report(
        outputs_root=outputs,
        buffett_munger_pack_run_id="bm",
    )
    for path in (
        files.markdown_path,
        files.json_path,
        files.work_order_index_csv_path,
        files.artifact_matrix_csv_path,
        files.phase_summary_path,
        files.re_gate_prerequisites_csv_path,
        files.safety_ledger_csv_path,
        files.latest_manifest_path,
    ):
        assert path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert payload["phase_closure_summary"]["phase_status"] == (
        "completed_after_audit_bundle"
    )
    markdown = files.markdown_path.read_text(encoding="utf-8")
    for section in (
        "Important Boundary",
        "Where We Are Now",
        "Repair Work Order Audit Index",
        "Artifact Traceability Matrix",
        "Phase Closure Summary",
        "Remaining Re-Gate Prerequisites",
        "Safety and Non-Actionability Ledger",
        "Next Phase",
    ):
        assert section in markdown


@pytest.mark.parametrize("auto_latest", [False, True])
def test_cli_explicit_and_auto_latest(tmp_path: Path, auto_latest: bool) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    args = [
        "build-research-audit-trail-bundle",
        "--outputs-root",
        str(outputs),
    ]
    if auto_latest:
        args.append("--auto-latest")
    else:
        args.extend(["--buffett-munger-pack-run-id", "bm"])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "Research Audit Trail Bundle" in result.output
    assert "gatekeeper_decision=hold" in result.output
    assert "progression_allowed=false" in result.output
    assert "phase_status=completed_after_audit_bundle" in result.output
    assert "recommended_next_phase=Re-Run & Re-Gate Layer" in result.output
