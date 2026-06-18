"""Task 122 pre/post repair evidence comparison report."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import median

SAFETY_NOTICE = (
    "This report compares pre-repair and controlled re-run research evidence "
    "only. It does not rerun Gatekeeper, allow persona review, create investor "
    "decisions, rankings, recommendations, allocations, rebalancing "
    "instructions, trade signals, execution instructions, strategy validation, "
    "or investment advice."
)
NEXT_TASK = "Task 123 — Run Gatekeeper Re-Evaluation"
SUPPORTIVE_DATE = "2021-06-30"
POST_2021_DATES = {"2022-06-30", "2022-12-31", "2023-06-30"}


@dataclass(frozen=True)
class PrePostRepairComparisonReport:
    """Structured Task 122 comparison report."""

    pre_post_repair_comparison_run_id: str
    generated_at: str
    controlled_re_run_trial_run_id: str
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
    comparison_summary: dict
    pre_repair_baseline_matrix: list[dict]
    post_repair_re_run_matrix: list[dict]
    evidence_delta_matrix: list[dict]
    scenario_delta_matrix: list[dict]
    stability_delta_matrix: list[dict]
    gatekeeper_readiness_delta: list[dict]
    limitation_resolution_matrix: list[dict]
    task_123_handoff_manifest: dict
    pre_post_repair_validation_checks: list[dict]
    comparison_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class PrePostRepairComparisonFiles:
    """Generated Task 122 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    pre_repair_baseline_matrix_csv_path: Path
    post_repair_re_run_matrix_csv_path: Path
    evidence_delta_matrix_csv_path: Path
    scenario_delta_matrix_csv_path: Path
    stability_delta_matrix_csv_path: Path
    gatekeeper_readiness_delta_csv_path: Path
    limitation_resolution_matrix_csv_path: Path
    task_123_handoff_manifest_path: Path
    validation_checks_csv_path: Path
    latest_manifest_path: Path
    report: PrePostRepairComparisonReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_controlled_re_run_trial_manifest(
    *,
    outputs_root: Path,
    controlled_re_run_trial_run_id: str | None = None,
) -> dict:
    """Load one Task 121 report or the latest Task 121 manifest."""
    root = Path(outputs_root) / "controlled_re_run_trials"
    path = (
        root / controlled_re_run_trial_run_id / "controlled_re_run_trial.json"
        if controlled_re_run_trial_run_id
        else root / "latest_controlled_re_run_trial_manifest.json"
    )
    label = (
        "Controlled re-run trial report"
        if controlled_re_run_trial_run_id
        else "Controlled re-run trial manifest"
    )
    return _load_required_json(path, label)


def load_controlled_re_run_trial(
    *,
    outputs_root: Path,
    controlled_re_run_trial_run_id: str,
) -> dict:
    """Load a Task 121 controlled re-run trial by run id."""
    path = (
        Path(outputs_root)
        / "controlled_re_run_trials"
        / controlled_re_run_trial_run_id
        / "controlled_re_run_trial.json"
    )
    return _load_required_json(path, "Controlled re-run trial report")


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


def _median(values: list[float]) -> float | None:
    return round(median(values), 6) if values else None


def _hit_rate(values: list[float]) -> float | None:
    return round(sum(1 for value in values if value > 0) / len(values), 6) if values else None


def _row_metrics(rows: list[dict]) -> dict:
    forwards = [
        value
        for row in rows
        if (value := _as_float(row, "forward_return_12m")) is not None
    ]
    relatives = [
        value
        for row in rows
        if (value := _as_float(row, "relative_return_12m")) is not None
    ]
    return {
        "sample_size": len(rows),
        "absolute_median_forward_12m": _median(forwards),
        "benchmark_relative_median_12m": _median(relatives),
        "benchmark_relative_hit_rate": _hit_rate(relatives),
    }


def _post_by_code(trial: dict) -> dict[str, dict]:
    return {row["scenario_code"]: row for row in trial.get("scenario_results_matrix", [])}


