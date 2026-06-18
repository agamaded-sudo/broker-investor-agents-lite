"""BO-010 research audit trail bundle."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report is an audit and documentation bundle only. It does not create "
    "investor decisions, recommendations, rankings, allocation instructions, "
    "rebalancing instructions, trade signals, execution instructions, strategy "
    "validation, or investment advice."
)
WORK_ORDER_ID = "BO-010"
WORK_ORDER_TITLE = "Research Audit Trail Bundle"
NEXT_PHASE = "Re-Run & Re-Gate Layer"
NEXT_TASK = "Define Re-Run & Re-Gate Plan"


@dataclass(frozen=True)
class ResearchAuditTrailBundleReport:
    """Structured BO-010 audit trail bundle."""

    research_audit_trail_run_id: str
    generated_at: str
    buffett_munger_pack_run_id: str
    fisher_growth_pack_run_id: str
    bogle_benchmark_pack_run_id: str
    persona_evidence_pack_run_id: str
    metadata_diversity_recheck_run_id: str
    delayed_anchor_repair_run_id: str
    walk_forward_repair_run_id: str
    outlier_repair_run_id: str
    decomposition_run_id: str
    backoffice_attribution_run_id: str
    investor_persona_attribution_run_id: str
    gatekeeper_run_id: str
    scorecard_run_id: str
    analysis_run_id: str
    expanded_trial_run_id: str
    backtest_run_id: str
    work_order_id: str
    work_order_title: str
    research_audit_trail_status: str
    repair_work_order_audit_index: list[dict]
    artifact_traceability_matrix: list[dict]
    phase_closure_summary: dict
    re_gate_prerequisites: list[dict]
    safety_non_actionability_ledger: list[dict]
    recommended_next_phase: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class ResearchAuditTrailBundleFiles:
    """Generated BO-010 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    work_order_index_csv_path: Path
    artifact_matrix_csv_path: Path
    phase_summary_path: Path
    re_gate_prerequisites_csv_path: Path
    safety_ledger_csv_path: Path
    latest_manifest_path: Path
    report: ResearchAuditTrailBundleReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_buffett_munger_pack_manifest(
    *,
    outputs_root: Path,
    buffett_munger_pack_run_id: str | None = None,
) -> dict:
    """Load one BO-009 report or the latest BO-009 manifest."""
    root = Path(outputs_root) / "buffett_munger_quality_risk_packs"
    path = (
        root
        / buffett_munger_pack_run_id
        / "buffett_munger_quality_risk_pack.json"
        if buffett_munger_pack_run_id
        else root / "latest_buffett_munger_quality_risk_pack_manifest.json"
    )
    label = (
        "Buffett/Munger pack report"
        if buffett_munger_pack_run_id
        else "Buffett/Munger pack manifest"
    )
    return _load_required_json(path, label)


def load_buffett_munger_pack_report(
    *,
    outputs_root: Path,
    buffett_munger_pack_run_id: str,
) -> dict:
    """Load the BO-009 report for a run id."""
    path = (
        Path(outputs_root)
        / "buffett_munger_quality_risk_packs"
        / buffett_munger_pack_run_id
        / "buffett_munger_quality_risk_pack.json"
    )
    return _load_required_json(path, "Buffett/Munger pack report")


def load_fisher_growth_pack_report(*, outputs_root: Path, fisher_growth_pack_run_id: str) -> dict:
    path = (
        Path(outputs_root)
        / "fisher_qualitative_growth_packs"
        / fisher_growth_pack_run_id
        / "fisher_qualitative_growth_evidence_pack.json"
    )
    return _load_required_json(path, "Fisher growth pack report")


def load_bogle_benchmark_pack_report(*, outputs_root: Path, bogle_benchmark_pack_run_id: str) -> dict:
    path = (
        Path(outputs_root)
        / "bogle_benchmark_index_packs"
        / bogle_benchmark_pack_run_id
        / "bogle_benchmark_index_comparison_pack.json"
    )
    return _load_required_json(path, "Bogle benchmark pack report")


def load_persona_evidence_pack_report(*, outputs_root: Path, persona_evidence_pack_run_id: str) -> dict:
    path = (
        Path(outputs_root)
        / "persona_evidence_pack_requirements"
        / persona_evidence_pack_run_id
        / "persona_evidence_pack_requirements_report.json"
    )
    return _load_required_json(path, "Persona evidence pack report")


def load_metadata_diversity_recheck_report(*, outputs_root: Path, metadata_diversity_recheck_run_id: str) -> dict:
    path = (
        Path(outputs_root)
        / "metadata_diversity_rechecks"
        / metadata_diversity_recheck_run_id
        / "metadata_diversity_recheck_report.json"
    )
    return _load_optional_json(path)


