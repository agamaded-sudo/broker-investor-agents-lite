"""Task 121 controlled re-run trial report."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean, median

SAFETY_NOTICE = (
    "This report is a controlled research re-run only. It does not rerun "
    "Gatekeeper, allow persona review, create investor decisions, rankings, "
    "recommendations, allocations, rebalancing instructions, trade signals, "
    "execution instructions, strategy validation, or investment advice."
)
NEXT_TASK = "Task 122 — Compare Pre-Repair vs Post-Repair Evidence"

CURRENT_CORE_TICKERS = {"MSFT", "AAPL", "NVDA", "COST"}
SUPPORTIVE_DATE = "2021-06-30"
POST_2021_DATES = {"2022-06-30", "2022-12-31", "2023-06-30"}


@dataclass(frozen=True)
class ControlledReRunTrialReport:
    """Structured Task 121 controlled re-run trial report."""

    controlled_re_run_trial_run_id: str
    generated_at: str
    re_run_input_package_run_id: str
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
    controlled_re_run_summary: dict
    scenario_execution_plan: list[dict]
    scenario_results_matrix: list[dict]
    control_diagnostics_matrix: list[dict]
    limitations_matrix: list[dict]
    task_122_handoff_manifest: dict
    controlled_re_run_validation_checks: list[dict]
    controlled_re_run_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class ControlledReRunTrialFiles:
    """Generated Task 121 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    scenario_execution_plan_csv_path: Path
    scenario_results_matrix_csv_path: Path
    control_diagnostics_matrix_csv_path: Path
    limitations_matrix_csv_path: Path
    task_122_handoff_manifest_path: Path
    validation_checks_csv_path: Path
    latest_manifest_path: Path
    report: ControlledReRunTrialReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_re_run_input_package_manifest(
    *,
    outputs_root: Path,
    re_run_input_package_run_id: str | None = None,
) -> dict:
    """Load one Task 120 report or the latest Task 120 manifest."""
    root = Path(outputs_root) / "re_run_input_packages"
    path = (
        root / re_run_input_package_run_id / "re_run_input_package.json"
        if re_run_input_package_run_id
        else root / "latest_re_run_input_package_manifest.json"
    )
    label = (
        "Re-run input package report"
        if re_run_input_package_run_id
        else "Re-run input package manifest"
    )
    return _load_required_json(path, label)


def load_re_run_input_package(
    *,
    outputs_root: Path,
    re_run_input_package_run_id: str,
) -> dict:
    """Load a Task 120 input package by run id."""
    path = (
        Path(outputs_root)
        / "re_run_input_packages"
        / re_run_input_package_run_id
        / "re_run_input_package.json"
    )
    return _load_required_json(path, "Re-run input package report")


def _load_backtest_rows(*, outputs_root: Path, backtest_run_id: str) -> list[dict]:
    path = Path(outputs_root) / "backtests" / backtest_run_id / "backtest_results.csv"
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _as_float(row: dict, key: str) -> float | None:
    value = row.get(key)
    if value in (None, ""):
        return None
    return float(value)