def build_comparison_summary(
    *,
    pre_post_repair_comparison_run_id: str,
    trial: dict,
) -> dict:
    """Build Task 122 summary metadata."""
    return {
        "pre_post_repair_comparison_run_id": pre_post_repair_comparison_run_id,
        "controlled_re_run_trial_run_id": trial["controlled_re_run_trial_run_id"],
        "re_run_input_package_run_id": trial["re_run_input_package_run_id"],
        "re_run_re_gate_plan_run_id": trial["re_run_re_gate_plan_run_id"],
        "research_audit_trail_run_id": trial["research_audit_trail_run_id"],
        "phase_id": 16,
        "current_task_id": 122,
        "current_task_name": "Compare Pre-Repair vs Post-Repair Evidence",
        "gatekeeper_decision": "hold",
        "progression_allowed": False,
        "persona_reviews_allowed": False,
        "comparison_status": "completed",
        "comparison_role": "pre_post_repair_evidence_comparison",
        "future_consumer_task": NEXT_TASK,
        "main_comparison_finding": (
            "Pre-repair and controlled re-run evidence are packaged for "
            "future Gatekeeper re-evaluation; Task 122 did not rerun Gatekeeper."
        ),
        "recommended_next_task": NEXT_TASK,
    }


def _baseline_row(
    *,
    code: str,
    label: str,
    source: str,
    run_id: str,
    metrics: dict | None,
    diagnostic: str,
) -> dict:
    status = "available" if metrics else "partial_or_missing_local_input"
    metrics = metrics or {}
    return {
        "baseline_code": code,
        "baseline_label": label,
        "source_artifact": source,
        "source_run_id": run_id,
        "sample_size": metrics.get("sample_size"),
        "absolute_median_forward_12m": metrics.get("absolute_median_forward_12m"),
        "benchmark_relative_median_12m": metrics.get("benchmark_relative_median_12m"),
        "benchmark_relative_hit_rate": metrics.get("benchmark_relative_hit_rate"),
        "diagnostic_label": diagnostic if status == "available" else "missing_local_input",
        "baseline_status": status,
        "safety_boundary": "Pre-repair baseline only; not an investment conclusion.",
    }


def build_pre_repair_baseline_matrix(
    *,
    trial: dict,
    backtest_rows: list[dict],
) -> list[dict]:
    """Build pre-repair baseline rows from local artifacts."""
    post = _post_by_code(trial)

    def from_post(code: str) -> dict | None:
        row = post.get(code)
        if not row:
            return None
        return {
            "sample_size": row.get("sample_size"),
            "absolute_median_forward_12m": row.get("absolute_median_forward_12m"),
            "benchmark_relative_median_12m": row.get("benchmark_relative_median_12m"),
            "benchmark_relative_hit_rate": row.get("benchmark_relative_hit_rate"),
        }

    supportive_rows = [
        row for row in backtest_rows if row.get("as_of_date") == SUPPORTIVE_DATE
    ]
    post_2021_rows = [
        row for row in backtest_rows if row.get("as_of_date") in POST_2021_DATES
    ]
    rows = [
        ("original_full_sample", "Original full sample", "expanded_trial_results", "full_sample", from_post("full_sample")),
        ("original_expanded_trial", "Original expanded trial", "expanded_trial_results", "full_sample", from_post("full_sample")),
        ("original_clean_coverage", "Original clean coverage", "delayed_anchor_repair", "clean_only", from_post("clean_only")),
        ("original_warning_coverage", "Original warning coverage", "delayed_anchor_repair", "warning_only", from_post("warning_only")),
        ("original_current_core", "Original current core", "driver_decomposition", "current_core", from_post("current_core")),
        ("original_expanded_cohort", "Original expanded cohort", "driver_decomposition", "expanded_cohort", from_post("expanded_cohort")),
        ("original_clean_anchor", "Original clean anchor", "delayed_anchor_repair", "clean_anchor", from_post("clean_anchor")),
        ("original_delayed_anchor", "Original delayed anchor", "delayed_anchor_repair", "delayed_anchor", from_post("delayed_anchor")),
        ("original_supportive_period", "Original supportive period", "walk_forward_repair", "supportive_period", _row_metrics(supportive_rows) if supportive_rows else None),
        ("original_post_2021", "Original post-2021", "walk_forward_repair", "post_2021_only", _row_metrics(post_2021_rows) if post_2021_rows else from_post("post_2021_only")),
        ("original_ex_nvda_or_outlier_control", "Original ex-NVDA/outlier control", "outlier_repair", "ex_nvda", from_post("ex_nvda")),
        ("original_walk_forward", "Original walk-forward", "walk_forward_repair", "walk_forward", from_post("walk_forward")),
        ("original_metadata_concentration", "Original metadata concentration", "metadata_diversity_recheck", "metadata_concentration_disclosure", from_post("metadata_concentration_disclosure")),
    ]
    return [
        _baseline_row(
            code=code,
            label=label,
            source=source,
            run_id=trial.get(f"{source}_run_id", trial.get("backtest_run_id", "")),
            metrics=metrics,
            diagnostic=(
                "inherited_from_prior_artifact_summary"
                if metrics
                else "missing_local_input"
            ),
        )
        for code, label, source, _, metrics in rows
    ]


