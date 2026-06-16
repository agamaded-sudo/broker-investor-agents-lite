"""BO-003 walk-forward stability repair planning for held research evidence."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean, median

SAFETY_NOTICE = (
    "This report analyzes walk-forward stability and research repair only. It "
    "does not create an investment decision, recommendation, ranking, "
    "allocation instruction, rebalancing instruction, trade signal, execution "
    "instruction, strategy validation, or investment advice."
)
WORK_ORDER_ID = "BO-003"
WORK_ORDER_TITLE = "Walk-Forward Stability Repair Plan"
NEXT_WORK_ORDER = "BO-004 Delayed Anchor Exposure Repair"
SUPPORTIVE_DATE = "2021-06-30"


@dataclass(frozen=True)
class WalkForwardRepairPlanReport:
    """Structured BO-003 walk-forward repair plan."""

    walk_forward_repair_run_id: str
    generated_at: str
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
    walk_forward_repair_status: str
    period_stability_analysis: list[dict]
    clean_vs_warning_period_attribution: list[dict]
    cohort_by_period_analysis: list[dict]
    ex_nvda_by_period_analysis: list[dict]
    supportive_date_dependence: dict
    stability_failure_modes: list[dict]
    walk_forward_retest_plan: dict
    recommended_next_work_order: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class WalkForwardRepairPlanFiles:
    """Generated BO-003 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    period_csv_path: Path
    cohort_csv_path: Path
    ex_nvda_csv_path: Path
    failure_modes_csv_path: Path
    retest_plan_path: Path
    latest_manifest_path: Path
    report: WalkForwardRepairPlanReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_outlier_repair_manifest(
    *,
    outputs_root: Path,
    outlier_repair_run_id: str | None = None,
) -> dict:
    """Load one BO-002 report or the latest BO-002 manifest."""
    root = Path(outputs_root) / "outlier_repair_paths"
    path = (
        root / str(outlier_repair_run_id) / "outlier_repair_path_report.json"
        if outlier_repair_run_id
        else root / "latest_outlier_repair_path_manifest.json"
    )
    payload = _load_required_json(path, "Outlier repair manifest")
    payload["_manifest_path"] = str(path)
    return payload


def load_outlier_repair_report(
    *, outputs_root: Path, outlier_repair_run_id: str
) -> dict:
    """Load a complete BO-002 outlier repair report."""
    path = (
        Path(outputs_root)
        / "outlier_repair_paths"
        / str(outlier_repair_run_id)
        / "outlier_repair_path_report.json"
    )
    return _load_required_json(path, "Outlier repair report")


def load_backtest_driver_decomposition_report(
    *, outputs_root: Path, decomposition_run_id: str
) -> dict:
    """Load linked BO-001 decomposition context if available."""
    return _load_optional_json(
        Path(outputs_root)
        / "backtest_driver_decompositions"
        / str(decomposition_run_id)
        / "backtest_driver_decomposition_report.json"
    )


def load_backoffice_attribution_report(
    *, outputs_root: Path, backoffice_attribution_run_id: str
) -> dict:
    """Load linked Backoffice attribution context if available."""
    return _load_optional_json(
        Path(outputs_root)
        / "backoffice_evidence_quality_attributions"
        / str(backoffice_attribution_run_id)
        / "backoffice_evidence_quality_attribution_report.json"
    )


def load_research_scorecard_report(
    *, outputs_root: Path, scorecard_run_id: str
) -> dict:
    """Load linked scorecard context if available."""
    return _load_optional_json(
        Path(outputs_root)
        / "research_evidence_scorecards"
        / str(scorecard_run_id)
        / "research_evidence_scorecard_report.json"
    )


def load_expanded_trial_analysis_report(
    *, outputs_root: Path, analysis_run_id: str
) -> dict:
    """Load linked expanded trial analysis context if available."""
    return _load_optional_json(
        Path(outputs_root)
        / "expanded_trial_analyses"
        / str(analysis_run_id)
        / "expanded_trial_analysis_report.json"
    )


