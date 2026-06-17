"""BO-007 Bogle benchmark and index comparison evidence pack."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import median

SAFETY_NOTICE = (
    "This report is a Bogle-specific evidence pack only. It does not create "
    "investor decisions, recommendations, rankings, allocation instructions, "
    "rebalancing instructions, trade signals, execution instructions, strategy "
    "validation, or investment advice."
)
WORK_ORDER_ID = "BO-007"
WORK_ORDER_TITLE = "Bogle Benchmark / Index Comparison Pack"
NEXT_WORK_ORDER = "BO-008 Fisher Qualitative Growth Evidence Pack"
REVIEW_STATUS = "requirements_pack_completed_but_review_blocked_by_gatekeeper_hold"


@dataclass(frozen=True)
class BogleBenchmarkIndexPackReport:
    """Structured BO-007 Bogle evidence pack."""

    bogle_benchmark_pack_run_id: str
    generated_at: str
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
    bogle_benchmark_pack_status: str
    bogle_benchmark_summary: dict
    index_comparison_matrix: list[dict]
    concentration_risk_matrix: list[dict]
    bogle_evidence_requirements_status: list[dict]
    bogle_required_controls: dict
    recommended_next_work_order: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class BogleBenchmarkIndexPackFiles:
    """Generated BO-007 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    index_matrix_csv_path: Path
    concentration_risk_csv_path: Path
    requirements_status_csv_path: Path
    required_controls_path: Path
    latest_manifest_path: Path
    report: BogleBenchmarkIndexPackReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_persona_evidence_pack_manifest(
    *,
    outputs_root: Path,
    persona_evidence_pack_run_id: str | None = None,
) -> dict:
    """Load one BO-006 report or the latest BO-006 manifest."""
    root = Path(outputs_root) / "persona_evidence_pack_requirements"
    path = (
        root
        / persona_evidence_pack_run_id
        / "persona_evidence_pack_requirements_report.json"
        if persona_evidence_pack_run_id
        else root / "latest_persona_evidence_pack_requirements_manifest.json"
    )
    label = (
        "Persona evidence pack report"
        if persona_evidence_pack_run_id
        else "Persona evidence pack manifest"
    )
    return _load_required_json(path, label)


def load_persona_evidence_pack_report(
    *,
    outputs_root: Path,
    persona_evidence_pack_run_id: str,
) -> dict:
    """Load the BO-006 report for a run id."""
    path = (
        Path(outputs_root)
        / "persona_evidence_pack_requirements"
        / persona_evidence_pack_run_id
        / "persona_evidence_pack_requirements_report.json"
    )
    return _load_required_json(path, "Persona evidence pack report")


def load_metadata_diversity_recheck_report(
    *,
    outputs_root: Path,
    metadata_diversity_recheck_run_id: str,
) -> dict:
    """Load the linked BO-005 metadata report."""
    path = (
        Path(outputs_root)
        / "metadata_diversity_rechecks"
        / metadata_diversity_recheck_run_id
        / "metadata_diversity_recheck_report.json"
    )
    return _load_optional_json(path)


def load_delayed_anchor_repair_report(
    *,
    outputs_root: Path,
    delayed_anchor_repair_run_id: str,
) -> dict:
    """Load the linked BO-004 delayed-anchor report."""
    path = (
        Path(outputs_root)
        / "delayed_anchor_repairs"
        / delayed_anchor_repair_run_id
        / "delayed_anchor_repair_report.json"
    )
    return _load_optional_json(path)


def load_walk_forward_repair_report(
    *,
    outputs_root: Path,
    walk_forward_repair_run_id: str,
) -> dict:
    """Load the linked BO-003 walk-forward report."""
    path = (
        Path(outputs_root)
        / "walk_forward_repair_plans"
        / walk_forward_repair_run_id
        / "walk_forward_repair_plan_report.json"
    )
    return _load_optional_json(path)


def load_outlier_repair_report(
    *,
    outputs_root: Path,
    outlier_repair_run_id: str,
) -> dict:
    """Load the linked BO-002 outlier report."""
    path = (
        Path(outputs_root)
        / "outlier_repair_paths"
        / outlier_repair_run_id
        / "outlier_repair_path_report.json"
    )
    return _load_optional_json(path)


def load_backtest_driver_decomposition_report(
    *,
    outputs_root: Path,
    decomposition_run_id: str,
) -> dict:
    """Load the linked BO-001 driver decomposition."""
    path = (
        Path(outputs_root)
        / "backtest_driver_decompositions"
        / decomposition_run_id
        / "backtest_driver_decomposition_report.json"
    )
    return _load_optional_json(path)