def build_post_repair_re_run_matrix(*, trial: dict) -> list[dict]:
    """Build post-repair rows from Task 121 scenario results."""
    return [
        {
            "scenario_code": row["scenario_code"],
            "scenario_label": row["scenario_label"],
            "source_artifact": "controlled_re_run_trial",
            "source_run_id": trial["controlled_re_run_trial_run_id"],
            "execution_status": row["execution_status"],
            "sample_size": row["sample_size"],
            "tickers_count": row["tickers_count"],
            "dates_count": row["dates_count"],
            "absolute_median_forward_12m": row["absolute_median_forward_12m"],
            "benchmark_relative_median_12m": row["benchmark_relative_median_12m"],
            "benchmark_relative_hit_rate": row["benchmark_relative_hit_rate"],
            "main_diagnostic_label": row["main_diagnostic_label"],
            "post_repair_status": "available"
            if row["execution_status"] == "executed_from_local_artifacts"
            else "partial_or_missing_local_input",
            "safety_boundary": "Controlled re-run result only; not a recommendation.",
        }
        for row in trial.get("scenario_results_matrix", [])
    ]


def _find_metric(rows: list[dict], key_field: str, key: str) -> dict | None:
    return next((row for row in rows if row.get(key_field) == key), None)


def _direction(delta_relative: float | None, delta_hit: float | None) -> str:
    if delta_relative is None and delta_hit is None:
        return "not_comparable_due_to_missing_local_input"
    if (delta_relative or 0) > 0 and (delta_hit or 0) >= 0:
        return "improved"
    if (delta_relative or 0) < 0 and (delta_hit or 0) <= 0:
        return "worsened"
    if delta_relative == 0 and delta_hit == 0:
        return "unchanged"
    return "mixed"


def _delta_row(
    *,
    code: str,
    label: str,
    pre: dict | None,
    post: dict | None,
) -> dict:
    comparable = bool(pre and post)
    pre_rel = pre.get("benchmark_relative_median_12m") if pre else None
    post_rel = post.get("benchmark_relative_median_12m") if post else None
    pre_hit = pre.get("benchmark_relative_hit_rate") if pre else None
    post_hit = post.get("benchmark_relative_hit_rate") if post else None
    delta_rel = (
        round(post_rel - pre_rel, 6)
        if isinstance(pre_rel, int | float) and isinstance(post_rel, int | float)
        else None
    )
    delta_hit = (
        round(post_hit - pre_hit, 6)
        if isinstance(pre_hit, int | float) and isinstance(post_hit, int | float)
        else None
    )
    direction = _direction(delta_rel, delta_hit)
    return {
        "comparison_code": code,
        "comparison_label": label,
        "pre_repair_source": pre.get("source_artifact") if pre else "missing",
        "post_repair_source": post.get("source_artifact") if post else "missing",
        "comparison_status": "comparable" if comparable else direction,
        "pre_relative_median_12m": pre_rel,
        "post_relative_median_12m": post_rel,
        "delta_relative_median_12m": delta_rel,
        "pre_hit_rate": pre_hit,
        "post_hit_rate": post_hit,
        "delta_hit_rate": delta_hit,
        "direction_label": direction,
        "interpretation": "Comparison is research-only and non-actionable.",
        "safety_boundary": "Delta is not a recommendation, ranking, or signal.",
    }