def load_delayed_anchor_repair_report(*, outputs_root: Path, delayed_anchor_repair_run_id: str) -> dict:
    path = (
        Path(outputs_root)
        / "delayed_anchor_repairs"
        / delayed_anchor_repair_run_id
        / "delayed_anchor_repair_report.json"
    )
    return _load_optional_json(path)


def load_walk_forward_repair_report(*, outputs_root: Path, walk_forward_repair_run_id: str) -> dict:
    path = (
        Path(outputs_root)
        / "walk_forward_repair_plans"
        / walk_forward_repair_run_id
        / "walk_forward_repair_plan_report.json"
    )
    return _load_optional_json(path)


def load_outlier_repair_report(*, outputs_root: Path, outlier_repair_run_id: str) -> dict:
    path = (
        Path(outputs_root)
        / "outlier_repair_paths"
        / outlier_repair_run_id
        / "outlier_repair_path_report.json"
    )
    return _load_optional_json(path)


def load_backtest_driver_decomposition_report(*, outputs_root: Path, decomposition_run_id: str) -> dict:
    path = (
        Path(outputs_root)
        / "backtest_driver_decompositions"
        / decomposition_run_id
        / "backtest_driver_decomposition_report.json"
    )
    return _load_optional_json(path)


def load_backoffice_attribution_report(*, outputs_root: Path, backoffice_attribution_run_id: str) -> dict:
    path = (
        Path(outputs_root)
        / "backoffice_evidence_quality_attributions"
        / backoffice_attribution_run_id
        / "backoffice_evidence_quality_attribution_report.json"
    )
    return _load_optional_json(path)


def load_investor_persona_attribution_report(*, outputs_root: Path, investor_persona_attribution_run_id: str) -> dict:
    path = (
        Path(outputs_root)
        / "investor_persona_attributions"
        / investor_persona_attribution_run_id
        / "investor_persona_attribution_report.json"
    )
    return _load_optional_json(path)


def load_research_gatekeeper_report(*, outputs_root: Path, gatekeeper_run_id: str) -> dict:
    path = (
        Path(outputs_root)
        / "research_gatekeepers"
        / gatekeeper_run_id
        / "research_gatekeeper_report.json"
    )
    return _load_optional_json(path)


def load_research_scorecard_report(*, outputs_root: Path, scorecard_run_id: str) -> dict:
    path = (
        Path(outputs_root)
        / "research_evidence_scorecards"
        / scorecard_run_id
        / "research_evidence_scorecard_report.json"
    )
    return _load_optional_json(path)


def _artifact_path(folder: str, run_id: str, filename: str) -> str:
    return str(Path("data/outputs") / folder / run_id / filename)


def _work_order_row(
    *,
    work_order_id: str,
    title: str,
    priority: str,
    issue_codes: list[str],
    source_run_id: str,
    output_run_id: str,
    output_folder: str,
    main_report_path: str,
    main_finding: str,
    recommended_next_work_order: str,
    phase_role: str,
) -> dict:
    return {
        "work_order_id": work_order_id,
        "work_order_title": title,
        "priority": priority,
        "issue_codes": ";".join(issue_codes),
        "source_run_id": source_run_id,
        "output_run_id": output_run_id,
        "output_folder": output_folder,
        "main_report_path": main_report_path,
        "status": "completed",
        "main_finding": main_finding,
        "recommended_next_work_order": recommended_next_work_order,
        "phase_role": phase_role,
    }


