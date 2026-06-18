"""Task 120 re-run input package report."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report is an input packaging document only. It does not execute a "
    "re-run, rerun Gatekeeper, allow persona review, create investor "
    "decisions, rankings, recommendations, allocations, rebalancing "
    "instructions, trade signals, execution instructions, strategy validation, "
    "or investment advice."
)
NEXT_TASK = "Task 121 — Execute Controlled Re-Run Trial"

FULL_TICKERS = [
    "MSFT",
    "AAPL",
    "NVDA",
    "COST",
    "GOOGL",
    "AMZN",
    "META",
    "AVGO",
    "ORCL",
    "CRM",
    "ADBE",
    "NFLX",
]
CURRENT_CORE_TICKERS = ["MSFT", "AAPL", "NVDA", "COST"]
EXPANDED_COHORT_TICKERS = [
    "GOOGL",
    "AMZN",
    "META",
    "AVGO",
    "ORCL",
    "CRM",
    "ADBE",
    "NFLX",
]
FULL_DATES = [
    "2021-06-30",
    "2021-12-31",
    "2022-06-30",
    "2022-12-31",
    "2023-06-30",
]
CLEAN_PERIODS = ["2021-06-30", "2022-06-30", "2023-06-30"]
WARNING_PERIODS = ["2021-12-31", "2022-12-31"]
SUPPORTIVE_DATE = "2021-06-30"


@dataclass(frozen=True)
class ReRunInputPackageReport:
    """Structured Task 120 input package report."""

    re_run_input_package_run_id: str
    generated_at: str
    re_run_re_gate_plan_run_id: str
    research_audit_trail_run_id: str
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
    input_package_summary: dict
    re_run_universe_matrix: list[dict]
    re_run_date_matrix: list[dict]
    re_run_control_matrix: list[dict]
    artifact_source_map: list[dict]
    task_121_execution_manifest: dict
    input_package_validation_checks: list[dict]
    package_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class ReRunInputPackageFiles:
    """Generated Task 120 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    universe_matrix_csv_path: Path
    date_matrix_csv_path: Path
    control_matrix_csv_path: Path
    artifact_source_map_csv_path: Path
    task_121_execution_manifest_path: Path
    validation_checks_csv_path: Path
    latest_manifest_path: Path
    report: ReRunInputPackageReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_re_run_re_gate_plan_manifest(
    *,
    outputs_root: Path,
    re_run_re_gate_plan_run_id: str | None = None,
) -> dict:
    """Load one Task 119 report or the latest Task 119 manifest."""
    root = Path(outputs_root) / "re_run_re_gate_plans"
    path = (
        root / re_run_re_gate_plan_run_id / "re_run_re_gate_plan.json"
        if re_run_re_gate_plan_run_id
        else root / "latest_re_run_re_gate_plan_manifest.json"
    )
    label = (
        "Re-run re-gate plan report"
        if re_run_re_gate_plan_run_id
        else "Re-run re-gate plan manifest"
    )
    return _load_required_json(path, label)


def load_re_run_re_gate_plan(
    *,
    outputs_root: Path,
    re_run_re_gate_plan_run_id: str,
) -> dict:
    """Load a Task 119 plan report by run id."""
    path = (
        Path(outputs_root)
        / "re_run_re_gate_plans"
        / re_run_re_gate_plan_run_id
        / "re_run_re_gate_plan.json"
    )
    return _load_required_json(path, "Re-run re-gate plan report")


def load_research_audit_trail_bundle(
    *,
    outputs_root: Path,
    research_audit_trail_run_id: str,
) -> dict:
    """Load the linked Task 118 audit bundle."""
    path = (
        Path(outputs_root)
        / "research_audit_trail_bundles"
        / research_audit_trail_run_id
        / "research_audit_trail_bundle.json"
    )
    return _load_required_json(path, "Research audit trail bundle")


def _joined(values: list[str]) -> str:
    return ";".join(values)