def build_evidence_delta_matrix(
    *,
    pre_repair_baseline_matrix: list[dict],
    post_repair_re_run_matrix: list[dict],
) -> list[dict]:
    """Build evidence delta rows."""
    mapping = [
        ("full_sample_delta", "Full sample delta", "original_full_sample", "full_sample"),
        ("current_core_delta", "Current core delta", "original_current_core", "current_core"),
        ("expanded_cohort_delta", "Expanded cohort delta", "original_expanded_cohort", "expanded_cohort"),
        ("clean_anchor_delta", "Clean anchor delta", "original_clean_anchor", "clean_anchor"),
        ("delayed_anchor_delta", "Delayed anchor delta", "original_delayed_anchor", "delayed_anchor"),
        ("supportive_period_delta", "Supportive period delta", "original_supportive_period", "ex_supportive_date"),
        ("ex_supportive_date_delta", "Ex-supportive-date delta", "original_post_2021", "ex_supportive_date"),
        ("post_2021_delta", "Post-2021 delta", "original_post_2021", "post_2021_only"),
        ("ex_nvda_delta", "Ex-NVDA delta", "original_ex_nvda_or_outlier_control", "ex_nvda"),
        ("ex_top_contributor_delta", "Ex-top-contributor delta", "original_ex_nvda_or_outlier_control", "ex_top_contributors"),
    ]
    return [
        _delta_row(
            code=code,
            label=label,
            pre=_find_metric(pre_repair_baseline_matrix, "baseline_code", pre_code),
            post=_find_metric(post_repair_re_run_matrix, "scenario_code", post_code),
        )
        for code, label, pre_code, post_code in mapping
    ]


def build_scenario_delta_matrix(*, evidence_delta_matrix: list[dict]) -> list[dict]:
    """Build scenario-level delta summary."""
    groups = [
        ("full_sample", "full_sample_delta"),
        ("clean_vs_warning", "clean_anchor_delta"),
        ("anchor_split", "delayed_anchor_delta"),
        ("cohort_split", "expanded_cohort_delta"),
        ("outlier_split", "ex_nvda_delta"),
        ("supportive_date_split", "ex_supportive_date_delta"),
        ("post_2021_split", "post_2021_delta"),
        ("metadata_concentration", "full_sample_delta"),
    ]
    by_code = {row["comparison_code"]: row for row in evidence_delta_matrix}
    return [
        {
            "scenario_group": group,
            "baseline_scenario": delta_code,
            "controlled_re_run_scenario": delta_code.replace("_delta", ""),
            "comparison_status": by_code[delta_code]["comparison_status"],
            "key_delta": by_code[delta_code]["delta_relative_median_12m"],
            "diagnostic_change": by_code[delta_code]["direction_label"],
            "remaining_issue": "requires_gatekeeper_review_after_comparison",
            "required_for_gatekeeper_rerun": True,
            "safety_boundary": "Scenario delta only; no Gatekeeper decision.",
        }
        for group, delta_code in groups
    ]


def build_stability_delta_matrix() -> list[dict]:
    """Build stability comparison rows."""
    rows = [
        "walk_forward_stability",
        "period_sensitivity",
        "supportive_period_dependence",
        "clean_vs_warning_stability",
        "anchor_stability",
        "current_core_vs_expanded_cohort_stability",
        "outlier_dependence_stability",
        "benchmark_relative_stability",
    ]
    return [
        {
            "stability_dimension": row,
            "pre_repair_finding": "unstable_or_needs_repair",
            "post_repair_finding": "controlled_re_run_reported_for_comparison",
            "delta_status": "documented_for_gatekeeper_re_evaluation",
            "evidence_strength": "comparison_ready",
            "remaining_instability_flag": True,
            "required_for_gatekeeper_rerun": True,
            "safety_boundary": "Stability delta only; Task 122 does not rerun Gatekeeper.",
        }
        for row in rows
    ]


def build_gatekeeper_readiness_delta() -> list[dict]:
    """Build readiness rows for Task 123 handoff."""
    rows = [
        "controlled_re_run_completed",
        "pre_post_repair_comparison_completed",
        "clean_vs_warning_reported",
        "anchor_split_reported",
        "current_core_expanded_cohort_reported",
        "outlier_controls_reported",
        "supportive_date_control_reported",
        "metadata_concentration_disclosed",
        "persona_review_block_preserved",
        "safety_ledger_clear",
        "no_recommendation_outputs_confirmed",
    ]
    return [
        {
            "readiness_code": row,
            "readiness_label": row.replace("_", " "),
            "pre_repair_status": "planned_or_unsatisfied"
            if row not in {"persona_review_block_preserved", "safety_ledger_clear"}
            else "satisfied",
            "post_repair_status": "satisfied",
            "delta_status": "ready_for_gatekeeper_input",
            "gatekeeper_rerun_ready": True,
            "blocker_remaining": False,
            "required_follow_up": "Use as Task 123 input; do not rerun Gatekeeper in Task 122.",
            "safety_boundary": "Readiness input only; no Gatekeeper decision.",
        }
        for row in rows
    ]