def load_backtest_results(
    *, outputs_root: Path, backtest_run_id: str
) -> list[dict]:
    """Load linked expanded backtest rows."""
    path = (
        Path(outputs_root)
        / "backtests"
        / str(backtest_run_id)
        / "backtest_results.csv"
    )
    if not path.is_file():
        raise FileNotFoundError(f"Backtest results not found: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _as_float(row: dict, key: str) -> float | None:
    value = row.get(key)
    if value in {None, "", "Missing"}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _round(value: float | None) -> float | None:
    return None if value is None else round(value, 6)


def _metadata_by_ticker(analysis: dict) -> dict[str, dict]:
    return {
        item["ticker"]: item
        for item in analysis.get("ticker_attribution", [])
        if item.get("ticker")
    }


def _enrich_rows(rows: list[dict], analysis: dict) -> list[dict]:
    metadata = _metadata_by_ticker(analysis)
    enriched = []
    for row in rows:
        item = dict(row)
        ticker_meta = metadata.get(str(row.get("ticker")), {})
        item["sector"] = row.get("sector") or ticker_meta.get("sector") or "Missing"
        item["category"] = (
            row.get("category") or ticker_meta.get("category") or "Missing"
        )
        item["universe_group"] = (
            row.get("universe_group")
            or ticker_meta.get("universe_group")
            or "Missing"
        )
        item["cohort"] = (
            "current_core"
            if item["universe_group"] == "current_core"
            else "expanded_cohort"
        )
        enriched.append(item)
    return enriched


def _metric_summary(rows: list[dict]) -> dict:
    forward = [
        value
        for value in (_as_float(row, "forward_return_12m") for row in rows)
        if value is not None
    ]
    relative = [
        value
        for value in (_as_float(row, "relative_return_12m") for row in rows)
        if value is not None
    ]
    drawdown = [
        value
        for value in (_as_float(row, "max_drawdown_12m") for row in rows)
        if value is not None
    ]
    hit_rate = None
    if relative:
        hit_rate = sum(value > 0 for value in relative) / len(relative)
    return {
        "records": len(rows),
        "clean_records": sum(
            row.get("coverage_guardrail_status") == "clean"
            or row.get("coverage_quality_label") == "clean"
            for row in rows
        ),
        "warning_records": sum(
            row.get("coverage_guardrail_status") != "clean"
            and row.get("coverage_quality_label") != "clean"
            for row in rows
        ),
        "median_forward_return_12m": _round(median(forward) if forward else None),
        "median_relative_return_12m": _round(median(relative) if relative else None),
        "average_relative_return_12m": _round(mean(relative) if relative else None),
        "hit_rate_vs_benchmark_12m": _round(hit_rate),
        "worst_max_drawdown_12m": _round(min(drawdown) if drawdown else None),
    }


def _group(rows: list[dict], key: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(str(row.get(key) or "Missing"), []).append(row)
    return grouped


def _relative_positive(summary: dict) -> bool:
    value = summary.get("median_relative_return_12m")
    return bool(value is not None and value > 0)


def _hit_rate_passes(summary: dict) -> bool:
    value = summary.get("hit_rate_vs_benchmark_12m")
    return bool(value is not None and value >= 0.5)


def _period_label(date: str, summary: dict, decomposition: dict) -> str:
    by_date = {
        item.get("as_of_date"): item.get("period_label")
        for item in decomposition.get("date_drivers", [])
    }
    if by_date.get(date):
        return by_date[date]
    if _relative_positive(summary) and _hit_rate_passes(summary):
        return "supportive_period"
    if summary.get("median_relative_return_12m", 0) < 0:
        return "negative_period"
    return "neutral_period"


def _severity(label: str, summary: dict) -> str:
    if label == "supportive_outlier_period":
        return "moderate"
    if label in {"warning_coverage_period", "cohort_break_period"}:
        return "high"
    if label == "benchmark_relative_failure":
        relative = summary.get("median_relative_return_12m")
        return "severe" if relative is not None and relative <= -0.1 else "high"
    if label == "mixed_instability_period":
        return "moderate"
    return "low"


def _instability_label(summary: dict, core: dict, expanded: dict) -> str:
    if _relative_positive(summary) and _hit_rate_passes(summary):
        return "supportive_outlier_period"
    if summary["warning_records"] > 0 and summary["clean_records"] == 0:
        return "warning_coverage_period"
    if not _relative_positive(summary) and not _hit_rate_passes(summary):
        return "benchmark_relative_failure"
    if _relative_positive(core) and not _relative_positive(expanded):
        return "cohort_break_period"
    if not _relative_positive(summary):
        return "mixed_instability_period"
    return "stable_period"


def _interpret_period(label: str, date: str) -> str:
    if label == "supportive_outlier_period":
        return f"{date} is supportive but creates dependence on one period."
    if label == "warning_coverage_period":
        return f"{date} is weak and consists only of warning-bearing records."
    if label == "cohort_break_period":
        return f"{date} breaks between current-core and expanded-cohort evidence."
    if label == "benchmark_relative_failure":
        return f"{date} underperforms benchmark-relative controls."
    if label == "mixed_instability_period":
        return f"{date} is mixed and needs separate retest controls."
    return f"{date} does not break stability in this diagnostic."


def analyze_period_breaks(
    rows: list[dict],
    *,
    analysis: dict,
    decomposition: dict,
) -> list[dict]:
    """Create period-level stability analysis for every evaluated date."""
    enriched = _enrich_rows(rows, analysis)
    periods = []
    for date, date_rows in sorted(_group(enriched, "signal_date").items()):
        summary = _metric_summary(date_rows)
        core = _metric_summary(
            [row for row in date_rows if row.get("cohort") == "current_core"]
        )
        expanded = _metric_summary(
            [row for row in date_rows if row.get("cohort") == "expanded_cohort"]
        )
        nvda_rows = [row for row in date_rows if row.get("ticker") == "NVDA"]
        ex_nvda = _metric_summary(
            [row for row in date_rows if row.get("ticker") != "NVDA"]
        )
        label = _instability_label(summary, core, expanded)
        periods.append(
            {
                "as_of_date": date,
                "period_label": _period_label(date, summary, decomposition),
                **summary,
                "current_core_median_relative_return_12m": core[
                    "median_relative_return_12m"
                ],
                "expanded_cohort_median_relative_return_12m": expanded[
                    "median_relative_return_12m"
                ],
                "current_core_hit_rate_vs_benchmark_12m": core[
                    "hit_rate_vs_benchmark_12m"
                ],
                "expanded_cohort_hit_rate_vs_benchmark_12m": expanded[
                    "hit_rate_vs_benchmark_12m"
                ],
                "nvda_relative_return_12m": (
                    _as_float(nvda_rows[0], "relative_return_12m")
                    if nvda_rows
                    else None
                ),
                "ex_nvda_median_relative_return_12m": ex_nvda[
                    "median_relative_return_12m"
                ],
                "instability_driver_label": label,
                "instability_severity": _severity(label, summary),
                "interpretation": _interpret_period(label, date),
            }
        )
    return periods


def _period_type(period: dict) -> str:
    if period["clean_records"] > 0 and period["warning_records"] == 0:
        return "clean_date_period"
    if period["warning_records"] > 0 and period["clean_records"] == 0:
        return "warning_date_period"
    return "mixed_period"


def summarize_clean_vs_warning_periods(periods: list[dict]) -> list[dict]:
    """Summarize stability by clean-date and warning-date period groups."""
    grouped: dict[str, list[dict]] = {}
    for period in periods:
        grouped.setdefault(_period_type(period), []).append(period)
    rows = []
    for period_type, items in sorted(grouped.items()):
        records = sum(int(item["records"]) for item in items)
        rel_values = [
            item["median_relative_return_12m"]
            for item in items
            if item["median_relative_return_12m"] is not None
        ]
        hit_values = [
            item["hit_rate_vs_benchmark_12m"]
            for item in items
            if item["hit_rate_vs_benchmark_12m"] is not None
        ]
        median_relative = _round(median(rel_values) if rel_values else None)
        hit_rate = _round(mean(hit_values) if hit_values else None)
        rows.append(
            {
                "period_type": period_type,
                "period_count": len(items),
                "records": records,
                "median_relative_return_12m": median_relative,
                "hit_rate_vs_benchmark_12m": hit_rate,
                "interpretation": (
                    "Clean periods also require repair controls."
                    if period_type == "clean_date_period"
                    and median_relative is not None
                    and median_relative < 0
                    else "Warning periods need separate attribution."
                    if period_type == "warning_date_period"
                    else "Mixed periods require separate review."
                ),
            }
        )
    return rows


def summarize_cohort_by_period(rows: list[dict], analysis: dict) -> list[dict]:
    """Create current-core versus expanded-cohort period rows."""
    enriched = _enrich_rows(rows, analysis)
    output = []
    for date, date_rows in sorted(_group(enriched, "signal_date").items()):
        core = _metric_summary(
            [row for row in date_rows if row.get("cohort") == "current_core"]
        )
        expanded = _metric_summary(
            [row for row in date_rows if row.get("cohort") == "expanded_cohort"]
        )
        core_rel = core["median_relative_return_12m"]
        expanded_rel = expanded["median_relative_return_12m"]
        gap = (
            _round(expanded_rel - core_rel)
            if core_rel is not None and expanded_rel is not None
            else None
        )
        label = (
            "expanded_cohort_drag"
            if gap is not None and gap < 0
            else "cohort_mixed"
            if gap is not None
            else "insufficient_cohort_evidence"
        )
        output.append(
            {
                "as_of_date": date,
                "current_core_records": core["records"],
                "expanded_cohort_records": expanded["records"],
                "current_core_median_relative_return_12m": core_rel,
                "expanded_cohort_median_relative_return_12m": expanded_rel,
                "current_core_hit_rate_vs_benchmark_12m": core[
                    "hit_rate_vs_benchmark_12m"
                ],
                "expanded_cohort_hit_rate_vs_benchmark_12m": expanded[
                    "hit_rate_vs_benchmark_12m"
                ],
                "relative_gap_expanded_minus_core": gap,
                "cohort_instability_label": label,
                "interpretation": (
                    "Expanded cohort is weaker than current core for this period."
                    if label == "expanded_cohort_drag"
                    else "Cohort split is mixed or incomplete for this period."
                ),
            }
        )
    return output


def summarize_ex_nvda_by_period(rows: list[dict], analysis: dict) -> list[dict]:
    """Create full-sample versus Ex-NVDA period rows."""
    enriched = _enrich_rows(rows, analysis)
    output = []
    for date, date_rows in sorted(_group(enriched, "signal_date").items()):
        full = _metric_summary(date_rows)
        ex_nvda = _metric_summary(
            [row for row in date_rows if row.get("ticker") != "NVDA"]
        )
        nvda_rows = [row for row in date_rows if row.get("ticker") == "NVDA"]
        full_rel = full["median_relative_return_12m"]
        ex_rel = ex_nvda["median_relative_return_12m"]
        label = (
            "nvda_lifts_period"
            if full_rel is not None and ex_rel is not None and ex_rel < full_rel
            else "nvda_not_primary_period_driver"
        )
        output.append(
            {
                "as_of_date": date,
                "full_sample_records": full["records"],
                "full_sample_median_relative_return_12m": full_rel,
                "full_sample_hit_rate_vs_benchmark_12m": full[
                    "hit_rate_vs_benchmark_12m"
                ],
                "ex_nvda_records": ex_nvda["records"],
                "ex_nvda_median_relative_return_12m": ex_rel,
                "ex_nvda_hit_rate_vs_benchmark_12m": ex_nvda[
                    "hit_rate_vs_benchmark_12m"
                ],
                "nvda_relative_return_12m": (
                    _as_float(nvda_rows[0], "relative_return_12m")
                    if nvda_rows
                    else None
                ),
                "nvda_dependency_label": label,
                "interpretation": (
                    "NVDA improves this period's relative evidence."
                    if label == "nvda_lifts_period"
                    else "NVDA is not the primary period-level lift."
                ),
            }
        )
    return output


def analyze_supportive_date_dependence(outlier: dict, periods: list[dict]) -> dict:
    """Summarize dependence on the supportive 2021-06-30 period."""
    scenarios = {
        item.get("scenario_code"): item
        for item in outlier.get("scenario_analysis", [])
    }
    supportive = next(
        (period for period in periods if period["as_of_date"] == SUPPORTIVE_DATE),
        {},
    )
    ex_supportive = scenarios.get("ex_supportive_date_2021_06_30", {})
    return {
        "supportive_date": SUPPORTIVE_DATE,
        "supportive_period_label": supportive.get("period_label"),
        "supportive_median_relative_return_12m": supportive.get(
            "median_relative_return_12m"
        ),
        "supportive_hit_rate_vs_benchmark_12m": supportive.get(
            "hit_rate_vs_benchmark_12m"
        ),
        "ex_supportive_date_median_relative_return_12m": ex_supportive.get(
            "median_relative_return_12m"
        ),
        "ex_supportive_date_hit_rate_vs_benchmark_12m": ex_supportive.get(
            "hit_rate_vs_benchmark_12m"
        ),
        "supportive_date_dependence_label": (
            "material_supportive_date_dependence"
            if ex_supportive.get("scenario_result_label") == "fails_outlier_control"
            else "limited_supportive_date_dependence"
        ),
        "interpretation": (
            "Removing 2021-06-30 weakens the evidence materially, so the "
            "supportive date must be reported separately in any retest."
        ),
    }


def _failure_modes(periods: list[dict]) -> list[dict]:
    negative_periods = [
        item["as_of_date"]
        for item in periods
        if item["period_label"] == "negative_period"
    ]
    clean_negative = [
        item["as_of_date"]
        for item in periods
        if _period_type(item) == "clean_date_period"
        and item["median_relative_return_12m"] is not None
        and item["median_relative_return_12m"] < 0
    ]
    warning_weak = [
        item["as_of_date"]
        for item in periods
        if _period_type(item) == "warning_date_period"
    ]
    return [
        {
            "failure_mode_code": "supportive_date_dependence",
            "failure_mode_label": "Supportive Date Dependence",
            "affected_periods": [SUPPORTIVE_DATE],
            "affected_cohorts": ["current_core", "expanded_cohort"],
            "evidence": "2021-06-30 is the only supportive evaluated period.",
            "repair_action": "Report full sample and ex-supportive-date separately.",
            "priority": "P0",
        },
        {
            "failure_mode_code": "post_2021_relative_underperformance",
            "failure_mode_label": "Post-2021 Relative Underperformance",
            "affected_periods": negative_periods,
            "affected_cohorts": ["current_core", "expanded_cohort"],
            "evidence": "Post-2021 evaluated periods are benchmark-relative weak.",
            "repair_action": "Add period controls before any future gatekeeper rerun.",
            "priority": "P0",
        },
        {
            "failure_mode_code": "warning_period_weakness",
            "failure_mode_label": "Warning Period Weakness",
            "affected_periods": warning_weak,
            "affected_cohorts": ["current_core", "expanded_cohort"],
            "evidence": "Warning-only periods underperform benchmark controls.",
            "repair_action": "Separate warning-date periods from clean-date periods.",
            "priority": "P1",
        },
        {
            "failure_mode_code": "clean_period_not_sufficient",
            "failure_mode_label": "Clean Period Not Sufficient",
            "affected_periods": clean_negative,
            "affected_cohorts": ["current_core", "expanded_cohort"],
            "evidence": "Some clean-date periods are benchmark-relative negative.",
            "repair_action": "Do not treat clean coverage as sufficient by itself.",
            "priority": "P1",
        },
        {
            "failure_mode_code": "expanded_cohort_period_drag",
            "failure_mode_label": "Expanded Cohort Period Drag",
            "affected_periods": negative_periods,
            "affected_cohorts": ["expanded_cohort"],
            "evidence": "Expanded cohort weakens current-core evidence by period.",
            "repair_action": "Report current-core and expanded-cohort by every date.",
            "priority": "P0",
        },
        {
            "failure_mode_code": "nvda_or_top_contributor_period_dependence",
            "failure_mode_label": "NVDA or Top Contributor Period Dependence",
            "affected_periods": [period["as_of_date"] for period in periods],
            "affected_cohorts": ["current_core"],
            "evidence": "Outlier repair confirms contributor dependence.",
            "repair_action": "Report Ex-NVDA and ex-top-2 controls by period.",
            "priority": "P0",
        },
        {
            "failure_mode_code": "benchmark_relative_failure",
            "failure_mode_label": "Benchmark-Relative Failure",
            "affected_periods": negative_periods,
            "affected_cohorts": ["current_core", "expanded_cohort"],
            "evidence": "Median relative 12M and hit rate fail after expansion.",
            "repair_action": "Separate absolute evidence from benchmark-relative evidence.",
            "priority": "P0",
        },
    ]


def attribute_period_instability(periods: list[dict]) -> dict:
    """Summarize date-level stability break counts and finding."""
    supportive = sum(item["period_label"] == "supportive_period" for item in periods)
    negative = sum(item["period_label"] == "negative_period" for item in periods)
    stable = sum(item["instability_driver_label"] == "stable_period" for item in periods)
    unstable = len(periods) - stable
    return {
        "supportive_period_count": supportive,
        "negative_period_count": negative,
        "stable_period_count": stable,
        "unstable_period_count": unstable,
        "main_date_break_finding": (
            "Walk-forward instability is concentrated in post-2021 periods, "
            "while 2021-06-30 is supportive and must be controlled separately."
        ),
    }


def build_walk_forward_retest_plan() -> dict:
    """Create the BO-003 non-actionable retest plan."""
    return {
        "retest_plan_id": "BO-003-walk-forward-retest-plan",
        "purpose": (
            "Define period, cohort, coverage, outlier, and benchmark controls "
            "required before any future research gatekeeper rerun."
        ),
        "required_period_controls": [
            "Report full sample and ex-supportive-date sample separately.",
            "Report clean-date periods separately from warning-date periods.",
            "Report current_core and expanded_cohort separately for every date.",
            "Report ex-NVDA and ex-top-2 by period.",
            "Report benchmark-relative and absolute evidence separately.",
        ],
        "required_date_additions": [
            "Acquire additional local fixture-supported dates only if point-in-time coverage exists.",
            "Do not claim additional dates are present until local coverage is validated.",
        ],
        "required_date_exclusions": [
            "Report ex_supportive_date_2021_06_30 as a required control.",
        ],
        "required_subsample_views": [
            "full_sample",
            "ex_supportive_date",
            "clean_date_periods",
            "warning_date_periods",
            "current_core_by_period",
            "expanded_cohort_by_period",
            "ex_nvda_by_period",
            "ex_top_2_by_period",
        ],
        "minimum_reporting_requirements": [
            "Every unstable period must have a documented driver.",
            "Rerun requirements must contain no fabricated coverage.",
            "Absolute and benchmark-relative evidence must remain separate.",
        ],
        "repair_before_rerun_requirements": [
            "Document period sensitivity.",
            "Document cohort composition effects.",
            "Document contributor dependence by period.",
        ],
        "next_gatekeeping_requirements": [
            "Gatekeeper must be rerun after repair before progression.",
            "Progression remains blocked while gatekeeper decision is hold.",
        ],
        "safety_constraints": [
            "Do not rerun investor agents for this repair plan.",
            "No future price information may be introduced.",
            "Do not create recommendations, rankings, allocations, or trade signals.",
        ],
    }


def build_walk_forward_repair_plan(
    *,
    walk_forward_repair_run_id: str,
    generated_at: str,
    outlier: dict,
    decomposition: dict,
    backoffice: dict,
    scorecard: dict,
    analysis: dict,
    rows: list[dict],
) -> WalkForwardRepairPlanReport:
    """Build the full BO-003 walk-forward repair report."""
    periods = analyze_period_breaks(
        rows,
        analysis=analysis,
        decomposition=decomposition,
    )
    clean_warning = summarize_clean_vs_warning_periods(periods)
    cohort_periods = summarize_cohort_by_period(rows, analysis)
    ex_nvda_periods = summarize_ex_nvda_by_period(rows, analysis)
    supportive = analyze_supportive_date_dependence(outlier, periods)
    failure_modes = _failure_modes(periods)
    retest_plan = build_walk_forward_retest_plan()
    return WalkForwardRepairPlanReport(
        walk_forward_repair_run_id=walk_forward_repair_run_id,
        generated_at=generated_at,
        outlier_repair_run_id=str(outlier.get("outlier_repair_run_id") or ""),
        decomposition_run_id=str(outlier.get("decomposition_run_id") or ""),
        backoffice_attribution_run_id=str(
            outlier.get("backoffice_attribution_run_id") or ""
        ),
        investor_persona_attribution_run_id=str(
            outlier.get("investor_persona_attribution_run_id") or ""
        ),
        gatekeeper_run_id=str(outlier.get("gatekeeper_run_id") or ""),
        scorecard_run_id=str(outlier.get("scorecard_run_id") or ""),
        analysis_run_id=str(outlier.get("analysis_run_id") or ""),
        expanded_trial_run_id=str(outlier.get("expanded_trial_run_id") or ""),
        backtest_run_id=str(outlier.get("backtest_run_id") or ""),
        work_order_id=WORK_ORDER_ID,
        work_order_title=WORK_ORDER_TITLE,
        walk_forward_repair_status="completed",
        period_stability_analysis=periods,
        clean_vs_warning_period_attribution=clean_warning,
        cohort_by_period_analysis=cohort_periods,
        ex_nvda_by_period_analysis=ex_nvda_periods,
        supportive_date_dependence=supportive,
        stability_failure_modes=failure_modes,
        walk_forward_retest_plan=retest_plan,
        recommended_next_work_order=NEXT_WORK_ORDER,
    )


def _display(value) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "None"
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return "" if value is None else str(value)


def _main_stability_finding(report: WalkForwardRepairPlanReport) -> str:
    attribution = attribute_period_instability(report.period_stability_analysis)
    return attribution["main_date_break_finding"]


def render_walk_forward_repair_plan_report(
    report: WalkForwardRepairPlanReport,
) -> str:
    """Render BO-003 as Markdown."""
    data = report.to_dict()
    main_finding = _main_stability_finding(report)
    lines = [
        "# Walk-Forward Stability Repair Plan",
        "",
        "## Executive Summary",
        "",
        f"- Walk-Forward Repair Run ID: {data['walk_forward_repair_run_id']}",
        f"- Outlier Repair Run ID: {data['outlier_repair_run_id']}",
        f"- Work Order ID: {data['work_order_id']}",
        f"- Backtest Run ID: {data['backtest_run_id']}",
        f"- Main Stability Finding: {main_finding}",
        f"- Recommended Next Work Order: {data['recommended_next_work_order']}",
        "",
        "## Important Boundary",
        "",
        (
            "This report analyzes walk-forward stability and research repair "
            "only. It does not create an investment decision, ranking, "
            "recommendation, allocation, rebalancing instruction, trade signal, "
            "or execution instruction."
        ),
        "",
        "## Source Context",
        "",
        "- Gatekeeper Decision: hold",
        "- Progression Allowed: false",
        f"- Current Work Order: {data['work_order_id']}",
        "- Reason: unstable walk-forward and period sensitivity.",
        "",
        "## Period Stability Analysis",
        "",
        (
            "| Date | Records | Clean | Warning | Median Relative 12M | "
            "Hit Rate | Instability Driver | Severity |"
        ),
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for item in data["period_stability_analysis"]:
        lines.append(
            f"| {item['as_of_date']} | {item['records']} | "
            f"{item['clean_records']} | {item['warning_records']} | "
            f"{item['median_relative_return_12m']} | "
            f"{item['hit_rate_vs_benchmark_12m']} | "
            f"{item['instability_driver_label']} | "
            f"{item['instability_severity']} |"
        )
    lines.extend(
        [
            "",
            "## Clean vs Warning Period Attribution",
            "",
        ]
    )
    for item in data["clean_vs_warning_period_attribution"]:
        lines.append(
            f"- {item['period_type']}: records={item['records']}, "
            f"median_relative_12m={item['median_relative_return_12m']}, "
            f"hit_rate={item['hit_rate_vs_benchmark_12m']}. "
            f"{item['interpretation']}"
        )
    lines.extend(
        [
            "",
            "## Current Core vs Expanded Cohort by Period",
            "",
        ]
    )
    for item in data["cohort_by_period_analysis"]:
        lines.append(
            f"- {item['as_of_date']}: current_core="
            f"{item['current_core_median_relative_return_12m']}, "
            f"expanded_cohort={item['expanded_cohort_median_relative_return_12m']}, "
            f"gap={item['relative_gap_expanded_minus_core']}."
        )
    lines.extend(
        [
            "",
            "## Ex-NVDA by Period",
            "",
        ]
    )
    for item in data["ex_nvda_by_period_analysis"]:
        lines.append(
            f"- {item['as_of_date']}: full="
            f"{item['full_sample_median_relative_return_12m']}, "
            f"ex_nvda={item['ex_nvda_median_relative_return_12m']}, "
            f"label={item['nvda_dependency_label']}."
        )
    supportive = data["supportive_date_dependence"]
    lines.extend(
        [
            "",
            "## Supportive Date Dependence",
            "",
            (
                f"- {supportive['supportive_date']}: median_relative_12m="
                f"{supportive['supportive_median_relative_return_12m']}, "
                f"ex_supportive_date_median_relative_12m="
                f"{supportive['ex_supportive_date_median_relative_return_12m']}."
            ),
            f"- Interpretation: {supportive['interpretation']}",
            "",
            "## Stability Failure Modes",
            "",
        ]
    )
    for item in data["stability_failure_modes"]:
        lines.append(
            f"- {item['failure_mode_code']}: {item['repair_action']} "
            f"(priority {item['priority']})."
        )
    lines.extend(
        [
            "",
            "## Walk-Forward Retest Plan",
            "",
            (
                "- Required Period Controls: "
                f"{_display(data['walk_forward_retest_plan']['required_period_controls'])}"
            ),
            (
                "- Required Subsample Views: "
                f"{_display(data['walk_forward_retest_plan']['required_subsample_views'])}"
            ),
            "",
            "## What This Suggests",
            "",
            (
                "- Evidence remains held until period instability is repaired or "
                "documented."
            ),
            "- Backoffice should proceed to delayed anchor repair next.",
            "",
            "## What This Does Not Suggest",
            "",
            "- It does not prove a strategy.",
            "- It does not rank tickers.",
            "- It does not recommend buying or selling.",
            "- It does not validate investor agents.",
            "- It does not create a trade signal.",
            "- It does not justify allocation or rebalancing.",
            "",
            "## Next Work Order",
            "",
            f"- {data['recommended_next_work_order']}",
            "",
            "## Safety Notice",
            "",
            data["safety_notice"],
            "",
        ]
    )
    return "\n".join(lines)


def _csv_value(value) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return "" if value is None else str(value)


def _write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in fields})


def write_walk_forward_repair_plan_report(
    *,
    outputs_root: Path,
    outlier_repair_run_id: str | None = None,
    generated_at: datetime | None = None,
) -> WalkForwardRepairPlanFiles:
    """Load BO-003 inputs and write walk-forward repair artifacts."""
    outputs_root = Path(outputs_root)
    timestamp = generated_at or datetime.now(timezone.utc)
    manifest = load_outlier_repair_manifest(
        outputs_root=outputs_root,
        outlier_repair_run_id=outlier_repair_run_id,
    )
    selected_id = str(
        outlier_repair_run_id or manifest.get("outlier_repair_run_id") or ""
    )
    if not selected_id:
        raise ValueError("Outlier repair run ID is required.")
    outlier = (
        manifest
        if outlier_repair_run_id
        else load_outlier_repair_report(
            outputs_root=outputs_root,
            outlier_repair_run_id=selected_id,
        )
    )
    decomposition = load_backtest_driver_decomposition_report(
        outputs_root=outputs_root,
        decomposition_run_id=str(outlier.get("decomposition_run_id") or ""),
    )
    backoffice = load_backoffice_attribution_report(
        outputs_root=outputs_root,
        backoffice_attribution_run_id=str(
            outlier.get("backoffice_attribution_run_id") or ""
        ),
    )
    scorecard = load_research_scorecard_report(
        outputs_root=outputs_root,
        scorecard_run_id=str(outlier.get("scorecard_run_id") or ""),
    )
    analysis = load_expanded_trial_analysis_report(
        outputs_root=outputs_root,
        analysis_run_id=str(outlier.get("analysis_run_id") or ""),
    )
    rows = load_backtest_results(
        outputs_root=outputs_root,
        backtest_run_id=str(outlier.get("backtest_run_id") or ""),
    )
    root = outputs_root / "walk_forward_repair_plans"
    root.mkdir(parents=True, exist_ok=True)
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    run_id = base
    suffix = 2
    while (root / run_id).exists():
        run_id = f"{base}_{suffix:02d}"
        suffix += 1
    report = build_walk_forward_repair_plan(
        walk_forward_repair_run_id=run_id,
        generated_at=timestamp.isoformat(),
        outlier=outlier,
        decomposition=decomposition,
        backoffice=backoffice,
        scorecard=scorecard,
        analysis=analysis,
        rows=rows,
    )
    folder = root / run_id
    folder.mkdir(parents=True, exist_ok=False)
    markdown_path = folder / "walk_forward_repair_plan_report.md"
    json_path = folder / "walk_forward_repair_plan_report.json"
    period_path = folder / "period_stability_analysis.csv"
    cohort_path = folder / "cohort_by_period_analysis.csv"
    ex_nvda_path = folder / "ex_nvda_by_period_analysis.csv"
    failure_path = folder / "stability_failure_modes.csv"
    retest_path = folder / "walk_forward_retest_plan.json"
    markdown_path.write_text(
        render_walk_forward_repair_plan_report(report), encoding="utf-8"
    )
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(period_path, report.period_stability_analysis)
    _write_csv(cohort_path, report.cohort_by_period_analysis)
    _write_csv(ex_nvda_path, report.ex_nvda_by_period_analysis)
    _write_csv(failure_path, report.stability_failure_modes)
    retest_path.write_text(
        json.dumps(report.walk_forward_retest_plan, indent=2),
        encoding="utf-8",
    )
    latest_path = root / "latest_walk_forward_repair_plan_manifest.json"
    latest_payload = {
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
        "walk_forward_repair_status": report.walk_forward_repair_status,
        "period_count": len(report.period_stability_analysis),
        "failure_mode_count": len(report.stability_failure_modes),
        "recommended_next_work_order": report.recommended_next_work_order,
        "output_folder": str(folder),
        "report_path": str(markdown_path),
        "report_json_path": str(json_path),
        "period_csv_path": str(period_path),
        "cohort_csv_path": str(cohort_path),
        "ex_nvda_csv_path": str(ex_nvda_path),
        "failure_modes_csv_path": str(failure_path),
        "retest_plan_path": str(retest_path),
        "safety_notice": report.safety_notice,
    }
    latest_path.write_text(json.dumps(latest_payload, indent=2), encoding="utf-8")
    return WalkForwardRepairPlanFiles(
        output_folder=folder,
        markdown_path=markdown_path,
        json_path=json_path,
        period_csv_path=period_path,
        cohort_csv_path=cohort_path,
        ex_nvda_csv_path=ex_nvda_path,
        failure_modes_csv_path=failure_path,
        retest_plan_path=retest_path,
        latest_manifest_path=latest_path,
        report=report,
    )