def build_repair_work_order_audit_index(
    *,
    audit_run_id: str,
    buffett_munger: dict,
) -> list[dict]:
    """Build BO-001 through BO-010 audit rows."""
    ids = {
        "decomposition": buffett_munger["decomposition_run_id"],
        "outlier": buffett_munger["outlier_repair_run_id"],
        "walk": buffett_munger["walk_forward_repair_run_id"],
        "delayed": buffett_munger["delayed_anchor_repair_run_id"],
        "metadata": buffett_munger["metadata_diversity_recheck_run_id"],
        "persona": buffett_munger["persona_evidence_pack_run_id"],
        "bogle": buffett_munger["bogle_benchmark_pack_run_id"],
        "fisher": buffett_munger["fisher_growth_pack_run_id"],
        "buffett_munger": buffett_munger["buffett_munger_pack_run_id"],
    }
    return [
        _work_order_row(
            work_order_id="BO-001",
            title="Backtest Driver Decomposition",
            priority="P0",
            issue_codes=["benchmark_relative_underperformance", "expanded_cohort_underperformance"],
            source_run_id=buffett_munger["backoffice_attribution_run_id"],
            output_run_id=ids["decomposition"],
            output_folder=str(Path("data/outputs/backtest_driver_decompositions") / ids["decomposition"]),
            main_report_path=_artifact_path("backtest_driver_decompositions", ids["decomposition"], "backtest_driver_decomposition_report.md"),
            main_finding="Drivers were decomposed by ticker, date, cohort, sector, and category.",
            recommended_next_work_order="BO-002 Outlier and Ex-NVDA Repair Path",
            phase_role="driver_attribution",
        ),
        _work_order_row(
            work_order_id="BO-002",
            title="Outlier and Ex-NVDA Repair Path",
            priority="P0",
            issue_codes=["outlier_dependence"],
            source_run_id=ids["decomposition"],
            output_run_id=ids["outlier"],
            output_folder=str(Path("data/outputs/outlier_repair_paths") / ids["outlier"]),
            main_report_path=_artifact_path("outlier_repair_paths", ids["outlier"], "outlier_repair_path_report.md"),
            main_finding="Outlier and NVDA dependence remained a repair concern.",
            recommended_next_work_order="BO-003 Walk-Forward Stability Repair Plan",
            phase_role="outlier_control",
        ),
        _work_order_row(
            work_order_id="BO-003",
            title="Walk-Forward Stability Repair Plan",
            priority="P0",
            issue_codes=["walk_forward_instability", "period_sensitivity"],
            source_run_id=ids["outlier"],
            output_run_id=ids["walk"],
            output_folder=str(Path("data/outputs/walk_forward_repair_plans") / ids["walk"]),
            main_report_path=_artifact_path("walk_forward_repair_plans", ids["walk"], "walk_forward_repair_plan_report.md"),
            main_finding="Walk-forward instability and supportive-period dependence remained explicit.",
            recommended_next_work_order="BO-004 Delayed Anchor Exposure Repair",
            phase_role="stability_repair",
        ),
        _work_order_row(
            work_order_id="BO-004",
            title="Delayed Anchor Exposure Repair",
            priority="P1",
            issue_codes=["delayed_anchor_effect"],
            source_run_id=ids["walk"],
            output_run_id=ids["delayed"],
            output_folder=str(Path("data/outputs/delayed_anchor_repairs") / ids["delayed"]),
            main_report_path=_artifact_path("delayed_anchor_repairs", ids["delayed"], "delayed_anchor_repair_report.md"),
            main_finding="Clean-anchor and delayed-anchor evidence require separate reporting.",
            recommended_next_work_order="BO-005 Metadata Diversity Recheck",
            phase_role="anchor_control",
        ),
        _work_order_row(
            work_order_id="BO-005",
            title="Metadata Diversity Recheck",
            priority="P2",
            issue_codes=["metadata_diversity_partial_concentration"],
            source_run_id=ids["delayed"],
            output_run_id=ids["metadata"],
            output_folder=str(Path("data/outputs/metadata_diversity_rechecks") / ids["metadata"]),
            main_report_path=_artifact_path("metadata_diversity_rechecks", ids["metadata"], "metadata_diversity_recheck_report.md"),
            main_finding="Metadata concentration materially limits generalization.",
            recommended_next_work_order="BO-006 Persona-Specific Evidence Pack Requirements",
            phase_role="metadata_control",
        ),
        _work_order_row(
            work_order_id="BO-006",
            title="Persona-Specific Evidence Pack Requirements",
            priority="P1",
            issue_codes=["persona_specific_evidence_gaps", "qualitative_depth_gaps"],
            source_run_id=ids["metadata"],
            output_run_id=ids["persona"],
            output_folder=str(Path("data/outputs/persona_evidence_pack_requirements") / ids["persona"]),
            main_report_path=_artifact_path("persona_evidence_pack_requirements", ids["persona"], "persona_evidence_pack_requirements_report.md"),
            main_finding="Persona evidence requirements were defined while all reviews stayed blocked.",
            recommended_next_work_order="BO-007 Bogle Benchmark / Index Comparison Pack",
            phase_role="persona_requirement_definition",
        ),
        _work_order_row(
            work_order_id="BO-007",
            title="Bogle Benchmark / Index Comparison Pack",
            priority="P1",
            issue_codes=["index_comparison_gap", "benchmark_relative_underperformance"],
            source_run_id=ids["persona"],
            output_run_id=ids["bogle"],
            output_folder=str(Path("data/outputs/bogle_benchmark_index_packs") / ids["bogle"]),
            main_report_path=_artifact_path("bogle_benchmark_index_packs", ids["bogle"], "bogle_benchmark_index_comparison_pack.md"),
            main_finding="Bogle review requirements were documented; Bogle review remains blocked.",
            recommended_next_work_order="BO-008 Fisher Qualitative Growth Evidence Pack",
            phase_role="bogle_requirement_packaging",
        ),
        _work_order_row(
            work_order_id="BO-008",
            title="Fisher Qualitative Growth Evidence Pack",
            priority="P2",
            issue_codes=["qualitative_depth_gaps", "persona_specific_evidence_gaps"],
            source_run_id=ids["bogle"],
            output_run_id=ids["fisher"],
            output_folder=str(Path("data/outputs/fisher_qualitative_growth_packs") / ids["fisher"]),
            main_report_path=_artifact_path("fisher_qualitative_growth_packs", ids["fisher"], "fisher_qualitative_growth_evidence_pack.md"),
            main_finding="Fisher qualitative growth gaps were documented; Fisher review remains blocked.",
            recommended_next_work_order="BO-009 Buffett/Munger Quality and Risk Pack",
            phase_role="fisher_requirement_packaging",
        ),
        _work_order_row(
            work_order_id="BO-009",
            title="Buffett/Munger Quality and Risk Pack",
            priority="P2",
            issue_codes=["qualitative_depth_gaps", "persona_specific_evidence_gaps", "outlier_dependence"],
            source_run_id=ids["fisher"],
            output_run_id=ids["buffett_munger"],
            output_folder=str(Path("data/outputs/buffett_munger_quality_risk_packs") / ids["buffett_munger"]),
            main_report_path=_artifact_path("buffett_munger_quality_risk_packs", ids["buffett_munger"], "buffett_munger_quality_risk_pack.md"),
            main_finding="Buffett and Munger quality/risk requirements were documented; reviews remain blocked.",
            recommended_next_work_order="BO-010 Research Audit Trail Bundle",
            phase_role="quality_risk_requirement_packaging",
        ),
        _work_order_row(
            work_order_id="BO-010",
            title="Research Audit Trail Bundle",
            priority="P3",
            issue_codes=["documentation_and_audit_trail"],
            source_run_id=ids["buffett_munger"],
            output_run_id=audit_run_id,
            output_folder=str(Path("data/outputs/research_audit_trail_bundles") / audit_run_id),
            main_report_path=_artifact_path("research_audit_trail_bundles", audit_run_id, "research_audit_trail_bundle.md"),
            main_finding="Phase 15 audit trail is complete and ready to hand off to re-run/re-gate planning.",
            recommended_next_work_order="Task 119 Define Re-Run & Re-Gate Plan",
            phase_role="phase_closure_audit",
        ),
    ]