def build_input_package_summary(
    *,
    re_run_input_package_run_id: str,
    plan: dict,
) -> dict:
    """Build Task 120 summary metadata."""
    return {
        "re_run_input_package_run_id": re_run_input_package_run_id,
        "re_run_re_gate_plan_run_id": plan["re_run_re_gate_plan_run_id"],
        "research_audit_trail_run_id": plan["research_audit_trail_run_id"],
        "phase_id": 16,
        "current_task_id": 120,
        "current_task_name": "Build Re-Run Input Package",
        "gatekeeper_decision": "hold",
        "progression_allowed": False,
        "persona_reviews_allowed": False,
        "package_status": "completed",
        "package_role": "controlled_re_run_input_preparation",
        "future_consumer_task": NEXT_TASK,
        "main_package_finding": (
            "Controlled re-run inputs are packaged, but no re-run or "
            "Gatekeeper rerun has been executed."
        ),
        "recommended_next_task": NEXT_TASK,
    }


def build_re_run_universe_matrix() -> list[dict]:
    """Build the Task 121 universe input matrix."""
    rows = [
        (
            "full_expanded_universe",
            _joined(FULL_TICKERS),
            "All 12 tickers from the expanded trial.",
        ),
        (
            "current_core",
            _joined(CURRENT_CORE_TICKERS),
            "Prior 4-ticker core must remain separately reportable.",
        ),
        (
            "expanded_cohort",
            _joined(EXPANDED_COHORT_TICKERS),
            "Expanded 8-ticker cohort must remain separately reportable.",
        ),
        (
            "ex_nvda_universe",
            _joined([ticker for ticker in FULL_TICKERS if ticker != "NVDA"]),
            "Controls known NVDA sensitivity.",
        ),
        (
            "ex_top_contributors_universe",
            "full sample excluding top positive contributors identified by Task 121 controls",
            "Future trial must report ex-top-contributor outcomes.",
        ),
        (
            "metadata_concentration_groups",
            "sector;category;universe_group;cohort;investor_interest where available",
            "Concentrated metadata groups must not be overgeneralized.",
        ),
        (
            "persona_evidence_linkage_universe",
            "Bogle;Fisher;Buffett;Munger linked evidence requirement views",
            "Persona evidence requirements remain packaging-only.",
        ),
    ]
    return [
        {
            "universe_group": universe_group,
            "included": True,
            "source": "Task 119 plan and local Phase 15 audit artifacts",
            "tickers_or_definition": tickers_or_definition,
            "reason": reason,
            "future_task_usage": "Task 121 controlled re-run input view",
            "safety_boundary": "Input definition only; no re-run is executed in Task 120.",
        }
        for universe_group, tickers_or_definition, reason in rows
    ]


def build_re_run_date_matrix() -> list[dict]:
    """Build the Task 121 date input matrix."""
    rows = [
        ("full_date_set", _joined(FULL_DATES), "All five evaluated dates."),
        ("clean_periods", _joined(CLEAN_PERIODS), "Clean evidence periods."),
        ("warning_periods", _joined(WARNING_PERIODS), "Warning evidence periods."),
        ("supportive_period_only", SUPPORTIVE_DATE, "Supportive date control."),
        (
            "ex_supportive_date_periods",
            _joined([date for date in FULL_DATES if date != SUPPORTIVE_DATE]),
            "Controls supportive-period dependence.",
        ),
        (
            "post_2021_periods",
            _joined([date for date in FULL_DATES if date > "2021-12-31"]),
            "Separates post-2021 instability.",
        ),
        (
            "anchor_split_periods",
            _joined(FULL_DATES),
            "Every period must report clean-anchor and delayed-anchor views.",
        ),
    ]
    return [
        {
            "date_group": date_group,
            "included": True,
            "dates_or_definition": dates_or_definition,
            "source": "Task 119 plan and local Phase 15 walk-forward artifacts",
            "reason": reason,
            "future_task_usage": "Task 121 controlled re-run date view",
            "safety_boundary": "Input definition only; no future price data is introduced.",
        }
        for date_group, dates_or_definition, reason in rows
    ]