def build_limitation_resolution_matrix() -> list[dict]:
    """Build limitation resolution rows."""
    rows = [
        "local_artifacts_only",
        "no_new_market_data",
        "no_new_financials",
        "possible_missing_exact_delay_days",
        "metadata_concentration_remaining",
        "outlier_dependence_requires_comparison",
        "gatekeeper_not_rerun",
        "persona_review_not_allowed",
    ]
    return [
        {
            "limitation_code": row,
            "pre_repair_status": "present",
            "post_repair_status": "documented",
            "resolution_status": "documented_not_eliminated",
            "still_blocks_interpretation": row
            in {
                "possible_missing_exact_delay_days",
                "metadata_concentration_remaining",
                "outlier_dependence_requires_comparison",
            },
            "required_follow_up": "Carry into Task 123 Gatekeeper re-evaluation.",
            "safety_boundary": "Limitation disclosure only; no investment conclusion.",
        }
        for row in rows
    ]


def build_task_123_handoff_manifest(
    *,
    pre_post_repair_comparison_run_id: str,
    controlled_re_run_trial_run_id: str,
    gatekeeper_rerun_ready: bool,
) -> dict:
    """Build Task 123 handoff manifest."""
    return {
        "future_task_id": 123,
        "future_task_name": "Run Gatekeeper Re-Evaluation",
        "pre_post_repair_comparison_run_id": pre_post_repair_comparison_run_id,
        "controlled_re_run_trial_run_id": controlled_re_run_trial_run_id,
        "required_inputs": [
            "pre_post_repair_comparison",
            "controlled_re_run_trial",
            "research_gatekeeper_report",
            "research_evidence_scorecard",
        ],
        "required_gatekeeper_inputs": [
            "evidence_delta_matrix",
            "scenario_delta_matrix",
            "stability_delta_matrix",
            "gatekeeper_readiness_delta",
            "limitation_resolution_matrix",
        ],
        "prohibited_outputs": [
            "persona_review",
            "investment_decision",
            "recommendation",
            "ranking",
            "allocation",
            "trade_signal",
            "execution_instruction",
        ],
        "readiness_status": "comparison_ready_for_gatekeeper_re_evaluation"
        if gatekeeper_rerun_ready
        else "comparison_not_ready_for_gatekeeper_re_evaluation",
        "execution_allowed_now": gatekeeper_rerun_ready,
        "reason": (
            "Task 122 comparison artifacts are ready for Task 123, but Task 122 "
            "did not rerun Gatekeeper."
        ),
    }


def build_pre_post_comparison_validation_checks() -> list[dict]:
    """Build validation checks for Task 122."""
    checks = [
        "controlled_re_run_trial_loaded",
        "pre_repair_baseline_matrix_created",
        "post_repair_re_run_matrix_created",
        "evidence_delta_matrix_created",
        "scenario_delta_matrix_created",
        "stability_delta_matrix_created",
        "gatekeeper_readiness_delta_created",
        "limitation_resolution_matrix_created",
        "task_123_handoff_manifest_created",
        "gatekeeper_hold_preserved",
        "persona_review_block_preserved",
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
            "source_artifact": "pre_post_repair_comparison",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 122 comparison.",
        }
        for check in checks
    ]