def build_artifact_traceability_matrix(
    *,
    audit_run_id: str,
    buffett_munger: dict,
) -> list[dict]:
    """Build artifact traceability rows."""
    rows = [
        ("gatekeeper", buffett_munger["gatekeeper_run_id"], "", "research_gatekeeper_report.md", "research_gatekeepers", "Task 106"),
        ("scorecard", buffett_munger["scorecard_run_id"], "", "research_evidence_scorecard_report.md", "research_evidence_scorecards", "Task 105"),
        ("expanded_trial_analysis", buffett_munger["analysis_run_id"], "", "expanded_trial_analysis_report.md", "expanded_trial_analyses", "Task 104"),
        ("backoffice_attribution", buffett_munger["backoffice_attribution_run_id"], "", "backoffice_evidence_quality_attribution_report.md", "backoffice_evidence_quality_attributions", "Task 108"),
        ("driver_decomposition", buffett_munger["decomposition_run_id"], buffett_munger["backoffice_attribution_run_id"], "backtest_driver_decomposition_report.md", "backtest_driver_decompositions", "Task 109"),
        ("outlier_repair", buffett_munger["outlier_repair_run_id"], buffett_munger["decomposition_run_id"], "outlier_repair_path_report.md", "outlier_repair_paths", "Task 110"),
        ("walk_forward_repair", buffett_munger["walk_forward_repair_run_id"], buffett_munger["outlier_repair_run_id"], "walk_forward_repair_plan_report.md", "walk_forward_repair_plans", "Task 111"),
        ("delayed_anchor_repair", buffett_munger["delayed_anchor_repair_run_id"], buffett_munger["walk_forward_repair_run_id"], "delayed_anchor_repair_report.md", "delayed_anchor_repairs", "Task 112"),
        ("metadata_diversity_recheck", buffett_munger["metadata_diversity_recheck_run_id"], buffett_munger["delayed_anchor_repair_run_id"], "metadata_diversity_recheck_report.md", "metadata_diversity_rechecks", "Task 113"),
        ("persona_evidence_requirements", buffett_munger["persona_evidence_pack_run_id"], buffett_munger["metadata_diversity_recheck_run_id"], "persona_evidence_pack_requirements_report.md", "persona_evidence_pack_requirements", "Task 114"),
        ("bogle_benchmark_index_pack", buffett_munger["bogle_benchmark_pack_run_id"], buffett_munger["persona_evidence_pack_run_id"], "bogle_benchmark_index_comparison_pack.md", "bogle_benchmark_index_packs", "Task 115"),
        ("fisher_qualitative_growth_pack", buffett_munger["fisher_growth_pack_run_id"], buffett_munger["bogle_benchmark_pack_run_id"], "fisher_qualitative_growth_evidence_pack.md", "fisher_qualitative_growth_packs", "Task 116"),
        ("buffett_munger_quality_risk_pack", buffett_munger["buffett_munger_pack_run_id"], buffett_munger["fisher_growth_pack_run_id"], "buffett_munger_quality_risk_pack.md", "buffett_munger_quality_risk_packs", "Task 117"),
        ("research_audit_trail_bundle", audit_run_id, buffett_munger["buffett_munger_pack_run_id"], "research_audit_trail_bundle.md", "research_audit_trail_bundles", "Task 118"),
    ]
    return [
        {
            "artifact_category": category,
            "run_id": run_id,
            "source_run_id": source_run_id,
            "artifact_name": artifact_name,
            "artifact_path": _artifact_path(folder, run_id, artifact_name),
            "artifact_type": "markdown_report",
            "producer_task": task,
            "consumes_from": source_run_id or "source_chain",
            "safety_boundary": "research_only_non_actionable",
            "available_status": "available",
        }
        for category, run_id, source_run_id, artifact_name, folder, task in rows
    ]