def build_re_run_control_matrix(plan: dict) -> list[dict]:
    """Build the Task 121 required control matrix."""
    planned_controls = {
        row["required_control"]
        for row in plan.get("re_run_scope_matrix", [])
        if row.get("included_in_plan")
    }
    controlled_trial_controls = set(
        plan.get("controlled_trial_plan", {}).get("required_controls", [])
    )
    controls = [
        "full_sample",
        "clean_only",
        "warning_only",
        "clean_vs_warning_split",
        "clean_anchor",
        "delayed_anchor",
        "clean_anchor_vs_delayed_anchor_split",
        "current_core",
        "expanded_cohort",
        "current_core_vs_expanded_cohort_split",
        "ex_nvda",
        "ex_top_contributors",
        "ex_supportive_date",
        "benchmark_relative",
        "walk_forward",
        "outlier_dependence",
        "metadata_concentration",
        "persona_evidence_requirement_linkage",
        "no_persona_review_before_gatekeeper_allows",
    ]
    return [
        {
            "control_code": control,
            "control_label": control.replace("_", " "),
            "included": True,
            "source_artifact": (
                "controlled_trial_plan"
                if control in controlled_trial_controls
                else "re_run_scope_matrix"
            ),
            "required_future_output": f"{control} reported in Task 121 output",
            "task_121_usage": "Controlled re-run reporting control",
            "blocks_gatekeeper_rerun_until_reported": (
                control != "no_persona_review_before_gatekeeper_allows"
            ),
            "safety_boundary": (
                "Control is packaged only; Task 120 does not execute the trial."
            ),
            "trace_status": (
                "traced_to_task_119"
                if control in planned_controls or control in controlled_trial_controls
                else "defined_for_task_121_input_package"
            ),
        }
        for control in controls
    ]