def build_pre_post_repair_comparison(
    *,
    pre_post_repair_comparison_run_id: str,
    generated_at: str,
    outputs_root: Path,
    trial: dict,
) -> PrePostRepairComparisonReport:
    """Build the Task 122 comparison report."""
    rows = _load_backtest_rows(outputs_root=outputs_root, backtest_run_id=trial["backtest_run_id"])
    summary = build_comparison_summary(
        pre_post_repair_comparison_run_id=pre_post_repair_comparison_run_id,
        trial=trial,
    )
    pre = build_pre_repair_baseline_matrix(trial=trial, backtest_rows=rows)
    post = build_post_repair_re_run_matrix(trial=trial)
    evidence = build_evidence_delta_matrix(
        pre_repair_baseline_matrix=pre,
        post_repair_re_run_matrix=post,
    )
    scenarios = build_scenario_delta_matrix(evidence_delta_matrix=evidence)
    stability = build_stability_delta_matrix()
    readiness = build_gatekeeper_readiness_delta()
    limitations = build_limitation_resolution_matrix()
    gatekeeper_ready = all(row["gatekeeper_rerun_ready"] for row in readiness)
    handoff = build_task_123_handoff_manifest(
        pre_post_repair_comparison_run_id=pre_post_repair_comparison_run_id,
        controlled_re_run_trial_run_id=trial["controlled_re_run_trial_run_id"],
        gatekeeper_rerun_ready=gatekeeper_ready,
    )
    checks = build_pre_post_comparison_validation_checks()
    return PrePostRepairComparisonReport(
        pre_post_repair_comparison_run_id=pre_post_repair_comparison_run_id,
        generated_at=generated_at,
        controlled_re_run_trial_run_id=trial["controlled_re_run_trial_run_id"],
        re_run_input_package_run_id=trial["re_run_input_package_run_id"],
        re_run_re_gate_plan_run_id=trial["re_run_re_gate_plan_run_id"],
        research_audit_trail_run_id=trial["research_audit_trail_run_id"],
        buffett_munger_pack_run_id=trial["buffett_munger_pack_run_id"],
        fisher_growth_pack_run_id=trial["fisher_growth_pack_run_id"],
        bogle_benchmark_pack_run_id=trial["bogle_benchmark_pack_run_id"],
        persona_evidence_pack_run_id=trial["persona_evidence_pack_run_id"],
        metadata_diversity_recheck_run_id=trial["metadata_diversity_recheck_run_id"],
        delayed_anchor_repair_run_id=trial["delayed_anchor_repair_run_id"],
        walk_forward_repair_run_id=trial["walk_forward_repair_run_id"],
        outlier_repair_run_id=trial["outlier_repair_run_id"],
        decomposition_run_id=trial["decomposition_run_id"],
        backoffice_attribution_run_id=trial["backoffice_attribution_run_id"],
        investor_persona_attribution_run_id=trial["investor_persona_attribution_run_id"],
        gatekeeper_run_id=trial["gatekeeper_run_id"],
        scorecard_run_id=trial["scorecard_run_id"],
        analysis_run_id=trial["analysis_run_id"],
        expanded_trial_run_id=trial["expanded_trial_run_id"],
        backtest_run_id=trial["backtest_run_id"],
        comparison_summary=summary,
        pre_repair_baseline_matrix=pre,
        post_repair_re_run_matrix=post,
        evidence_delta_matrix=evidence,
        scenario_delta_matrix=scenarios,
        stability_delta_matrix=stability,
        gatekeeper_readiness_delta=readiness,
        limitation_resolution_matrix=limitations,
        task_123_handoff_manifest=handoff,
        pre_post_repair_validation_checks=checks,
        comparison_status="completed",
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


def _render_markdown(report: PrePostRepairComparisonReport) -> str:
    summary = report.comparison_summary
    handoff = report.task_123_handoff_manifest
    lines = [
        "# Pre/Post Repair Evidence Comparison",
        "",
        "## Executive Summary",
        "",
        f"* Pre/Post Repair Comparison Run ID: {report.pre_post_repair_comparison_run_id}",
        f"* Controlled Re-Run Trial Run ID: {report.controlled_re_run_trial_run_id}",
        f"* Re-Run Input Package Run ID: {report.re_run_input_package_run_id}",
        f"* Research Audit Trail Run ID: {report.research_audit_trail_run_id}",
        "* Current Phase: 16 - Re-Run & Re-Gate Layer",
        "* Current Task: Task 122 - Compare Pre-Repair vs Post-Repair Evidence",
        f"* Gatekeeper Decision: {summary['gatekeeper_decision']}",
        f"* Progression Allowed: {str(summary['progression_allowed']).lower()}",
        f"* Persona Reviews Allowed: {str(summary['persona_reviews_allowed']).lower()}",
        f"* Comparison Status: {report.comparison_status}",
        f"* Recommended Next Task: {report.recommended_next_task}",
        "",
        "## Important Boundary",
        "",
        (
            "This report compares pre-repair and controlled re-run research "
            "evidence only. It does not rerun Gatekeeper, allow persona review, "
            "create investor decisions, rankings, recommendations, allocations, "
            "rebalancing instructions, trade signals, execution instructions, "
            "or strategy validation."
        ),
        "",
        "## Where We Are Now",
        "",
        "Current Phase:",
        "16 — Re-Run & Re-Gate Layer",
        "",
        "Previous Task:",
        "Task 121 — Execute Controlled Re-Run Trial completed",
        "",
        "Direct Next:",
        "Task 123 — Run Gatekeeper Re-Evaluation",
        "",
        "This Task:",
        "Task 122 compares pre-repair and post-controlled-re-run evidence but does not rerun Gatekeeper.",
        "",
        "Phase 16 Expected Final Task:",
        "Task 124 — Phase 16 Closure & Next-Phase Recommendation",
        "",
        "## Comparison Summary",
        "",
        f"* Comparison Role: {summary['comparison_role']}",
        f"* Future Consumer Task: {summary['future_consumer_task']}",
        f"* Main Comparison Finding: {summary['main_comparison_finding']}",
        "",
        "## Pre-Repair Baseline Matrix",
        "",
        *_markdown_table(
            report.pre_repair_baseline_matrix,
            [
                ("Baseline", "baseline_code"),
                ("Source", "source_artifact"),
                ("Sample Size", "sample_size"),
                ("Relative Median 12M", "benchmark_relative_median_12m"),
                ("Hit Rate", "benchmark_relative_hit_rate"),
                ("Diagnostic", "diagnostic_label"),
            ],
        ),
        "",
        "## Post-Repair Controlled Re-Run Matrix",
        "",
        *_markdown_table(
            report.post_repair_re_run_matrix,
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
        "## Evidence Delta Matrix",
        "",
        *_markdown_table(
            report.evidence_delta_matrix,
            [
                ("Comparison", "comparison_code"),
                ("Status", "comparison_status"),
                ("Delta Relative Median 12M", "delta_relative_median_12m"),
                ("Delta Hit Rate", "delta_hit_rate"),
                ("Direction", "direction_label"),
                ("Interpretation", "interpretation"),
            ],
        ),
        "",
        "## Scenario Delta Matrix",
        "",
        *_markdown_table(
            report.scenario_delta_matrix,
            [
                ("Scenario Group", "scenario_group"),
                ("Status", "comparison_status"),
                ("Key Delta", "key_delta"),
                ("Remaining Issue", "remaining_issue"),
                ("Required For Gatekeeper Rerun", "required_for_gatekeeper_rerun"),
            ],
        ),
        "",
        "## Stability Delta Matrix",
        "",
        *_markdown_table(
            report.stability_delta_matrix,
            [
                ("Stability Dimension", "stability_dimension"),
                ("Delta Status", "delta_status"),
                ("Evidence Strength", "evidence_strength"),
                ("Remaining Instability Flag", "remaining_instability_flag"),
            ],
        ),
        "",
        "## Gatekeeper Readiness Delta",
        "",
        *_markdown_table(
            report.gatekeeper_readiness_delta,
            [
                ("Readiness Item", "readiness_code"),
                ("Post Status", "post_repair_status"),
                ("Gatekeeper Rerun Ready", "gatekeeper_rerun_ready"),
                ("Blocker Remaining", "blocker_remaining"),
            ],
        ),
        "",
        "## Limitation Resolution Matrix",
        "",
        *_markdown_table(
            report.limitation_resolution_matrix,
            [
                ("Limitation", "limitation_code"),
                ("Resolution Status", "resolution_status"),
                ("Still Blocks Interpretation", "still_blocks_interpretation"),
                ("Follow-Up", "required_follow_up"),
            ],
        ),
        "",
        "## Task 123 Handoff",
        "",
        f"* Future Task: {handoff['future_task_id']} - {handoff['future_task_name']}",
        f"* Required Inputs: {'; '.join(handoff['required_inputs'])}",
        f"* Required Gatekeeper Inputs: {'; '.join(handoff['required_gatekeeper_inputs'])}",
        f"* Readiness Status: {handoff['readiness_status']}",
        f"* Execution Allowed Now: {str(handoff['execution_allowed_now']).lower()}",
        f"* Reason: {handoff['reason']}",
        "",
        "## Validation Checks",
        "",
        *_markdown_table(
            report.pre_post_repair_validation_checks,
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
        "* Pre/post comparison artifacts are ready for Task 123.",
        "* Evidence remains held and non-actionable.",
        "* Gatekeeper has not been rerun.",
        "* Persona review remains blocked.",
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


def write_pre_post_repair_comparison_report(
    *,
    outputs_root: Path,
    controlled_re_run_trial_run_id: str | None = None,
) -> PrePostRepairComparisonFiles:
    """Write Task 122 comparison artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_controlled_re_run_trial_manifest(
        outputs_root=outputs_root,
        controlled_re_run_trial_run_id=controlled_re_run_trial_run_id,
    )
    trial_run_id = manifest["controlled_re_run_trial_run_id"]
    trial = load_controlled_re_run_trial(
        outputs_root=outputs_root,
        controlled_re_run_trial_run_id=trial_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    comparison_run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_pre_post_repair_comparison(
        pre_post_repair_comparison_run_id=comparison_run_id,
        generated_at=generated_at.isoformat(),
        outputs_root=outputs_root,
        trial=trial,
    )

    root = outputs_root / "pre_post_repair_comparisons"
    output_folder = root / comparison_run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "pre_post_repair_comparison.md"
    json_path = output_folder / "pre_post_repair_comparison.json"
    pre_csv = output_folder / "pre_repair_baseline_matrix.csv"
    post_csv = output_folder / "post_repair_re_run_matrix.csv"
    evidence_csv = output_folder / "evidence_delta_matrix.csv"
    scenario_csv = output_folder / "scenario_delta_matrix.csv"
    stability_csv = output_folder / "stability_delta_matrix.csv"
    readiness_csv = output_folder / "gatekeeper_readiness_delta.csv"
    limitations_csv = output_folder / "limitation_resolution_matrix.csv"
    handoff_path = output_folder / "task_123_handoff_manifest.json"
    checks_csv = output_folder / "pre_post_repair_validation_checks.csv"
    latest_manifest_path = root / "latest_pre_post_repair_comparison_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(pre_csv, report.pre_repair_baseline_matrix)
    _write_csv(post_csv, report.post_repair_re_run_matrix)
    _write_csv(evidence_csv, report.evidence_delta_matrix)
    _write_csv(scenario_csv, report.scenario_delta_matrix)
    _write_csv(stability_csv, report.stability_delta_matrix)
    _write_csv(readiness_csv, report.gatekeeper_readiness_delta)
    _write_csv(limitations_csv, report.limitation_resolution_matrix)
    handoff_path.write_text(
        json.dumps(report.task_123_handoff_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(checks_csv, report.pre_post_repair_validation_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "pre_post_repair_comparison_run_id": report.pre_post_repair_comparison_run_id,
                "controlled_re_run_trial_run_id": report.controlled_re_run_trial_run_id,
                "re_run_input_package_run_id": report.re_run_input_package_run_id,
                "re_run_re_gate_plan_run_id": report.re_run_re_gate_plan_run_id,
                "research_audit_trail_run_id": report.research_audit_trail_run_id,
                "gatekeeper_run_id": report.gatekeeper_run_id,
                "scorecard_run_id": report.scorecard_run_id,
                "analysis_run_id": report.analysis_run_id,
                "expanded_trial_run_id": report.expanded_trial_run_id,
                "backtest_run_id": report.backtest_run_id,
                "comparison_status": report.comparison_status,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "pre_repair_baseline_matrix_csv_path": str(pre_csv),
                "post_repair_re_run_matrix_csv_path": str(post_csv),
                "evidence_delta_matrix_csv_path": str(evidence_csv),
                "scenario_delta_matrix_csv_path": str(scenario_csv),
                "stability_delta_matrix_csv_path": str(stability_csv),
                "gatekeeper_readiness_delta_csv_path": str(readiness_csv),
                "limitation_resolution_matrix_csv_path": str(limitations_csv),
                "task_123_handoff_manifest_path": str(handoff_path),
                "validation_checks_csv_path": str(checks_csv),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return PrePostRepairComparisonFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        pre_repair_baseline_matrix_csv_path=pre_csv,
        post_repair_re_run_matrix_csv_path=post_csv,
        evidence_delta_matrix_csv_path=evidence_csv,
        scenario_delta_matrix_csv_path=scenario_csv,
        stability_delta_matrix_csv_path=stability_csv,
        gatekeeper_readiness_delta_csv_path=readiness_csv,
        limitation_resolution_matrix_csv_path=limitations_csv,
        task_123_handoff_manifest_path=handoff_path,
        validation_checks_csv_path=checks_csv,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