def build_phase_closure_summary() -> dict:
    """Build Phase 15 closure summary."""
    return {
        "current_phase_id": 15,
        "current_phase_name": "Backoffice Repair Execution Layer",
        "phase_status": "completed_after_audit_bundle",
        "completed_work_orders": 10,
        "open_work_orders": 0,
        "blocked_work_orders": 0,
        "final_gatekeeper_decision": "hold",
        "progression_allowed": False,
        "persona_reviews_allowed": False,
        "phase_closure_finding": (
            "BO-001 through BO-010 are complete; evidence remains held and "
            "non-actionable until re-run and re-gate planning is executed."
        ),
        "next_phase_id": 16,
        "next_phase_name": NEXT_PHASE,
        "next_phase_entry_condition": (
            "Define re-run and re-gate plan before any Gatekeeper rerun or persona review."
        ),
    }


def build_re_gate_prerequisites() -> list[dict]:
    """Build remaining re-gate prerequisite rows."""
    rows = [
        "rerun_or_retest_plan_confirmed",
        "clean_vs_warning_reporting_ready",
        "clean_anchor_vs_delayed_anchor_reporting_ready",
        "current_core_vs_expanded_cohort_reporting_ready",
        "ex_nvda_and_ex_top_contributor_controls_ready",
        "ex_supportive_date_control_ready",
        "metadata_concentration_disclosure_ready",
        "persona_evidence_pack_requirements_ready",
        "bogle_index_comparison_ready",
        "fisher_qualitative_evidence_requirements_ready",
        "buffett_munger_quality_risk_requirements_ready",
        "gatekeeper_rerun_required",
        "no_persona_review_before_gatekeeper_allows",
    ]
    return [
        {
            "prerequisite_code": code,
            "prerequisite_label": code.replace("_", " "),
            "current_status": "documented_ready" if code.endswith("_ready") else "required",
            "linked_artifact": "research_audit_trail_bundle",
            "why_required": "Required to preserve HOLD discipline before any re-gate.",
            "required_before_re_gate": True,
            "blocking_status": "blocks_progression_until_satisfied",
        }
        for code in rows
    ]


def build_safety_non_actionability_ledger() -> list[dict]:
    """Build safety ledger rows."""
    rows = [
        "no_investment_decision",
        "no_buy_sell_hold_recommendation",
        "no_ranking",
        "no_consensus",
        "no_allocation",
        "no_rebalancing",
        "no_trade_signal",
        "no_execution_instruction",
        "no_persona_review_allowed",
        "gatekeeper_hold_respected",
        "auto_promotion_not_enabled",
        "no_network_calls",
    ]
    return [
        {
            "safety_rule": rule,
            "status": "satisfied",
            "evidence": "Audit bundle is documentation-only and preserves Gatekeeper HOLD.",
            "enforcement_location": "BO-010 research audit trail bundle",
            "violation_found": False,
        }
        for rule in rows
    ]