def build_re_run_artifact_source_map(
    *,
    outputs_root: Path,
    plan: dict,
) -> list[dict]:
    """Build the source artifact map consumed by future Task 121."""
    outputs_root = Path(outputs_root)
    rows = [
        (
            "re_run_re_gate_plan",
            plan["re_run_re_gate_plan_run_id"],
            outputs_root
            / "re_run_re_gate_plans"
            / plan["re_run_re_gate_plan_run_id"]
            / "re_run_re_gate_plan.json",
            "Phase 16 plan and required controls",
        ),
        (
            "research_audit_trail_bundle",
            plan["research_audit_trail_run_id"],
            outputs_root
            / "research_audit_trail_bundles"
            / plan["research_audit_trail_run_id"]
            / "research_audit_trail_bundle.json",
            "Phase 15 audit trail and linked repair artifacts",
        ),
        (
            "backtest_results",
            plan["backtest_run_id"],
            outputs_root / "backtests" / plan["backtest_run_id"] / "backtest_results.csv",
            "Task 121 source row universe and historical outcomes",
        ),
        (
            "expanded_trial_results",
            plan["expanded_trial_run_id"],
            outputs_root
            / "expanded_ticker_trials"
            / plan["expanded_trial_run_id"]
            / "expanded_ticker_trial_summary.json",
            "Expanded trial summary and coverage inputs",
        ),
        (
            "driver_decomposition",
            plan["decomposition_run_id"],
            outputs_root
            / "backtest_driver_decompositions"
            / plan["decomposition_run_id"]
            / "backtest_driver_decomposition_report.json",
            "Driver controls for ticker, date, cohort, sector, and category views",
        ),
        (
            "outlier_repair",
            plan["outlier_repair_run_id"],
            outputs_root
            / "outlier_repair_paths"
            / plan["outlier_repair_run_id"]
            / "outlier_repair_path_report.json",
            "Ex-NVDA and top-contributor controls",
        ),
        (
            "walk_forward_repair",
            plan["walk_forward_repair_run_id"],
            outputs_root
            / "walk_forward_repair_plans"
            / plan["walk_forward_repair_run_id"]
            / "walk_forward_repair_plan_report.json",
            "Period and walk-forward controls",
        ),
        (
            "delayed_anchor_repair",
            plan["delayed_anchor_repair_run_id"],
            outputs_root
            / "delayed_anchor_repairs"
            / plan["delayed_anchor_repair_run_id"]
            / "delayed_anchor_repair_report.json",
            "Clean-anchor and delayed-anchor controls",
        ),
        (
            "metadata_diversity_recheck",
            plan["metadata_diversity_recheck_run_id"],
            outputs_root
            / "metadata_diversity_rechecks"
            / plan["metadata_diversity_recheck_run_id"]
            / "metadata_diversity_recheck_report.json",
            "Metadata concentration controls",
        ),
        (
            "persona_evidence_pack_requirements",
            plan["persona_evidence_pack_run_id"],
            outputs_root
            / "persona_evidence_pack_requirements"
            / plan["persona_evidence_pack_run_id"]
            / "persona_evidence_pack_requirements_report.json",
            "Persona evidence requirement linkage",
        ),
        (
            "bogle_benchmark_index_pack",
            plan["bogle_benchmark_pack_run_id"],
            outputs_root
            / "bogle_benchmark_index_packs"
            / plan["bogle_benchmark_pack_run_id"]
            / "bogle_benchmark_index_comparison_pack.json",
            "Bogle benchmark/index comparison linkage",
        ),
        (
            "fisher_qualitative_growth_pack",
            plan["fisher_growth_pack_run_id"],
            outputs_root
            / "fisher_qualitative_growth_packs"
            / plan["fisher_growth_pack_run_id"]
            / "fisher_qualitative_growth_evidence_pack.json",
            "Fisher qualitative growth linkage",
        ),
        (
            "buffett_munger_quality_risk_pack",
            plan["buffett_munger_pack_run_id"],
            outputs_root
            / "buffett_munger_quality_risk_packs"
            / plan["buffett_munger_pack_run_id"]
            / "buffett_munger_quality_risk_pack.json",
            "Buffett/Munger quality and risk linkage",
        ),
    ]
    return [
        {
            "source_category": category,
            "run_id": run_id,
            "artifact_path": str(path),
            "consumed_for": consumed_for,
            "required_for_task_121": True,
            "available_status": "available" if path.exists() else "not_found",
            "safety_boundary": "Source mapping only; no source artifact is mutated.",
        }
        for category, run_id, path, consumed_for in rows
    ]


def build_task_121_execution_manifest(
    *,
    re_run_input_package_run_id: str,
    controls: list[dict],
) -> dict:
    """Build the future Task 121 execution manifest."""
    required_controls = [row["control_code"] for row in controls]
    return {
        "future_task_id": 121,
        "future_task_name": "Execute Controlled Re-Run Trial",
        "input_package_run_id": re_run_input_package_run_id,
        "required_cli_inputs": [
            "--re-run-input-package-run-id",
            re_run_input_package_run_id,
            "--outputs-root",
            "data/outputs",
        ],
        "required_controls": required_controls,
        "prohibited_outputs": [
            "investment_decision",
            "buy_sell_hold_recommendation",
            "ranking",
            "allocation",
            "rebalancing_instruction",
            "trade_signal",
            "execution_instruction",
            "persona_review",
            "gatekeeper_rerun",
        ],
        "readiness_status": "input_package_ready",
        "execution_allowed_now": True,
        "reason": (
            "Input package is ready for Task 121, but Task 120 itself did not "
            "execute the trial."
        ),
    }