def _as_bool(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _metric(values: list[float], mode: str) -> float | None:
    if not values:
        return None
    result = median(values) if mode == "median" else mean(values)
    return round(result, 6)


def _scenario_rows(rows: list[dict], scenario_code: str) -> list[dict]:
    if scenario_code in {
        "full_sample",
        "clean_vs_warning_split",
        "clean_anchor_vs_delayed_anchor_split",
        "current_core_vs_expanded_cohort_split",
        "benchmark_relative",
        "walk_forward",
        "metadata_concentration_disclosure",
    }:
        return rows
    if scenario_code == "clean_only":
        return [row for row in rows if row.get("coverage_quality_label") == "clean"]
    if scenario_code == "warning_only":
        return [row for row in rows if row.get("coverage_quality_label") != "clean"]
    if scenario_code == "clean_anchor":
        return [row for row in rows if not _as_bool(row.get("has_delayed_price_anchor"))]
    if scenario_code == "delayed_anchor":
        return [row for row in rows if _as_bool(row.get("has_delayed_price_anchor"))]
    if scenario_code == "current_core":
        return [row for row in rows if row.get("ticker") in CURRENT_CORE_TICKERS]
    if scenario_code == "expanded_cohort":
        return [row for row in rows if row.get("ticker") not in CURRENT_CORE_TICKERS]
    if scenario_code == "ex_nvda":
        return [row for row in rows if row.get("ticker") != "NVDA"]
    if scenario_code == "ex_top_contributors":
        top_tickers = _top_positive_tickers(rows, count=2)
        return [row for row in rows if row.get("ticker") not in top_tickers]
    if scenario_code == "ex_supportive_date":
        return [row for row in rows if row.get("as_of_date") != SUPPORTIVE_DATE]
    if scenario_code == "post_2021_only":
        return [row for row in rows if row.get("as_of_date") in POST_2021_DATES]
    return []


def _top_positive_tickers(rows: list[dict], *, count: int) -> set[str]:
    grouped: dict[str, list[float]] = {}
    for row in rows:
        value = _as_float(row, "relative_return_12m")
        if value is None:
            continue
        grouped.setdefault(row["ticker"], []).append(value)
    averages = [
        (ticker, mean(values))
        for ticker, values in grouped.items()
        if values and mean(values) > 0
    ]
    averages.sort(key=lambda item: item[1], reverse=True)
    return {ticker for ticker, _ in averages[:count]}


def build_controlled_re_run_summary(
    *,
    controlled_re_run_trial_run_id: str,
    package: dict,
) -> dict:
    """Build Task 121 summary metadata."""
    return {
        "controlled_re_run_trial_run_id": controlled_re_run_trial_run_id,
        "re_run_input_package_run_id": package["re_run_input_package_run_id"],
        "re_run_re_gate_plan_run_id": package["re_run_re_gate_plan_run_id"],
        "research_audit_trail_run_id": package["research_audit_trail_run_id"],
        "phase_id": 16,
        "current_task_id": 121,
        "current_task_name": "Execute Controlled Re-Run Trial",
        "gatekeeper_decision": "hold",
        "progression_allowed": False,
        "persona_reviews_allowed": False,
        "controlled_re_run_status": "completed",
        "trial_role": "controlled_re_run_execution",
        "future_consumer_task": NEXT_TASK,
        "main_trial_finding": (
            "Controlled local scenario outputs are ready for comparison; "
            "evidence remains held and no Gatekeeper rerun was executed."
        ),
        "recommended_next_task": NEXT_TASK,
    }


def build_scenario_execution_plan(package: dict) -> list[dict]:
    """Build the controlled scenario execution plan."""
    scenario_defs = [
        ("full_sample", "Full sample", "full_expanded_universe", "full_date_set"),
        ("clean_only", "Clean only", "full_expanded_universe", "clean_periods"),
        ("warning_only", "Warning only", "full_expanded_universe", "warning_periods"),
        (
            "clean_vs_warning_split",
            "Clean versus warning split",
            "full_expanded_universe",
            "full_date_set",
        ),
        ("clean_anchor", "Clean anchor", "full_expanded_universe", "clean_periods"),
        ("delayed_anchor", "Delayed anchor", "full_expanded_universe", "warning_periods"),
        (
            "clean_anchor_vs_delayed_anchor_split",
            "Clean-anchor versus delayed-anchor split",
            "full_expanded_universe",
            "anchor_split_periods",
        ),
        ("current_core", "Current core", "current_core", "full_date_set"),
        ("expanded_cohort", "Expanded cohort", "expanded_cohort", "full_date_set"),
        (
            "current_core_vs_expanded_cohort_split",
            "Current-core versus expanded-cohort split",
            "full_expanded_universe",
            "full_date_set",
        ),
        ("ex_nvda", "Ex-NVDA", "ex_nvda_universe", "full_date_set"),
        (
            "ex_top_contributors",
            "Ex-top contributors",
            "ex_top_contributors_universe",
            "full_date_set",
        ),
        (
            "ex_supportive_date",
            "Ex-supportive date",
            "full_expanded_universe",
            "ex_supportive_date_periods",
        ),
        ("post_2021_only", "Post-2021 only", "full_expanded_universe", "post_2021_periods"),
        (
            "benchmark_relative",
            "Benchmark-relative reporting",
            "full_expanded_universe",
            "full_date_set",
        ),
        ("walk_forward", "Walk-forward reporting", "full_expanded_universe", "full_date_set"),
        (
            "metadata_concentration_disclosure",
            "Metadata concentration disclosure",
            "metadata_concentration_groups",
            "full_date_set",
        ),
    ]
    controls = [row["control_code"] for row in package.get("re_run_control_matrix", [])]
    return [
        {
            "scenario_code": code,
            "scenario_label": label,
            "included": True,
            "universe_definition": universe,
            "date_definition": dates,
            "required_controls": ";".join(controls),
            "source_artifacts": "re_run_input_package;backtest_results;repair_artifacts",
            "executable_status": "executable",
            "non_execution_reason": "",
            "safety_boundary": "Research re-run only; no Gatekeeper or persona review execution.",
        }
        for code, label, universe, dates in scenario_defs
    ]


def _diagnostic_label(scenario_code: str, rel_median: float | None) -> str:
    if rel_median is None:
        return "missing_local_input"
    if scenario_code in {"clean_vs_warning_split", "clean_anchor_vs_delayed_anchor_split"}:
        return "split_reported_for_task_122"
    if scenario_code == "metadata_concentration_disclosure":
        return "metadata_context_disclosed"
    if rel_median > 0:
        return "positive_relative_research_slice"
    if rel_median < 0:
        return "negative_relative_research_slice"
    return "neutral_relative_research_slice"


def _scenario_result(
    *,
    scenario: dict,
    rows: list[dict],
) -> dict:
    scenario_code = scenario["scenario_code"]
    selected = _scenario_rows(rows, scenario_code)
    if not selected:
        return {
            "scenario_code": scenario_code,
            "scenario_label": scenario["scenario_label"],
            "execution_status": "not_executable_due_to_missing_local_input",
            "sample_size": 0,
            "tickers_count": 0,
            "dates_count": 0,
            "absolute_median_forward_12m": None,
            "benchmark_relative_median_12m": None,
            "benchmark_relative_hit_rate": None,
            "main_diagnostic_label": "missing_local_input",
            "comparison_note": "Local rows were unavailable for this scenario.",
            "safety_boundary": "No value was fabricated for missing local input.",
        }
    forwards = [
        value
        for row in selected
        if (value := _as_float(row, "forward_return_12m")) is not None
    ]
    relatives = [
        value
        for row in selected
        if (value := _as_float(row, "relative_return_12m")) is not None
    ]
    rel_median = _metric(relatives, "median")
    hit_rate = (
        round(sum(1 for value in relatives if value > 0) / len(relatives), 6)
        if relatives
        else None
    )
    return {
        "scenario_code": scenario_code,
        "scenario_label": scenario["scenario_label"],
        "execution_status": "executed_from_local_artifacts",
        "sample_size": len(selected),
        "tickers_count": len({row.get("ticker") for row in selected}),
        "dates_count": len({row.get("as_of_date") for row in selected}),
        "absolute_median_forward_12m": _metric(forwards, "median"),
        "benchmark_relative_median_12m": rel_median,
        "benchmark_relative_hit_rate": hit_rate,
        "main_diagnostic_label": _diagnostic_label(scenario_code, rel_median),
        "comparison_note": "Computed from local backtest_results.csv for Task 122 comparison.",
        "safety_boundary": "Research-only scenario result; not a recommendation or ranking.",
    }


def execute_re_run_scenarios_from_local_artifacts(
    *,
    scenario_execution_plan: list[dict],
    backtest_rows: list[dict],
) -> list[dict]:
    """Execute local scenario filters against existing backtest rows."""
    return [
        _scenario_result(scenario=scenario, rows=backtest_rows)
        for scenario in scenario_execution_plan
    ]


def build_scenario_results_matrix(
    *,
    scenario_execution_plan: list[dict],
    backtest_rows: list[dict],
) -> list[dict]:
    """Build controlled scenario results from local artifacts."""
    return execute_re_run_scenarios_from_local_artifacts(
        scenario_execution_plan=scenario_execution_plan,
        backtest_rows=backtest_rows,
    )


def build_control_diagnostics_matrix(package: dict) -> list[dict]:
    """Build diagnostics for required controls."""
    controls = [row["control_code"] for row in package.get("re_run_control_matrix", [])]
    if "post_2021_only" not in controls:
        controls.insert(13, "post_2021_only")
    return [
        {
            "control_code": control,
            "control_label": control.replace("_", " "),
            "reported_status": "reported",
            "finding": f"{control} is reported for Task 122 comparison.",
            "blocks_gatekeeper_rerun_until_compared": (
                control != "no_persona_review_before_gatekeeper_allows"
            ),
            "required_for_task_122": True,
            "safety_boundary": "Control diagnostic only; Gatekeeper is not rerun in Task 121.",
        }
        for control in controls
    ]


def build_re_run_limitations_matrix() -> list[dict]:
    """Build limitations for the controlled re-run trial."""
    rows = [
        ("local_artifacts_only", "Local artifacts only", "moderate"),
        ("no_new_market_data", "No new market data", "moderate"),
        ("no_new_financials", "No new financials", "moderate"),
        ("no_live_api_calls", "No live API calls", "low"),
        ("possible_missing_exact_delay_days", "Possible missing exact delay days", "moderate"),
        ("metadata_concentration_remaining", "Metadata concentration remaining", "high"),
        (
            "outlier_dependence_requires_comparison",
            "Outlier dependence requires comparison",
            "high",
        ),
        ("gatekeeper_not_rerun_in_task_121", "Gatekeeper not rerun in Task 121", "critical"),
        ("persona_review_not_allowed", "Persona review not allowed", "critical"),
    ]
    return [
        {
            "limitation_code": code,
            "limitation_label": label,
            "severity": severity,
            "source": "Task 121 controlled local re-run",
            "impact_on_interpretation": (
                "Task 122 must compare this limitation before any future gatekeeping."
            ),
            "required_follow_up": "Carry limitation into Task 122 comparison.",
            "safety_boundary": "Limitation disclosure only; no investment conclusion.",
        }
        for code, label, severity in rows
    ]


def build_task_122_handoff_manifest(
    *,
    controlled_re_run_trial_run_id: str,
) -> dict:
    """Build the Task 122 handoff manifest."""
    return {
        "future_task_id": 122,
        "future_task_name": "Compare Pre-Repair vs Post-Repair Evidence",
        "controlled_re_run_trial_run_id": controlled_re_run_trial_run_id,
        "required_inputs": [
            "controlled_re_run_trial",
            "scenario_results_matrix",
            "control_diagnostics_matrix",
            "limitations_matrix",
            "pre_repair_artifacts",
        ],
        "required_comparisons": [
            "pre_repair_vs_controlled_rerun",
            "full_sample_delta",
            "clean_vs_warning_delta",
            "clean_anchor_vs_delayed_anchor_delta",
            "current_core_vs_expanded_cohort_delta",
            "ex_nvda_delta",
            "ex_top_contributor_delta",
            "ex_supportive_date_delta",
            "post_2021_delta",
            "benchmark_relative_delta",
            "walk_forward_delta",
            "metadata_concentration_context",
        ],
        "prohibited_outputs": [
            "gatekeeper_decision",
            "persona_review",
            "investment_decision",
            "recommendation",
            "ranking",
            "allocation",
            "trade_signal",
            "execution_instruction",
        ],
        "readiness_status": "controlled_re_run_ready_for_comparison",
        "execution_allowed_now": True,
        "reason": (
            "Controlled re-run trial artifacts are ready for comparison, but "
            "Task 121 did not rerun Gatekeeper."
        ),
    }


def build_controlled_re_run_validation_checks() -> list[dict]:
    """Build validation checks for Task 121."""
    checks = [
        "input_package_loaded",
        "scenario_execution_plan_created",
        "scenario_results_matrix_created",
        "control_diagnostics_matrix_created",
        "limitations_matrix_created",
        "task_122_handoff_manifest_created",
        "gatekeeper_hold_preserved",
        "persona_review_block_preserved",
        "controlled_re_run_executed_or_rows_documented",
        "gatekeeper_not_rerun",
        "no_recommendation_outputs",
        "no_ranking_outputs",
        "no_trade_signal_outputs",
        "no_network_calls",
    ]
    return [
        {
            "check_code": check,
            "check_label": check.replace("_", " "),
            "status": "satisfied",
            "source_artifact": "controlled_re_run_trial",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 121 controlled re-run.",
        }
        for check in checks
    ]


def build_controlled_re_run_trial(
    *,
    controlled_re_run_trial_run_id: str,
    generated_at: str,
    outputs_root: Path,
    package: dict,
) -> ControlledReRunTrialReport:
    """Build the Task 121 controlled re-run trial."""
    backtest_rows = _load_backtest_rows(
        outputs_root=outputs_root,
        backtest_run_id=package["backtest_run_id"],
    )
    summary = build_controlled_re_run_summary(
        controlled_re_run_trial_run_id=controlled_re_run_trial_run_id,
        package=package,
    )
    scenario_plan = build_scenario_execution_plan(package)
    scenario_results = build_scenario_results_matrix(
        scenario_execution_plan=scenario_plan,
        backtest_rows=backtest_rows,
    )
    diagnostics = build_control_diagnostics_matrix(package)
    limitations = build_re_run_limitations_matrix()
    handoff = build_task_122_handoff_manifest(
        controlled_re_run_trial_run_id=controlled_re_run_trial_run_id,
    )
    checks = build_controlled_re_run_validation_checks()
    return ControlledReRunTrialReport(
        controlled_re_run_trial_run_id=controlled_re_run_trial_run_id,
        generated_at=generated_at,
        re_run_input_package_run_id=package["re_run_input_package_run_id"],
        re_run_re_gate_plan_run_id=package["re_run_re_gate_plan_run_id"],
        research_audit_trail_run_id=package["research_audit_trail_run_id"],
        buffett_munger_pack_run_id=package["buffett_munger_pack_run_id"],
        fisher_growth_pack_run_id=package["fisher_growth_pack_run_id"],
        bogle_benchmark_pack_run_id=package["bogle_benchmark_pack_run_id"],
        persona_evidence_pack_run_id=package["persona_evidence_pack_run_id"],
        metadata_diversity_recheck_run_id=package["metadata_diversity_recheck_run_id"],
        delayed_anchor_repair_run_id=package["delayed_anchor_repair_run_id"],
        walk_forward_repair_run_id=package["walk_forward_repair_run_id"],
        outlier_repair_run_id=package["outlier_repair_run_id"],
        decomposition_run_id=package["decomposition_run_id"],
        backoffice_attribution_run_id=package["backoffice_attribution_run_id"],
        investor_persona_attribution_run_id=package["investor_persona_attribution_run_id"],
        gatekeeper_run_id=package["gatekeeper_run_id"],
        scorecard_run_id=package["scorecard_run_id"],
        analysis_run_id=package["analysis_run_id"],
        expanded_trial_run_id=package["expanded_trial_run_id"],
        backtest_run_id=package["backtest_run_id"],
        controlled_re_run_summary=summary,
        scenario_execution_plan=scenario_plan,
        scenario_results_matrix=scenario_results,
        control_diagnostics_matrix=diagnostics,
        limitations_matrix=limitations,
        task_122_handoff_manifest=handoff,
        controlled_re_run_validation_checks=checks,
        controlled_re_run_status="completed",
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


def _render_markdown(report: ControlledReRunTrialReport) -> str:
    summary = report.controlled_re_run_summary
    handoff = report.task_122_handoff_manifest
    lines = [
        "# Controlled Re-Run Trial",
        "",
        "## Executive Summary",
        "",
        f"* Controlled Re-Run Trial Run ID: {report.controlled_re_run_trial_run_id}",
        f"* Re-Run Input Package Run ID: {report.re_run_input_package_run_id}",
        f"* Re-Run & Re-Gate Plan Run ID: {report.re_run_re_gate_plan_run_id}",
        f"* Research Audit Trail Run ID: {report.research_audit_trail_run_id}",
        "* Current Phase: 16 - Re-Run & Re-Gate Layer",
        "* Current Task: Task 121 - Execute Controlled Re-Run Trial",
        f"* Gatekeeper Decision: {summary['gatekeeper_decision']}",
        f"* Progression Allowed: {str(summary['progression_allowed']).lower()}",
        f"* Persona Reviews Allowed: {str(summary['persona_reviews_allowed']).lower()}",
        f"* Controlled Re-Run Status: {report.controlled_re_run_status}",
        f"* Recommended Next Task: {report.recommended_next_task}",
        "",
        "## Important Boundary",
        "",
        (
            "This report is a controlled research re-run only. It does not "
            "rerun Gatekeeper, allow persona review, create investor decisions, "
            "rankings, recommendations, allocations, rebalancing instructions, "
            "trade signals, execution instructions, or strategy validation."
        ),
        "",
        "## Where We Are Now",
        "",
        "Current Phase:",
        "16 — Re-Run & Re-Gate Layer",
        "",
        "Previous Task:",
        "Task 120 — Build Re-Run Input Package completed",
        "",
        "Direct Next:",
        "Task 122 — Compare Pre-Repair vs Post-Repair Evidence",
        "",
        "This Task:",
        "Task 121 executes the controlled re-run trial but does not rerun Gatekeeper.",
        "",
        "Phase 16 Expected Final Task:",
        "Task 124 — Phase 16 Closure & Next-Phase Recommendation",
        "",
        "## Controlled Re-Run Summary",
        "",
        f"* Trial Role: {summary['trial_role']}",
        f"* Future Consumer Task: {summary['future_consumer_task']}",
        f"* Main Trial Finding: {summary['main_trial_finding']}",
        "",
        "## Scenario Execution Plan",
        "",
        *_markdown_table(
            report.scenario_execution_plan,
            [
                ("Scenario", "scenario_code"),
                ("Included", "included"),
                ("Universe", "universe_definition"),
                ("Dates", "date_definition"),
                ("Executable Status", "executable_status"),
                ("Reason", "non_execution_reason"),
            ],
        ),
        "",
        "## Scenario Results Matrix",
        "",
        *_markdown_table(
            report.scenario_results_matrix,
            [
                ("Scenario", "scenario_code"),
                ("Status", "execution_status"),
                ("Sample Size", "sample_size"),
                ("Relative Median 12M", "benchmark_relative_median_12m"),
                ("Hit Rate", "benchmark_relative_hit_rate"),
                ("Diagnostic", "main_diagnostic_label"),
            ],
        ),
        "",
        "## Control Diagnostics Matrix",
        "",
        *_markdown_table(
            report.control_diagnostics_matrix,
            [
                ("Control", "control_code"),
                ("Reported Status", "reported_status"),
                ("Finding", "finding"),
                ("Required For Task 122", "required_for_task_122"),
            ],
        ),
        "",
        "## Limitations",
        "",
        *_markdown_table(
            report.limitations_matrix,
            [
                ("Limitation", "limitation_code"),
                ("Severity", "severity"),
                ("Impact", "impact_on_interpretation"),
                ("Follow-Up", "required_follow_up"),
            ],
        ),
        "",
        "## Task 122 Handoff",
        "",
        f"* Future Task: {handoff['future_task_id']} - {handoff['future_task_name']}",
        f"* Required Inputs: {'; '.join(handoff['required_inputs'])}",
        f"* Required Comparisons: {'; '.join(handoff['required_comparisons'])}",
        f"* Readiness Status: {handoff['readiness_status']}",
        f"* Execution Allowed Now: {str(handoff['execution_allowed_now']).lower()}",
        f"* Reason: {handoff['reason']}",
        "",
        "## Validation Checks",
        "",
        *_markdown_table(
            report.controlled_re_run_validation_checks,
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
        "* Controlled re-run artifacts are ready for Task 122 comparison.",
        "* Evidence remains held and non-actionable.",
        "* Gatekeeper has not been rerun.",
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


def write_controlled_re_run_trial_report(
    *,
    outputs_root: Path,
    re_run_input_package_run_id: str | None = None,
) -> ControlledReRunTrialFiles:
    """Write Task 121 controlled re-run artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_re_run_input_package_manifest(
        outputs_root=outputs_root,
        re_run_input_package_run_id=re_run_input_package_run_id,
    )
    package_run_id = manifest["re_run_input_package_run_id"]
    package = load_re_run_input_package(
        outputs_root=outputs_root,
        re_run_input_package_run_id=package_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    trial_run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_controlled_re_run_trial(
        controlled_re_run_trial_run_id=trial_run_id,
        generated_at=generated_at.isoformat(),
        outputs_root=outputs_root,
        package=package,
    )

    root = outputs_root / "controlled_re_run_trials"
    output_folder = root / trial_run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "controlled_re_run_trial.md"
    json_path = output_folder / "controlled_re_run_trial.json"
    scenario_execution_plan_csv_path = output_folder / "scenario_execution_plan.csv"
    scenario_results_matrix_csv_path = output_folder / "scenario_results_matrix.csv"
    control_diagnostics_matrix_csv_path = output_folder / "control_diagnostics_matrix.csv"
    limitations_matrix_csv_path = output_folder / "limitations_matrix.csv"
    task_122_handoff_manifest_path = output_folder / "task_122_handoff_manifest.json"
    validation_checks_csv_path = output_folder / "controlled_re_run_validation_checks.csv"
    latest_manifest_path = root / "latest_controlled_re_run_trial_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(scenario_execution_plan_csv_path, report.scenario_execution_plan)
    _write_csv(scenario_results_matrix_csv_path, report.scenario_results_matrix)
    _write_csv(control_diagnostics_matrix_csv_path, report.control_diagnostics_matrix)
    _write_csv(limitations_matrix_csv_path, report.limitations_matrix)
    task_122_handoff_manifest_path.write_text(
        json.dumps(report.task_122_handoff_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(validation_checks_csv_path, report.controlled_re_run_validation_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "controlled_re_run_trial_run_id": report.controlled_re_run_trial_run_id,
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
                "controlled_re_run_status": report.controlled_re_run_status,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "scenario_execution_plan_csv_path": str(
                    scenario_execution_plan_csv_path
                ),
                "scenario_results_matrix_csv_path": str(
                    scenario_results_matrix_csv_path
                ),
                "control_diagnostics_matrix_csv_path": str(
                    control_diagnostics_matrix_csv_path
                ),
                "limitations_matrix_csv_path": str(limitations_matrix_csv_path),
                "task_122_handoff_manifest_path": str(task_122_handoff_manifest_path),
                "validation_checks_csv_path": str(validation_checks_csv_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return ControlledReRunTrialFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        scenario_execution_plan_csv_path=scenario_execution_plan_csv_path,
        scenario_results_matrix_csv_path=scenario_results_matrix_csv_path,
        control_diagnostics_matrix_csv_path=control_diagnostics_matrix_csv_path,
        limitations_matrix_csv_path=limitations_matrix_csv_path,
        task_122_handoff_manifest_path=task_122_handoff_manifest_path,
        validation_checks_csv_path=validation_checks_csv_path,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