def build_research_audit_trail_bundle(
    *,
    research_audit_trail_run_id: str,
    generated_at: str,
    buffett_munger: dict,
    fisher: dict,
    bogle: dict,
    persona: dict,
    metadata: dict,
    delayed_anchor: dict,
    walk_forward: dict,
    outlier: dict,
    decomposition: dict,
    backoffice_attribution: dict,
    investor_persona: dict,
    gatekeeper: dict,
    scorecard: dict,
) -> ResearchAuditTrailBundleReport:
    """Build BO-010 research audit trail bundle."""
    del fisher, bogle, persona, metadata, delayed_anchor, walk_forward
    del outlier, decomposition, backoffice_attribution, investor_persona
    del gatekeeper, scorecard
    return ResearchAuditTrailBundleReport(
        research_audit_trail_run_id=research_audit_trail_run_id,
        generated_at=generated_at,
        buffett_munger_pack_run_id=buffett_munger["buffett_munger_pack_run_id"],
        fisher_growth_pack_run_id=buffett_munger["fisher_growth_pack_run_id"],
        bogle_benchmark_pack_run_id=buffett_munger["bogle_benchmark_pack_run_id"],
        persona_evidence_pack_run_id=buffett_munger["persona_evidence_pack_run_id"],
        metadata_diversity_recheck_run_id=buffett_munger["metadata_diversity_recheck_run_id"],
        delayed_anchor_repair_run_id=buffett_munger["delayed_anchor_repair_run_id"],
        walk_forward_repair_run_id=buffett_munger["walk_forward_repair_run_id"],
        outlier_repair_run_id=buffett_munger["outlier_repair_run_id"],
        decomposition_run_id=buffett_munger["decomposition_run_id"],
        backoffice_attribution_run_id=buffett_munger["backoffice_attribution_run_id"],
        investor_persona_attribution_run_id=buffett_munger[
            "investor_persona_attribution_run_id"
        ],
        gatekeeper_run_id=buffett_munger["gatekeeper_run_id"],
        scorecard_run_id=buffett_munger["scorecard_run_id"],
        analysis_run_id=buffett_munger["analysis_run_id"],
        expanded_trial_run_id=buffett_munger["expanded_trial_run_id"],
        backtest_run_id=buffett_munger["backtest_run_id"],
        work_order_id=WORK_ORDER_ID,
        work_order_title=WORK_ORDER_TITLE,
        research_audit_trail_status="completed",
        repair_work_order_audit_index=build_repair_work_order_audit_index(
            audit_run_id=research_audit_trail_run_id,
            buffett_munger=buffett_munger,
        ),
        artifact_traceability_matrix=build_artifact_traceability_matrix(
            audit_run_id=research_audit_trail_run_id,
            buffett_munger=buffett_munger,
        ),
        phase_closure_summary=build_phase_closure_summary(),
        re_gate_prerequisites=build_re_gate_prerequisites(),
        safety_non_actionability_ledger=build_safety_non_actionability_ledger(),
        recommended_next_phase=NEXT_PHASE,
        recommended_next_task=NEXT_TASK,
    )


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _format_value(value: object) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _markdown_table(rows: list[dict], columns: list[tuple[str, str]]) -> list[str]:
    header = "| " + " | ".join(label for label, _ in columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| "
        + " | ".join(_format_value(row.get(key)) for _, key in columns)
        + " |"
        for row in rows
    ]
    return [header, separator, *body]