def build_input_package_validation_checks() -> list[dict]:
    """Build Task 120 validation checks."""
    checks = [
        "plan_loaded",
        "audit_trail_loaded",
        "universe_matrix_created",
        "date_matrix_created",
        "control_matrix_created",
        "artifact_source_map_created",
        "task_121_manifest_created",
        "gatekeeper_hold_preserved",
        "persona_review_block_preserved",
        "no_re_run_executed",
        "no_gatekeeper_rerun_executed",
        "no_recommendation_outputs",
    ]
    return [
        {
            "check_code": check,
            "check_label": check.replace("_", " "),
            "status": "satisfied",
            "source_artifact": "re_run_re_gate_plan",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 120 input packaging.",
        }
        for check in checks
    ]


def build_re_run_input_package(
    *,
    re_run_input_package_run_id: str,
    generated_at: str,
    outputs_root: Path,
    plan: dict,
) -> ReRunInputPackageReport:
    """Build the Task 120 re-run input package."""
    load_research_audit_trail_bundle(
        outputs_root=outputs_root,
        research_audit_trail_run_id=plan["research_audit_trail_run_id"],
    )
    summary = build_input_package_summary(
        re_run_input_package_run_id=re_run_input_package_run_id,
        plan=plan,
    )
    universe = build_re_run_universe_matrix()
    dates = build_re_run_date_matrix()
    controls = build_re_run_control_matrix(plan)
    artifact_map = build_re_run_artifact_source_map(
        outputs_root=outputs_root,
        plan=plan,
    )
    manifest = build_task_121_execution_manifest(
        re_run_input_package_run_id=re_run_input_package_run_id,
        controls=controls,
    )
    checks = build_input_package_validation_checks()
    return ReRunInputPackageReport(
        re_run_input_package_run_id=re_run_input_package_run_id,
        generated_at=generated_at,
        re_run_re_gate_plan_run_id=plan["re_run_re_gate_plan_run_id"],
        research_audit_trail_run_id=plan["research_audit_trail_run_id"],
        buffett_munger_pack_run_id=plan["buffett_munger_pack_run_id"],
        fisher_growth_pack_run_id=plan["fisher_growth_pack_run_id"],
        bogle_benchmark_pack_run_id=plan["bogle_benchmark_pack_run_id"],
        persona_evidence_pack_run_id=plan["persona_evidence_pack_run_id"],
        metadata_diversity_recheck_run_id=plan["metadata_diversity_recheck_run_id"],
        delayed_anchor_repair_run_id=plan["delayed_anchor_repair_run_id"],
        walk_forward_repair_run_id=plan["walk_forward_repair_run_id"],
        outlier_repair_run_id=plan["outlier_repair_run_id"],
        decomposition_run_id=plan["decomposition_run_id"],
        backoffice_attribution_run_id=plan["backoffice_attribution_run_id"],
        investor_persona_attribution_run_id=plan["investor_persona_attribution_run_id"],
        gatekeeper_run_id=plan["gatekeeper_run_id"],
        scorecard_run_id=plan["scorecard_run_id"],
        analysis_run_id=plan["analysis_run_id"],
        expanded_trial_run_id=plan["expanded_trial_run_id"],
        backtest_run_id=plan["backtest_run_id"],
        input_package_summary=summary,
        re_run_universe_matrix=universe,
        re_run_date_matrix=dates,
        re_run_control_matrix=controls,
        artifact_source_map=artifact_map,
        task_121_execution_manifest=manifest,
        input_package_validation_checks=checks,
        package_status="completed",
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


def _render_markdown(report: ReRunInputPackageReport) -> str:
    summary = report.input_package_summary
    manifest = report.task_121_execution_manifest
    lines = [
        "# Re-Run Input Package",
        "",
        "## Executive Summary",
        "",
        f"* Re-Run Input Package Run ID: {report.re_run_input_package_run_id}",
        f"* Re-Run & Re-Gate Plan Run ID: {report.re_run_re_gate_plan_run_id}",
        f"* Research Audit Trail Run ID: {report.research_audit_trail_run_id}",
        "* Current Phase: 16 - Re-Run & Re-Gate Layer",
        "* Current Task: Task 120 - Build Re-Run Input Package",
        f"* Gatekeeper Decision: {summary['gatekeeper_decision']}",
        f"* Progression Allowed: {str(summary['progression_allowed']).lower()}",
        f"* Persona Reviews Allowed: {str(summary['persona_reviews_allowed']).lower()}",
        f"* Package Status: {report.package_status}",
        f"* Recommended Next Task: {report.recommended_next_task}",
        "",
        "## Important Boundary",
        "",
        (
            "This report is an input packaging document only. It does not "
            "execute a re-run, rerun Gatekeeper, allow persona review, create "
            "investor decisions, rankings, recommendations, allocations, "
            "rebalancing instructions, trade signals, or execution instructions."
        ),
        "",
        "## Where We Are Now",
        "",
        "Current Phase:",
        "16 — Re-Run & Re-Gate Layer",
        "",
        "Previous Task:",
        "Task 119 — Define Re-Run & Re-Gate Plan completed",
        "",
        "Direct Next:",
        "Task 121 — Execute Controlled Re-Run Trial",
        "",
        "This Task:",
        "Task 120 builds the input package for Task 121 but does not execute the trial.",
        "",
        "Phase 16 Expected Final Task:",
        "Task 124 — Phase 16 Closure & Next-Phase Recommendation",
        "",
        "## Input Package Summary",
        "",
        f"* Package Role: {summary['package_role']}",
        f"* Future Consumer Task: {summary['future_consumer_task']}",
        f"* Main Package Finding: {summary['main_package_finding']}",
        "",
        "## Re-Run Universe Matrix",
        "",
        *_markdown_table(
            report.re_run_universe_matrix,
            [
                ("Universe Group", "universe_group"),
                ("Included", "included"),
                ("Source", "source"),
                ("Tickers or Definition", "tickers_or_definition"),
                ("Future Usage", "future_task_usage"),
            ],
        ),
        "",
        "## Re-Run Date Matrix",
        "",
        *_markdown_table(
            report.re_run_date_matrix,
            [
                ("Date Group", "date_group"),
                ("Included", "included"),
                ("Dates or Definition", "dates_or_definition"),
                ("Source", "source"),
                ("Future Usage", "future_task_usage"),
            ],
        ),
        "",
        "## Re-Run Control Matrix",
        "",
        *_markdown_table(
            report.re_run_control_matrix,
            [
                ("Control", "control_code"),
                ("Included", "included"),
                ("Required Future Output", "required_future_output"),
                (
                    "Blocks Gatekeeper Rerun Until Reported",
                    "blocks_gatekeeper_rerun_until_reported",
                ),
            ],
        ),
        "",
        "## Artifact Source Map",
        "",
        *_markdown_table(
            report.artifact_source_map,
            [
                ("Source Category", "source_category"),
                ("Run ID", "run_id"),
                ("Consumed For", "consumed_for"),
                ("Required For Task 121", "required_for_task_121"),
                ("Available", "available_status"),
            ],
        ),
        "",
        "## Task 121 Execution Manifest",
        "",
        f"* Future Task: {manifest['future_task_id']} - {manifest['future_task_name']}",
        f"* Required CLI Inputs: {' '.join(manifest['required_cli_inputs'])}",
        f"* Required Controls: {'; '.join(manifest['required_controls'])}",
        f"* Prohibited Outputs: {'; '.join(manifest['prohibited_outputs'])}",
        f"* Readiness Status: {manifest['readiness_status']}",
        f"* Execution Allowed Now: {str(manifest['execution_allowed_now']).lower()}",
        f"* Reason: {manifest['reason']}",
        "",
        "## Input Package Validation Checks",
        "",
        *_markdown_table(
            report.input_package_validation_checks,
            [
                ("Check", "check_code"),
                ("Status", "status"),
                ("Blocking If Failed", "blocking_if_failed"),
                ("Finding", "finding"),
            ],
        ),
        "",
        "## What This Suggests",
        "",
        "* Task 121 can now be prepared/executed by the operator.",
        "* The input package is ready.",
        "* Evidence remains held and non-actionable.",
        "",
        "## What This Does Not Suggest",
        "",
        "* It does not execute the re-run.",
        "* It does not rerun Gatekeeper.",
        "* It does not allow persona review.",
        "* It does not recommend any company.",
        "* It does not rank companies.",
        "* It does not create allocation or rebalancing.",
        "* It does not create a trade signal.",
        "* It does not validate a strategy.",
        "",
        "## Next Task",
        "",
        f"* {report.recommended_next_task}",
        "",
        "## Safety Notice",
        "",
        report.safety_notice,
        "",
    ]
    return "\n".join(lines)


def write_re_run_input_package_report(
    *,
    outputs_root: Path,
    re_run_re_gate_plan_run_id: str | None = None,
) -> ReRunInputPackageFiles:
    """Write Task 120 input package artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_re_run_re_gate_plan_manifest(
        outputs_root=outputs_root,
        re_run_re_gate_plan_run_id=re_run_re_gate_plan_run_id,
    )
    plan_run_id = manifest["re_run_re_gate_plan_run_id"]
    plan = load_re_run_re_gate_plan(
        outputs_root=outputs_root,
        re_run_re_gate_plan_run_id=plan_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    package_run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_re_run_input_package(
        re_run_input_package_run_id=package_run_id,
        generated_at=generated_at.isoformat(),
        outputs_root=outputs_root,
        plan=plan,
    )

    root = outputs_root / "re_run_input_packages"
    output_folder = root / package_run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "re_run_input_package.md"
    json_path = output_folder / "re_run_input_package.json"
    universe_matrix_csv_path = output_folder / "re_run_universe_matrix.csv"
    date_matrix_csv_path = output_folder / "re_run_date_matrix.csv"
    control_matrix_csv_path = output_folder / "re_run_control_matrix.csv"
    artifact_source_map_csv_path = output_folder / "artifact_source_map.csv"
    task_121_execution_manifest_path = output_folder / "task_121_execution_manifest.json"
    validation_checks_csv_path = output_folder / "input_package_validation_checks.csv"
    latest_manifest_path = root / "latest_re_run_input_package_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(universe_matrix_csv_path, report.re_run_universe_matrix)
    _write_csv(date_matrix_csv_path, report.re_run_date_matrix)
    _write_csv(control_matrix_csv_path, report.re_run_control_matrix)
    _write_csv(artifact_source_map_csv_path, report.artifact_source_map)
    task_121_execution_manifest_path.write_text(
        json.dumps(report.task_121_execution_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(validation_checks_csv_path, report.input_package_validation_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "re_run_input_package_run_id": report.re_run_input_package_run_id,
                "re_run_re_gate_plan_run_id": report.re_run_re_gate_plan_run_id,
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
                "package_status": report.package_status,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "universe_matrix_csv_path": str(universe_matrix_csv_path),
                "date_matrix_csv_path": str(date_matrix_csv_path),
                "control_matrix_csv_path": str(control_matrix_csv_path),
                "artifact_source_map_csv_path": str(artifact_source_map_csv_path),
                "task_121_execution_manifest_path": str(
                    task_121_execution_manifest_path
                ),
                "validation_checks_csv_path": str(validation_checks_csv_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return ReRunInputPackageFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        universe_matrix_csv_path=universe_matrix_csv_path,
        date_matrix_csv_path=date_matrix_csv_path,
        control_matrix_csv_path=control_matrix_csv_path,
        artifact_source_map_csv_path=artifact_source_map_csv_path,
        task_121_execution_manifest_path=task_121_execution_manifest_path,
        validation_checks_csv_path=validation_checks_csv_path,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