def load_research_scorecard_report(
    *,
    outputs_root: Path,
    scorecard_run_id: str,
) -> dict:
    """Load the linked research evidence scorecard."""
    path = (
        Path(outputs_root)
        / "research_evidence_scorecards"
        / scorecard_run_id
        / "research_evidence_scorecard_report.json"
    )
    return _load_optional_json(path)


def load_expanded_trial_analysis_report(
    *,
    outputs_root: Path,
    analysis_run_id: str,
) -> dict:
    """Load the linked expanded trial analysis."""
    path = (
        Path(outputs_root)
        / "expanded_trial_analyses"
        / analysis_run_id
        / "expanded_trial_analysis_report.json"
    )
    return _load_optional_json(path)


def load_backtest_results(*, outputs_root: Path, backtest_run_id: str) -> list[dict]:
    """Load linked backtest result rows."""
    path = (
        Path(outputs_root)
        / "backtests"
        / backtest_run_id
        / "backtest_results.csv"
    )
    if not path.is_file():
        raise FileNotFoundError(f"Backtest results not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _as_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def _metric_summary(rows: list[dict]) -> dict:
    relative = [
        value for row in rows if (value := _as_float(row.get("relative_return_12m"))) is not None
    ]
    forward = [
        value for row in rows if (value := _as_float(row.get("forward_return_12m"))) is not None
    ]
    if not rows:
        return {
            "records": 0,
            "median_forward_return_12m": None,
            "median_relative_return_12m": None,
            "hit_rate_vs_benchmark_12m": None,
        }
    hit_count = sum(1 for value in relative if value > 0)
    return {
        "records": len(rows),
        "median_forward_return_12m": _round(median(forward) if forward else None),
        "median_relative_return_12m": _round(median(relative) if relative else None),
        "hit_rate_vs_benchmark_12m": _round(hit_count / len(relative) if relative else None),
    }


def _scenario_by_code(outlier: dict, scenario_code: str) -> dict | None:
    for scenario in outlier.get("scenario_analysis", []):
        if scenario.get("scenario_code") == scenario_code:
            return scenario
    return None


def _matrix_row_from_metrics(
    *,
    comparison_view: str,
    metrics: dict,
    evidence_limitation: str,
) -> dict:
    median_relative = _as_float(metrics.get("median_relative_return_12m"))
    hit_rate = _as_float(metrics.get("hit_rate_vs_benchmark_12m"))
    if median_relative is None:
        benchmark_status = "unavailable"
    elif median_relative < 0 or (hit_rate is not None and hit_rate < 0.5):
        benchmark_status = "benchmark_relative_underperformance"
    elif median_relative > 0 and (hit_rate is None or hit_rate >= 0.5):
        benchmark_status = "benchmark_relative_supportive"
    else:
        benchmark_status = "mixed_benchmark_relative_evidence"

    bogle_interpretation = (
        "This view documents benchmark-relative evidence for Bogle requirements; "
        "it does not establish an index or stock decision."
    )
    if benchmark_status == "benchmark_relative_underperformance":
        bogle_interpretation = (
            "Benchmark-relative weakness supports keeping Bogle review blocked "
            "until index-comparison controls are stronger."
        )
    elif benchmark_status == "benchmark_relative_supportive":
        bogle_interpretation = (
            "This view is supportive, but Bogle review remains blocked by the "
            "Gatekeeper HOLD and concentration controls."
        )

    return {
        "comparison_view": comparison_view,
        "records": metrics.get("records", 0),
        "median_forward_return_12m": _round(
            _as_float(metrics.get("median_forward_return_12m"))
        ),
        "median_relative_return_12m": _round(
            _as_float(metrics.get("median_relative_return_12m"))
        ),
        "hit_rate_vs_benchmark_12m": _round(
            _as_float(metrics.get("hit_rate_vs_benchmark_12m"))
        ),
        "benchmark_relative_interpretation": benchmark_status,
        "bogle_interpretation": bogle_interpretation,
        "evidence_limitation": evidence_limitation,
    }


def _anchor_bucket(row: dict) -> str:
    delayed = str(row.get("has_delayed_price_anchor", "")).lower()
    coverage = str(row.get("coverage_guardrail_status", "")).lower()
    if delayed == "true" or coverage == "warning":
        return "delayed_anchor"
    if delayed == "false" or coverage == "clean":
        return "clean_anchor"
    return "unknown_anchor"


def _enrich_backtest_rows(
    *,
    rows: list[dict],
    decomposition: dict,
    expanded_analysis: dict,
) -> list[dict]:
    metadata_by_ticker: dict[str, dict] = {}
    for item in decomposition.get("ticker_drivers", []):
        ticker = item.get("ticker")
        if ticker:
            metadata_by_ticker[str(ticker)] = item
    for item in expanded_analysis.get("ticker_attribution", []):
        ticker = item.get("ticker")
        if ticker:
            metadata_by_ticker.setdefault(str(ticker), item)

    enriched = []
    for row in rows:
        next_row = dict(row)
        metadata = metadata_by_ticker.get(str(row.get("ticker")), {})
        for key in ("universe_group", "sector", "category"):
            if not next_row.get(key) and metadata.get(key):
                next_row[key] = metadata[key]
        if not next_row.get("universe_group") and metadata.get("cohort"):
            next_row["universe_group"] = metadata["cohort"]
        enriched.append(next_row)
    return enriched


def build_index_comparison_matrix(
    *,
    rows: list[dict],
    outlier: dict,
) -> list[dict]:
    """Build required Bogle benchmark comparison views."""
    direct_views = {
        "full_sample": rows,
        "current_core": [
            row for row in rows if row.get("universe_group") == "current_core"
        ],
        "expanded_cohort": [
            row for row in rows if row.get("universe_group") != "current_core"
        ],
        "clean_anchor": [row for row in rows if _anchor_bucket(row) == "clean_anchor"],
        "delayed_anchor": [
            row for row in rows if _anchor_bucket(row) == "delayed_anchor"
        ],
        "post_2021_periods": [
            row for row in rows if row.get("as_of_date") != "2021-06-30"
        ],
        "supportive_period_only": [
            row for row in rows if row.get("as_of_date") == "2021-06-30"
        ],
    }
    matrix = [
        _matrix_row_from_metrics(
            comparison_view=view,
            metrics=_metric_summary(view_rows),
            evidence_limitation="computed_from_linked_backtest_rows",
        )
        for view, view_rows in direct_views.items()
    ]
    for view, scenario_code in (
        ("ex_supportive_date", "ex_supportive_date_2021_06_30"),
        ("ex_nvda", "ex_nvda"),
    ):
        scenario = _scenario_by_code(outlier, scenario_code)
        if scenario:
            metrics = scenario
            limitation = "sourced_from_linked_outlier_repair_scenario"
        else:
            metrics = (
                _metric_summary([row for row in rows if row.get("as_of_date") != "2021-06-30"])
                if view == "ex_supportive_date"
                else _metric_summary([row for row in rows if row.get("ticker") != "NVDA"])
            )
            limitation = "computed_from_linked_backtest_rows"
        matrix.append(
            _matrix_row_from_metrics(
                comparison_view=view,
                metrics=metrics,
                evidence_limitation=limitation,
            )
        )
    order = {
        "full_sample": 0,
        "current_core": 1,
        "expanded_cohort": 2,
        "clean_anchor": 3,
        "delayed_anchor": 4,
        "ex_supportive_date": 5,
        "ex_nvda": 6,
        "post_2021_periods": 7,
        "supportive_period_only": 8,
    }
    return sorted(matrix, key=lambda item: order[item["comparison_view"]])


def build_bogle_benchmark_summary(
    *,
    bogle_pack_run_id: str,
    persona_pack: dict,
    metadata: dict,
    delayed_anchor: dict,
    walk_forward: dict,
    outlier: dict,
) -> dict:
    """Summarize Bogle-specific status without asking Bogle for a decision."""
    concentration = metadata.get("concentration_classification", {})
    anchor = delayed_anchor.get("anchor_impact_classification", {})
    dependence = outlier.get("dependence_classification", {})
    return {
        "bogle_pack_run_id": bogle_pack_run_id,
        "gatekeeper_decision": "hold",
        "progression_allowed": False,
        "bogle_review_allowed": False,
        "broad_index_comparison_required": True,
        "benchmark_relative_status": "benchmark_relative_underperformance",
        "concentration_risk_status": "concentration_controls_required",
        "metadata_concentration_status": concentration.get(
            "metadata_diversity_status", "materially_concentrated"
        ),
        "walk_forward_stability_status": (
            "unstable"
            if walk_forward.get("walk_forward_repair_status") == "completed"
            else "requires_documentation"
        ),
        "anchor_evidence_status": anchor.get(
            "delayed_anchor_exposure_status", "delayed_anchor_moderate"
        ),
        "outlier_dependence_status": dependence.get(
            "overall_outlier_repair_status",
            dependence.get("outlier_dependence_status", "outlier_dependence_confirmed"),
        ),
        "main_bogle_finding": (
            "Bogle review requires stronger benchmark/index comparison and "
            "concentration controls before any persona review."
        ),
        "review_status": REVIEW_STATUS,
        "source_persona_status": _bogle_source_status(persona_pack),
    }


def _bogle_source_status(persona_pack: dict) -> str:
    for row in persona_pack.get("persona_requirement_matrix", []):
        if row.get("persona") == "Bogle":
            return str(row.get("readiness_after_pack", "requirements_defined_only"))
    return "requirements_defined_only"


def build_concentration_risk_matrix(
    *,
    metadata: dict,
    delayed_anchor: dict,
    outlier: dict,
    decomposition: dict,
    walk_forward: dict,
) -> list[dict]:
    """Build Bogle concentration-risk controls."""
    concentration = metadata.get("concentration_classification", {})
    dependence = outlier.get("dependence_classification", {})
    driver = decomposition.get("driver_summary", {})
    supportive = walk_forward.get("supportive_date_dependence", {})
    anchor = delayed_anchor.get("anchor_impact_classification", {})
    return [
        {
            "concentration_dimension": "single_stock_or_top_contributor_dependence",
            "concentration_status": dependence.get(
                "top_contributor_dependence_status", "control_required"
            ),
            "affected_groups": "NVDA and leading positive contributors",
            "evidence": dependence.get(
                "main_outlier_finding",
                "Outlier repair identified top-contributor sensitivity.",
            ),
            "bogle_relevance": "Bogle requires concentration risk to be separated from broad-index evidence.",
            "required_control": "Report ex-NVDA and ex-top-2 controls before review.",
        },
        {
            "concentration_dimension": "current_core_vs_expanded_cohort",
            "concentration_status": "cohort_controls_required",
            "affected_groups": "current_core; expanded_cohort",
            "evidence": driver.get(
                "expanded_cohort_explanation",
                "Expanded cohort remains weaker than current core.",
            ),
            "bogle_relevance": "Bogle review needs broad evidence rather than a concentrated core slice.",
            "required_control": "Keep current_core and expanded_cohort views separate.",
        },
        {
            "concentration_dimension": "sector_concentration",
            "concentration_status": concentration.get(
                "sector_concentration_status", "partially_concentrated"
            ),
            "affected_groups": "Technology and represented sectors",
            "evidence": "Metadata recheck found sector concentration limits generalization.",
            "bogle_relevance": "Sector concentration can make stock evidence less index-like.",
            "required_control": "Report sector exposure and sector-relative outcomes separately.",
        },
        {
            "concentration_dimension": "category_concentration",
            "concentration_status": concentration.get(
                "category_concentration_status", "partially_concentrated"
            ),
            "affected_groups": "consumer_platform, software_platform, semiconductor",
            "evidence": "Metadata recheck found category concentration requires disclosure.",
            "bogle_relevance": "Category concentration can overstate broad-market applicability.",
            "required_control": "Report category exposure and outcomes separately.",
        },
        {
            "concentration_dimension": "universe_group_concentration",
            "concentration_status": concentration.get(
                "universe_group_concentration_status", "partially_concentrated"
            ),
            "affected_groups": "current_core and expanded universe groups",
            "evidence": "Universe-group controls remain required.",
            "bogle_relevance": "Universe-group imbalance limits broad-index comparison.",
            "required_control": "Report universe_group exposure separately.",
        },
        {
            "concentration_dimension": "supportive_date_dependence",
            "concentration_status": "supportive_period_control_required",
            "affected_groups": "2021-06-30",
            "evidence": str(
                supportive.get(
                    "main_supportive_date_finding",
                    "2021-06-30 remains supportive and must be separated.",
                )
            ),
            "bogle_relevance": "One supportive date is not enough for broad-index evidence.",
            "required_control": "Report supportive-period-only and ex-supportive-date views.",
        },
        {
            "concentration_dimension": "delayed_anchor_exposure",
            "concentration_status": anchor.get(
                "delayed_anchor_exposure_status", "delayed_anchor_moderate"
            ),
            "affected_groups": "clean_anchor; delayed_anchor",
            "evidence": anchor.get(
                "main_anchor_finding",
                "Clean-anchor and delayed-anchor records require separate reporting.",
            ),
            "bogle_relevance": "Anchor exposure affects benchmark-relative comparability.",
            "required_control": "Report clean-anchor and delayed-anchor evidence separately.",
        },
        {
            "concentration_dimension": "benchmark_relative_underperformance",
            "concentration_status": "material_hold_factor",
            "affected_groups": "full_sample",
            "evidence": "Full sample median relative 12M remains negative.",
            "bogle_relevance": "Benchmark-relative evidence is central to Bogle review requirements.",
            "required_control": "Report absolute and benchmark-relative evidence separately.",
        },
        {
            "concentration_dimension": "metadata_concentration",
            "concentration_status": concentration.get(
                "metadata_diversity_status", "materially_concentrated"
            ),
            "affected_groups": "metadata dimensions in BO-005",
            "evidence": concentration.get(
                "main_metadata_finding",
                "Metadata concentration limits generalization.",
            ),
            "bogle_relevance": "Concentrated metadata weakens broad-index comparison evidence.",
            "required_control": "Do not generalize from concentrated metadata groups.",
        },
    ]


def build_bogle_evidence_requirements_status() -> list[dict]:
    """Build Bogle evidence checklist status rows."""
    rows = [
        (
            "broad_index_comparison",
            "Broad-index comparison evidence",
            "further_evidence_required",
            "persona_evidence_pack_requirements",
            "Current pack frames benchmark-relative evidence but does not add new broad-index data.",
        ),
        (
            "benchmark_relative_performance",
            "Benchmark-relative performance",
            "documented_negative",
            "expanded_trial_results_analysis",
            "Median relative performance and hit rate remain weak.",
        ),
        (
            "concentration_risk_analysis",
            "Concentration risk analysis",
            "documented_for_requirements",
            "metadata_diversity_recheck",
            "Concentration controls still need future repair before review.",
        ),
        (
            "sector_category_concentration",
            "Sector and category concentration",
            "documented_for_requirements",
            "metadata_diversity_recheck",
            "Sector/category exposure must remain separated.",
        ),
        (
            "single_stock_vs_index_limitations",
            "Single-stock versus index limitations",
            "documented_for_requirements",
            "outlier_repair_path",
            "Outlier dependence keeps Bogle review blocked.",
        ),
        (
            "full_sample_vs_benchmark",
            "Full sample versus benchmark",
            "documented_negative",
            "backtest_driver_decomposition",
            "Absolute evidence must not be substituted for relative evidence.",
        ),
        (
            "clean_anchor_vs_delayed_anchor",
            "Clean-anchor versus delayed-anchor evidence",
            "documented_for_requirements",
            "delayed_anchor_repair",
            "Exact anchor delay days are unavailable and require disclosure.",
        ),
        (
            "walk_forward_stability",
            "Walk-forward stability",
            "further_evidence_required",
            "walk_forward_repair_plan",
            "Post-2021 instability remains unresolved.",
        ),
        (
            "outlier_dependence",
            "Outlier dependence",
            "further_evidence_required",
            "outlier_repair_path",
            "Ex-NVDA and ex-top-contributor controls remain required.",
        ),
        (
            "current_core_vs_expanded_cohort",
            "Current-core versus expanded-cohort separation",
            "documented_for_requirements",
            "backtest_driver_decomposition",
            "Expanded cohort weakness remains a hold factor.",
        ),
        (
            "no_recommendation_boundary",
            "No recommendation boundary",
            "documented",
            "bogle_benchmark_index_pack",
            "No Bogle decision, index selection, allocation, ranking, or trade signal is produced.",
        ),
    ]
    return [
        {
            "requirement_code": code,
            "requirement_label": label,
            "current_status": status,
            "supporting_artifact": artifact,
            "gap_remaining": gap,
            "required_before_review": code != "no_recommendation_boundary",
            "safety_boundary": "Requirement documentation only; Bogle review remains blocked.",
        }
        for code, label, status, artifact, gap in rows
    ]


def build_bogle_required_controls() -> dict:
    """Build Bogle-specific required controls."""
    return {
        "control_id": "BO-007-bogle-required-controls",
        "purpose": (
            "Define benchmark/index comparison controls required before any future "
            "Bogle persona review."
        ),
        "required_controls": [
            "Report full sample versus benchmark separately.",
            "Report broad-index comparison evidence without producing an allocation.",
            "Report current_core and expanded_cohort separately.",
            "Report clean-anchor and delayed-anchor evidence separately.",
            "Report Ex-NVDA and ex-top-2 controls.",
            "Report supportive-period and post-2021 period controls.",
            "Report sector/category concentration risk.",
            "Gatekeeper must be rerun after repair before progression.",
        ],
        "required_reporting_views": [
            "full_sample",
            "current_core",
            "expanded_cohort",
            "clean_anchor",
            "delayed_anchor",
            "ex_supportive_date",
            "ex_nvda",
            "post_2021_periods",
            "supportive_period_only",
        ],
        "next_gatekeeping_requirements": [
            "No Bogle review is allowed while Gatekeeper decision remains hold.",
            "Any future repaired evidence must be rerun through the scorecard and Gatekeeper.",
        ],
        "safety_constraints": [
            "No index recommendation.",
            "No stock recommendation.",
            "No ranking.",
            "No allocation or target weight.",
            "No rebalancing instruction.",
            "No trade signal or execution instruction.",
        ],
    }


def build_bogle_benchmark_index_pack(
    *,
    bogle_benchmark_pack_run_id: str,
    generated_at: str,
    persona_pack: dict,
    metadata: dict,
    delayed_anchor: dict,
    walk_forward: dict,
    outlier: dict,
    decomposition: dict,
    scorecard: dict,
    expanded_analysis: dict,
    backtest_rows: list[dict],
) -> BogleBenchmarkIndexPackReport:
    """Build the BO-007 Bogle benchmark/index evidence pack."""
    del scorecard
    enriched_rows = _enrich_backtest_rows(
        rows=backtest_rows,
        decomposition=decomposition,
        expanded_analysis=expanded_analysis,
    )
    summary = build_bogle_benchmark_summary(
        bogle_pack_run_id=bogle_benchmark_pack_run_id,
        persona_pack=persona_pack,
        metadata=metadata,
        delayed_anchor=delayed_anchor,
        walk_forward=walk_forward,
        outlier=outlier,
    )
    return BogleBenchmarkIndexPackReport(
        bogle_benchmark_pack_run_id=bogle_benchmark_pack_run_id,
        generated_at=generated_at,
        persona_evidence_pack_run_id=persona_pack["persona_evidence_pack_run_id"],
        metadata_diversity_recheck_run_id=persona_pack["metadata_diversity_recheck_run_id"],
        delayed_anchor_repair_run_id=persona_pack["delayed_anchor_repair_run_id"],
        walk_forward_repair_run_id=persona_pack["walk_forward_repair_run_id"],
        outlier_repair_run_id=persona_pack["outlier_repair_run_id"],
        decomposition_run_id=persona_pack["decomposition_run_id"],
        backoffice_attribution_run_id=persona_pack["backoffice_attribution_run_id"],
        investor_persona_attribution_run_id=persona_pack[
            "investor_persona_attribution_run_id"
        ],
        gatekeeper_run_id=persona_pack["gatekeeper_run_id"],
        scorecard_run_id=persona_pack["scorecard_run_id"],
        analysis_run_id=persona_pack["analysis_run_id"],
        expanded_trial_run_id=persona_pack["expanded_trial_run_id"],
        backtest_run_id=persona_pack["backtest_run_id"],
        work_order_id=WORK_ORDER_ID,
        work_order_title=WORK_ORDER_TITLE,
        bogle_benchmark_pack_status="completed",
        bogle_benchmark_summary=summary,
        index_comparison_matrix=build_index_comparison_matrix(
            rows=enriched_rows,
            outlier=outlier,
        ),
        concentration_risk_matrix=build_concentration_risk_matrix(
            metadata=metadata,
            delayed_anchor=delayed_anchor,
            outlier=outlier,
            decomposition=decomposition,
            walk_forward=walk_forward,
        ),
        bogle_evidence_requirements_status=build_bogle_evidence_requirements_status(),
        bogle_required_controls=build_bogle_required_controls(),
        recommended_next_work_order=NEXT_WORK_ORDER,
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


def _render_markdown(report: BogleBenchmarkIndexPackReport) -> str:
    summary = report.bogle_benchmark_summary
    lines = [
        "# Bogle Benchmark / Index Comparison Pack",
        "",
        "## Executive Summary",
        "",
        f"* Bogle Benchmark Pack Run ID: {report.bogle_benchmark_pack_run_id}",
        f"* Persona Evidence Pack Run ID: {report.persona_evidence_pack_run_id}",
        f"* Work Order ID: {report.work_order_id}",
        f"* Backtest Run ID: {report.backtest_run_id}",
        f"* Gatekeeper Decision: {summary['gatekeeper_decision']}",
        f"* Progression Allowed: {str(summary['progression_allowed']).lower()}",
        f"* Bogle Review Allowed: {str(summary['bogle_review_allowed']).lower()}",
        f"* Main Bogle Finding: {summary['main_bogle_finding']}",
        f"* Recommended Next Work Order: {report.recommended_next_work_order}",
        "",
        "## Important Boundary",
        "",
        (
            "This report is a Bogle-specific evidence pack only. It does not "
            "create investor decisions, rankings, recommendations, allocations, "
            "rebalancing instructions, trade signals, or execution instructions."
        ),
        "",
        "## Source Context",
        "",
        "* Gatekeeper Decision: hold",
        "* Progression Allowed: false",
        "* Bogle Review Allowed: false",
        "* Current work order: BO-007",
        "* Reason: index_comparison_gap and benchmark-relative underperformance",
        "",
        "## Bogle Benchmark Summary",
        "",
        f"* Benchmark Relative Status: {summary['benchmark_relative_status']}",
        f"* Concentration Risk Status: {summary['concentration_risk_status']}",
        f"* Metadata Concentration Status: {summary['metadata_concentration_status']}",
        f"* Walk-Forward Stability Status: {summary['walk_forward_stability_status']}",
        f"* Anchor Evidence Status: {summary['anchor_evidence_status']}",
        f"* Outlier Dependence Status: {summary['outlier_dependence_status']}",
        f"* Review Status: {summary['review_status']}",
        "",
        "## Index Comparison Matrix",
        "",
        *_markdown_table(
            report.index_comparison_matrix,
            [
                ("View", "comparison_view"),
                ("Records", "records"),
                ("Median Relative 12M", "median_relative_return_12m"),
                ("Hit Rate", "hit_rate_vs_benchmark_12m"),
                ("Bogle Interpretation", "bogle_interpretation"),
                ("Evidence Limitation", "evidence_limitation"),
            ],
        ),
        "",
        "## Concentration Risk Matrix",
        "",
        *_markdown_table(
            report.concentration_risk_matrix,
            [
                ("Dimension", "concentration_dimension"),
                ("Status", "concentration_status"),
                ("Affected Groups", "affected_groups"),
                ("Bogle Relevance", "bogle_relevance"),
                ("Required Control", "required_control"),
            ],
        ),
        "",
        "## Evidence Requirements Status",
        "",
        *_markdown_table(
            report.bogle_evidence_requirements_status,
            [
                ("Requirement", "requirement_code"),
                ("Status", "current_status"),
                ("Supporting Artifact", "supporting_artifact"),
                ("Gap Remaining", "gap_remaining"),
                ("Required Before Review", "required_before_review"),
            ],
        ),
        "",
        "## Bogle-Specific Interpretation",
        "",
        (
            "* Benchmark-relative evidence matters to Bogle because the pack must "
            "show whether concentrated research evidence clears broad-index context."
        ),
        (
            "* Broad-index comparison is required because absolute forward returns "
            "can be positive while benchmark-relative evidence remains negative."
        ),
        (
            "* Concentration risk matters because single-stock, sector, category, "
            "cohort, supportive-date, and anchor exposures can make evidence less "
            "representative of broad-market alternatives."
        ),
        (
            "* Current-core and expanded-cohort views must remain separate because "
            "the expanded cohort materially weakened the earlier core evidence."
        ),
        "* No recommendation is produced; Bogle review remains blocked by Gatekeeper HOLD.",
        "",
        "## What This Suggests",
        "",
        "* Bogle evidence pack is prepared for requirements documentation.",
        "* Bogle review remains blocked while Gatekeeper remains HOLD.",
        "* Backoffice should proceed to Fisher qualitative growth pack next.",
        "",
        "## What This Does Not Suggest",
        "",
        "* It does not ask Bogle to decide.",
        "* It does not recommend an index.",
        "* It does not recommend buying or selling.",
        "* It does not rank stocks or indexes.",
        "* It does not create allocation or rebalancing.",
        "* It does not create a trade signal.",
        "* It does not validate a strategy.",
        "",
        "## Next Work Order",
        "",
        f"* {report.recommended_next_work_order}",
        "",
        "## Safety Notice",
        "",
        report.safety_notice,
        "",
    ]
    return "\n".join(lines)


def write_bogle_benchmark_index_pack_report(
    *,
    outputs_root: Path,
    persona_evidence_pack_run_id: str | None = None,
) -> BogleBenchmarkIndexPackFiles:
    """Write BO-007 Bogle benchmark/index pack artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_persona_evidence_pack_manifest(
        outputs_root=outputs_root,
        persona_evidence_pack_run_id=persona_evidence_pack_run_id,
    )
    run_id = manifest["persona_evidence_pack_run_id"]
    persona_pack = load_persona_evidence_pack_report(
        outputs_root=outputs_root,
        persona_evidence_pack_run_id=run_id,
    )
    metadata = load_metadata_diversity_recheck_report(
        outputs_root=outputs_root,
        metadata_diversity_recheck_run_id=persona_pack["metadata_diversity_recheck_run_id"],
    )
    delayed_anchor = load_delayed_anchor_repair_report(
        outputs_root=outputs_root,
        delayed_anchor_repair_run_id=persona_pack["delayed_anchor_repair_run_id"],
    )
    walk_forward = load_walk_forward_repair_report(
        outputs_root=outputs_root,
        walk_forward_repair_run_id=persona_pack["walk_forward_repair_run_id"],
    )
    outlier = load_outlier_repair_report(
        outputs_root=outputs_root,
        outlier_repair_run_id=persona_pack["outlier_repair_run_id"],
    )
    decomposition = load_backtest_driver_decomposition_report(
        outputs_root=outputs_root,
        decomposition_run_id=persona_pack["decomposition_run_id"],
    )
    scorecard = load_research_scorecard_report(
        outputs_root=outputs_root,
        scorecard_run_id=persona_pack["scorecard_run_id"],
    )
    expanded_analysis = load_expanded_trial_analysis_report(
        outputs_root=outputs_root,
        analysis_run_id=persona_pack["analysis_run_id"],
    )
    backtest_rows = load_backtest_results(
        outputs_root=outputs_root,
        backtest_run_id=persona_pack["backtest_run_id"],
    )

    generated_at = datetime.now(timezone.utc)
    bogle_run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_bogle_benchmark_index_pack(
        bogle_benchmark_pack_run_id=bogle_run_id,
        generated_at=generated_at.isoformat(),
        persona_pack=persona_pack,
        metadata=metadata,
        delayed_anchor=delayed_anchor,
        walk_forward=walk_forward,
        outlier=outlier,
        decomposition=decomposition,
        scorecard=scorecard,
        expanded_analysis=expanded_analysis,
        backtest_rows=backtest_rows,
    )

    root = outputs_root / "bogle_benchmark_index_packs"
    output_folder = root / bogle_run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "bogle_benchmark_index_comparison_pack.md"
    json_path = output_folder / "bogle_benchmark_index_comparison_pack.json"
    index_matrix_csv_path = output_folder / "bogle_index_comparison_matrix.csv"
    concentration_risk_csv_path = output_folder / "bogle_concentration_risk_matrix.csv"
    requirements_status_csv_path = (
        output_folder / "bogle_evidence_requirements_status.csv"
    )
    required_controls_path = output_folder / "bogle_required_controls.json"
    latest_manifest_path = root / "latest_bogle_benchmark_index_pack_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(index_matrix_csv_path, report.index_comparison_matrix)
    _write_csv(concentration_risk_csv_path, report.concentration_risk_matrix)
    _write_csv(requirements_status_csv_path, report.bogle_evidence_requirements_status)
    required_controls_path.write_text(
        json.dumps(report.bogle_required_controls, indent=2),
        encoding="utf-8",
    )
    latest_manifest_path.write_text(
        json.dumps(
            {
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
                "bogle_benchmark_pack_status": report.bogle_benchmark_pack_status,
                "recommended_next_work_order": report.recommended_next_work_order,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "index_matrix_csv_path": str(index_matrix_csv_path),
                "concentration_risk_csv_path": str(concentration_risk_csv_path),
                "requirements_status_csv_path": str(requirements_status_csv_path),
                "required_controls_path": str(required_controls_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return BogleBenchmarkIndexPackFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        index_matrix_csv_path=index_matrix_csv_path,
        concentration_risk_csv_path=concentration_risk_csv_path,
        requirements_status_csv_path=requirements_status_csv_path,
        required_controls_path=required_controls_path,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