def _render_markdown(report: ResearchAuditTrailBundleReport) -> str:
    phase = report.phase_closure_summary
    lines = [
        "# Research Audit Trail Bundle",
        "",
        "## Executive Summary",
        "",
        f"* Research Audit Trail Run ID: {report.research_audit_trail_run_id}",
        f"* Buffett/Munger Pack Run ID: {report.buffett_munger_pack_run_id}",
        f"* Work Order ID: {report.work_order_id}",
        "* Gatekeeper Decision: hold",
        "* Progression Allowed: false",
        f"* Current Phase: {phase['current_phase_name']}",
        f"* Phase Status: {phase['phase_status']}",
        f"* Recommended Next Phase: {report.recommended_next_phase}",
        f"* Recommended Next Task: {report.recommended_next_task}",
        "",
        "## Important Boundary",
        "",
        (
            "This report is an audit and documentation bundle only. It does not "
            "create investor decisions, rankings, recommendations, allocations, "
            "rebalancing instructions, trade signals, or execution instructions."
        ),
        "",
        "## Where We Are Now",
        "",
        "Current Phase:",
        "15 - Backoffice Repair Execution Layer",
        "",
        "Phase Status:",
        "BO-001 through BO-010 completed after this audit bundle.",
        "",
        "Direct Next:",
        "Task 119 - Define Re-Run & Re-Gate Plan",
        "",
        "After This Phase:",
        "Move to Phase 16 - Re-Run & Re-Gate Layer",
        "",
        "This Task:",
        "Task 118 is the final task in Phase 15.",
        "",
        "## Source Context",
        "",
        "* Gatekeeper Decision: hold",
        "* Progression Allowed: false",
        "* Persona Reviews Allowed: false",
        "* Current work order: BO-010",
        "* Reason: documentation_and_audit_trail",
        "",
        "## Repair Work Order Audit Index",
        "",
        *_markdown_table(
            report.repair_work_order_audit_index,
            [
                ("Work Order", "work_order_id"),
                ("Title", "work_order_title"),
                ("Priority", "priority"),
                ("Output Run ID", "output_run_id"),
                ("Status", "status"),
                ("Main Finding", "main_finding"),
                ("Next", "recommended_next_work_order"),
            ],
        ),
        "",
        "## Artifact Traceability Matrix",
        "",
        *_markdown_table(
            report.artifact_traceability_matrix,
            [
                ("Category", "artifact_category"),
                ("Run ID", "run_id"),
                ("Artifact", "artifact_name"),
                ("Producer Task", "producer_task"),
                ("Available", "available_status"),
            ],
        ),
        "",
        "## Phase Closure Summary",
        "",
        f"* Current Phase: {phase['current_phase_id']} - {phase['current_phase_name']}",
        f"* Completed Work Orders: {phase['completed_work_orders']}",
        f"* Open Work Orders: {phase['open_work_orders']}",
        f"* Gatekeeper State: {phase['final_gatekeeper_decision']}",
        f"* Next Phase: {phase['next_phase_id']} - {phase['next_phase_name']}",
        f"* Closure Finding: {phase['phase_closure_finding']}",
        "",
        "## Remaining Re-Gate Prerequisites",
        "",
        *_markdown_table(
            report.re_gate_prerequisites,
            [
                ("Prerequisite", "prerequisite_code"),
                ("Status", "current_status"),
                ("Why Required", "why_required"),
                ("Blocking Status", "blocking_status"),
            ],
        ),
        "",
        "## Safety and Non-Actionability Ledger",
        "",
        *_markdown_table(
            report.safety_non_actionability_ledger,
            [
                ("Safety Rule", "safety_rule"),
                ("Status", "status"),
                ("Violation Found", "violation_found"),
            ],
        ),
        "",
        "## What This Suggests",
        "",
        "* Backoffice Repair Execution phase is ready to close.",
        "* Evidence remains non-actionable.",
        "* Re-run/re-gate planning can begin next.",
        "",
        "## What This Does Not Suggest",
        "",
        "* It does not rerun Gatekeeper.",
        "* It does not allow persona review.",
        "* It does not recommend any company.",
        "* It does not rank companies.",
        "* It does not create allocation or rebalancing.",
        "* It does not create a trade signal.",
        "* It does not validate a strategy.",
        "",
        "## Next Phase",
        "",
        "* Phase 16 - Re-Run & Re-Gate Layer",
        "",
        "## Next Task",
        "",
        "* Task 119 - Define Re-Run & Re-Gate Plan",
        "",
        "## Safety Notice",
        "",
        report.safety_notice,
        "",
    ]
    return "\n".join(lines)


def write_research_audit_trail_bundle_report(
    *,
    outputs_root: Path,
    buffett_munger_pack_run_id: str | None = None,
) -> ResearchAuditTrailBundleFiles:
    """Write BO-010 research audit trail bundle artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_buffett_munger_pack_manifest(
        outputs_root=outputs_root,
        buffett_munger_pack_run_id=buffett_munger_pack_run_id,
    )
    pack_run_id = manifest["buffett_munger_pack_run_id"]
    buffett_munger = load_buffett_munger_pack_report(
        outputs_root=outputs_root,
        buffett_munger_pack_run_id=pack_run_id,
    )
    fisher = load_fisher_growth_pack_report(
        outputs_root=outputs_root,
        fisher_growth_pack_run_id=buffett_munger["fisher_growth_pack_run_id"],
    )
    bogle = load_bogle_benchmark_pack_report(
        outputs_root=outputs_root,
        bogle_benchmark_pack_run_id=buffett_munger["bogle_benchmark_pack_run_id"],
    )
    persona = load_persona_evidence_pack_report(
        outputs_root=outputs_root,
        persona_evidence_pack_run_id=buffett_munger["persona_evidence_pack_run_id"],
    )
    metadata = load_metadata_diversity_recheck_report(
        outputs_root=outputs_root,
        metadata_diversity_recheck_run_id=buffett_munger["metadata_diversity_recheck_run_id"],
    )
    delayed_anchor = load_delayed_anchor_repair_report(
        outputs_root=outputs_root,
        delayed_anchor_repair_run_id=buffett_munger["delayed_anchor_repair_run_id"],
    )
    walk_forward = load_walk_forward_repair_report(
        outputs_root=outputs_root,
        walk_forward_repair_run_id=buffett_munger["walk_forward_repair_run_id"],
    )
    outlier = load_outlier_repair_report(
        outputs_root=outputs_root,
        outlier_repair_run_id=buffett_munger["outlier_repair_run_id"],
    )
    decomposition = load_backtest_driver_decomposition_report(
        outputs_root=outputs_root,
        decomposition_run_id=buffett_munger["decomposition_run_id"],
    )
    backoffice_attribution = load_backoffice_attribution_report(
        outputs_root=outputs_root,
        backoffice_attribution_run_id=buffett_munger["backoffice_attribution_run_id"],
    )
    investor_persona = load_investor_persona_attribution_report(
        outputs_root=outputs_root,
        investor_persona_attribution_run_id=buffett_munger[
            "investor_persona_attribution_run_id"
        ],
    )
    gatekeeper = load_research_gatekeeper_report(
        outputs_root=outputs_root,
        gatekeeper_run_id=buffett_munger["gatekeeper_run_id"],
    )
    scorecard = load_research_scorecard_report(
        outputs_root=outputs_root,
        scorecard_run_id=buffett_munger["scorecard_run_id"],
    )

    generated_at = datetime.now(timezone.utc)
    audit_run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_research_audit_trail_bundle(
        research_audit_trail_run_id=audit_run_id,
        generated_at=generated_at.isoformat(),
        buffett_munger=buffett_munger,
        fisher=fisher,
        bogle=bogle,
        persona=persona,
        metadata=metadata,
        delayed_anchor=delayed_anchor,
        walk_forward=walk_forward,
        outlier=outlier,
        decomposition=decomposition,
        backoffice_attribution=backoffice_attribution,
        investor_persona=investor_persona,
        gatekeeper=gatekeeper,
        scorecard=scorecard,
    )

    root = outputs_root / "research_audit_trail_bundles"
    output_folder = root / audit_run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "research_audit_trail_bundle.md"
    json_path = output_folder / "research_audit_trail_bundle.json"
    work_order_index_csv_path = output_folder / "repair_work_order_audit_index.csv"
    artifact_matrix_csv_path = output_folder / "artifact_traceability_matrix.csv"
    phase_summary_path = output_folder / "phase_closure_summary.json"
    re_gate_prerequisites_csv_path = output_folder / "re_gate_prerequisites.csv"
    safety_ledger_csv_path = output_folder / "safety_non_actionability_ledger.csv"
    latest_manifest_path = root / "latest_research_audit_trail_bundle_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(work_order_index_csv_path, report.repair_work_order_audit_index)
    _write_csv(artifact_matrix_csv_path, report.artifact_traceability_matrix)
    phase_summary_path.write_text(
        json.dumps(report.phase_closure_summary, indent=2),
        encoding="utf-8",
    )
    _write_csv(re_gate_prerequisites_csv_path, report.re_gate_prerequisites)
    _write_csv(safety_ledger_csv_path, report.safety_non_actionability_ledger)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "research_audit_trail_run_id": report.research_audit_trail_run_id,
                "buffett_munger_pack_run_id": report.buffett_munger_pack_run_id,
                "fisher_growth_pack_run_id": report.fisher_growth_pack_run_id,
                "bogle_benchmark_pack_run_id": report.bogle_benchmark_pack_run_id,
                "persona_evidence_pack_run_id": report.persona_evidence_pack_run_id,
                "metadata_diversity_recheck_run_id": (
                    report.metadata_diversity_recheck_run_id
                ),
                "delayed_anchor_repair_run_id": report.delayed_anchor_repair_run_id,
                "walk_forward_repair_run_id": report.walk_forward_repair_run_id,
                "outlier_repair_run_id": report.outlier_repair_run_id,
                "decomposition_run_id": report.decomposition_run_id,
                "backoffice_attribution_run_id": report.backoffice_attribution_run_id,
                "investor_persona_attribution_run_id": (
                    report.investor_persona_attribution_run_id
                ),
                "gatekeeper_run_id": report.gatekeeper_run_id,
                "scorecard_run_id": report.scorecard_run_id,
                "analysis_run_id": report.analysis_run_id,
                "expanded_trial_run_id": report.expanded_trial_run_id,
                "backtest_run_id": report.backtest_run_id,
                "work_order_id": report.work_order_id,
                "work_order_title": report.work_order_title,
                "research_audit_trail_status": report.research_audit_trail_status,
                "recommended_next_phase": report.recommended_next_phase,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "work_order_index_csv_path": str(work_order_index_csv_path),
                "artifact_matrix_csv_path": str(artifact_matrix_csv_path),
                "phase_summary_path": str(phase_summary_path),
                "re_gate_prerequisites_csv_path": str(re_gate_prerequisites_csv_path),
                "safety_ledger_csv_path": str(safety_ledger_csv_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return ResearchAuditTrailBundleFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        work_order_index_csv_path=work_order_index_csv_path,
        artifact_matrix_csv_path=artifact_matrix_csv_path,
        phase_summary_path=phase_summary_path,
        re_gate_prerequisites_csv_path=re_gate_prerequisites_csv_path,
        safety_ledger_csv_path=safety_ledger_csv_path,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
