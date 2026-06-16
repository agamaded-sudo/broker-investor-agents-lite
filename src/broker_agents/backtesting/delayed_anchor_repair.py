"""BO-004 delayed anchor exposure repair for held research evidence."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean, median

SAFETY_NOTICE = (
    "This report analyzes delayed anchor exposure and research repair only. It "
    "does not create an investment decision, recommendation, ranking, "
    "allocation instruction, rebalancing instruction, trade signal, execution "
    "instruction, strategy validation, or investment advice."
)
WORK_ORDER_ID = "BO-004"
WORK_ORDER_TITLE = "Delayed Anchor Exposure Repair"
NEXT_WORK_ORDER = "BO-005 Metadata Diversity Recheck"


@dataclass(frozen=True)
class DelayedAnchorRepairReport:
    """Structured BO-004 delayed anchor repair result."""

    delayed_anchor_repair_run_id: str
    generated_at: str
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
    delayed_anchor_repair_status: str
    anchor_exposure_analysis: list[dict]
    period_anchor_attribution: list[dict]
    cohort_anchor_attribution: list[dict]
    anchor_impact_classification: dict
    delayed_anchor_retest_controls: dict
    recommended_next_work_order: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class DelayedAnchorRepairFiles:
    """Generated BO-004 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    anchor_csv_path: Path
    period_csv_path: Path
    cohort_csv_path: Path
    retest_controls_path: Path
    latest_manifest_path: Path
    report: DelayedAnchorRepairReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_walk_forward_repair_manifest(
    *,
    outputs_root: Path,
    walk_forward_repair_run_id: str | None = None,
) -> dict:
    """Load one BO-003 report or the latest BO-003 manifest."""
    root = Path(outputs_root) / "walk_forward_repair_plans"
    path = (
        root
        / str(walk_forward_repair_run_id)
        / "walk_forward_repair_plan_report.json"
        if walk_forward_repair_run_id
        else root / "latest_walk_forward_repair_plan_manifest.json"
    )
    payload = _load_required_json(path, "Walk-forward repair manifest")
    payload["_manifest_path"] = str(path)
    return payload


def load_walk_forward_repair_report(
    *, outputs_root: Path, walk_forward_repair_run_id: str
) -> dict:
    """Load a complete BO-003 walk-forward repair report."""
    path = (
        Path(outputs_root)
        / "walk_forward_repair_plans"
        / str(walk_forward_repair_run_id)
        / "walk_forward_repair_plan_report.json"
    )
    return _load_required_json(path, "Walk-forward repair report")


def load_outlier_repair_report(
    *, outputs_root: Path, outlier_repair_run_id: str
) -> dict:
    """Load linked BO-002 outlier repair context if available."""
    return _load_optional_json(
        Path(outputs_root)
        / "outlier_repair_paths"
        / str(outlier_repair_run_id)
        / "outlier_repair_path_report.json"
    )


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


def _as_bool_value(value: object) -> bool | None:
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
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
        item["anchor_bucket"] = _anchor_bucket(item)
        enriched.append(item)
    return enriched


def _anchor_bucket(row: dict) -> str:
    delayed = _as_bool_value(row.get("has_delayed_price_anchor"))
    if delayed is True:
        return "delayed_anchor"
    if delayed is False:
        return "clean_anchor"
    label = str(row.get("coverage_quality_label") or "").lower()
    if "delayed" in label:
        return "delayed_anchor"
    if label == "clean" or row.get("coverage_guardrail_status") == "clean":
        return "clean_anchor"
    return "unknown_anchor"


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


def _anchor_columns_available(rows: list[dict]) -> bool:
    return any("has_delayed_price_anchor" in row for row in rows)


def _exact_delay_days_available(rows: list[dict]) -> bool:
    delay_columns = {
        "price_anchor_delay_days",
        "anchor_delay_days",
        "price_start_delay_days",
    }
    return any(any(column in row and row.get(column) for column in delay_columns) for row in rows)


def analyze_anchor_exposure(rows: list[dict], analysis: dict) -> list[dict]:
    """Create anchor bucket exposure analysis."""
    enriched = _enrich_rows(rows, analysis)
    buckets = ["full_sample", "clean_anchor", "delayed_anchor", "unknown_anchor"]
    output = []
    for bucket in buckets:
        bucket_rows = enriched if bucket == "full_sample" else [
            row for row in enriched if row["anchor_bucket"] == bucket
        ]
        summary = _metric_summary(bucket_rows)
        output.append(
            {
                "anchor_bucket": bucket,
                "anchor_quality_label": bucket,
                **summary,
                "affected_periods": sorted(
                    {str(row.get("signal_date")) for row in bucket_rows}
                ),
                "affected_cohorts": sorted(
                    {str(row.get("cohort")) for row in bucket_rows}
                ),
                "interpretation": _interpret_anchor_bucket(bucket, summary),
            }
        )
    return output


def _interpret_anchor_bucket(bucket: str, summary: dict) -> str:
    if bucket == "full_sample":
        return "Full sample mixes anchor exposure and must remain disclosed."
    if summary["records"] == 0:
        return f"{bucket} has no available records in this run."
    if bucket == "clean_anchor":
        return "Clean-anchor evidence must be reported separately."
    if bucket == "delayed_anchor":
        return "Delayed-anchor evidence requires separate repair controls."
    return "Anchor detail is insufficient for these records."


def _anchor_counts(rows: list[dict]) -> dict:
    return {
        "clean_anchor_records": sum(row["anchor_bucket"] == "clean_anchor" for row in rows),
        "delayed_anchor_records": sum(
            row["anchor_bucket"] == "delayed_anchor" for row in rows
        ),
        "unknown_anchor_records": sum(
            row["anchor_bucket"] == "unknown_anchor" for row in rows
        ),
    }


def _anchor_effect_label(summary: dict, clean: dict, delayed: dict, unknown: int) -> str:
    if unknown > 0:
        return "unknown_anchor_exposure"
    if clean["records"] == 0 and delayed["records"] == 0:
        return "insufficient_anchor_detail"
    clean_rel = clean.get("median_relative_return_12m")
    delayed_rel = delayed.get("median_relative_return_12m")
    if clean_rel is not None and delayed_rel is not None and delayed_rel < clean_rel:
        return "delayed_anchor_drag"
    if clean_rel is not None and clean_rel > 0:
        return "clean_anchor_supported"
    if delayed["records"] > 0:
        return "delayed_anchor_not_primary"
    return "insufficient_anchor_detail"


def _interpret_anchor_effect(label: str) -> str:
    if label == "clean_anchor_supported":
        return "Clean-anchor evidence is stronger in this slice."
    if label == "delayed_anchor_drag":
        return "Delayed-anchor evidence is weaker than clean-anchor evidence."
    if label == "delayed_anchor_not_primary":
        return "Delayed-anchor exposure is present but not the sole driver."
    if label == "unknown_anchor_exposure":
        return "Some records lack enough anchor detail for full attribution."
    return "Anchor detail is insufficient for this slice."


def attribute_anchor_effect_by_period(
    rows: list[dict], analysis: dict
) -> list[dict]:
    """Create period-level anchor attribution."""
    enriched = _enrich_rows(rows, analysis)
    output = []
    for date, date_rows in sorted(_group(enriched, "signal_date").items()):
        summary = _metric_summary(date_rows)
        clean = _metric_summary(
            [row for row in date_rows if row["anchor_bucket"] == "clean_anchor"]
        )
        delayed = _metric_summary(
            [row for row in date_rows if row["anchor_bucket"] == "delayed_anchor"]
        )
        counts = _anchor_counts(date_rows)
        label = _anchor_effect_label(summary, clean, delayed, counts["unknown_anchor_records"])
        output.append(
            {
                "as_of_date": date,
                "records": summary["records"],
                **counts,
                "median_relative_return_12m": summary["median_relative_return_12m"],
                "clean_anchor_median_relative_return_12m": clean[
                    "median_relative_return_12m"
                ],
                "delayed_anchor_median_relative_return_12m": delayed[
                    "median_relative_return_12m"
                ],
                "hit_rate_vs_benchmark_12m": summary["hit_rate_vs_benchmark_12m"],
                "clean_anchor_hit_rate_vs_benchmark_12m": clean[
                    "hit_rate_vs_benchmark_12m"
                ],
                "delayed_anchor_hit_rate_vs_benchmark_12m": delayed[
                    "hit_rate_vs_benchmark_12m"
                ],
                "anchor_effect_label": label,
                "interpretation": _interpret_anchor_effect(label),
            }
        )
    return output


def attribute_anchor_effect_by_cohort(
    rows: list[dict], analysis: dict
) -> list[dict]:
    """Create cohort-level anchor attribution."""
    enriched = _enrich_rows(rows, analysis)
    output = []
    cohort_rows = dict(_group(enriched, "cohort"))
    cohort_rows["full_expanded_universe"] = enriched
    for cohort in ("current_core", "expanded_cohort", "full_expanded_universe"):
        rows_for_cohort = cohort_rows.get(cohort, [])
        summary = _metric_summary(rows_for_cohort)
        clean = _metric_summary(
            [
                row
                for row in rows_for_cohort
                if row["anchor_bucket"] == "clean_anchor"
            ]
        )
        delayed = _metric_summary(
            [
                row
                for row in rows_for_cohort
                if row["anchor_bucket"] == "delayed_anchor"
            ]
        )
        counts = _anchor_counts(rows_for_cohort)
        label = _anchor_effect_label(summary, clean, delayed, counts["unknown_anchor_records"])
        output.append(
            {
                "cohort": cohort,
                "records": summary["records"],
                **counts,
                "median_relative_return_12m": summary["median_relative_return_12m"],
                "clean_anchor_median_relative_return_12m": clean[
                    "median_relative_return_12m"
                ],
                "delayed_anchor_median_relative_return_12m": delayed[
                    "median_relative_return_12m"
                ],
                "hit_rate_vs_benchmark_12m": summary["hit_rate_vs_benchmark_12m"],
                "clean_anchor_hit_rate_vs_benchmark_12m": clean[
                    "hit_rate_vs_benchmark_12m"
                ],
                "delayed_anchor_hit_rate_vs_benchmark_12m": delayed[
                    "hit_rate_vs_benchmark_12m"
                ],
                "anchor_effect_label": label,
                "interpretation": _interpret_anchor_effect(label),
            }
        )
    return output


def compare_clean_anchor_vs_delayed_anchor(anchor_analysis: list[dict]) -> dict:
    """Compare clean-anchor and delayed-anchor buckets."""
    by_bucket = {item["anchor_bucket"]: item for item in anchor_analysis}
    clean = by_bucket.get("clean_anchor", {})
    delayed = by_bucket.get("delayed_anchor", {})
    clean_rel = clean.get("median_relative_return_12m")
    delayed_rel = delayed.get("median_relative_return_12m")
    return {
        "clean_anchor_records": clean.get("records", 0),
        "delayed_anchor_records": delayed.get("records", 0),
        "clean_anchor_median_relative_return_12m": clean_rel,
        "delayed_anchor_median_relative_return_12m": delayed_rel,
        "relative_gap_delayed_minus_clean": _round(
            delayed_rel - clean_rel
            if clean_rel is not None and delayed_rel is not None
            else None
        ),
    }


def _anchor_classification(
    *,
    rows: list[dict],
    anchor_analysis: list[dict],
    period_attribution: list[dict],
) -> dict:
    comparison = compare_clean_anchor_vs_delayed_anchor(anchor_analysis)
    delayed_records = int(comparison["delayed_anchor_records"] or 0)
    clean_records = int(comparison["clean_anchor_records"] or 0)
    gap = comparison["relative_gap_delayed_minus_clean"]
    exact_days = _exact_delay_days_available(rows)
    if delayed_records == 0:
        exposure = "delayed_anchor_limited"
    elif gap is not None and gap < -0.05:
        exposure = "delayed_anchor_material"
    else:
        exposure = "delayed_anchor_moderate"
    clean_status = "clean_anchor_available" if clean_records > 0 else "clean_anchor_absent"
    delayed_status = (
        "delayed_anchor_available" if delayed_records > 0 else "delayed_anchor_absent"
    )
    sufficiency = (
        "anchor_buckets_available_without_exact_delay_days"
        if _anchor_columns_available(rows) and not exact_days
        else "exact_anchor_delay_available"
        if exact_days
        else "insufficient_anchor_detail"
    )
    effect_on_hold = (
        "anchor_effect_supports_continued_hold"
        if exposure in {"delayed_anchor_material", "delayed_anchor_moderate"}
        else "anchor_effect_not_primary_hold_driver"
    )
    affected_periods = [
        item["as_of_date"]
        for item in period_attribution
        if item["delayed_anchor_records"] > 0
    ]
    return {
        "delayed_anchor_exposure_status": exposure,
        "clean_anchor_evidence_status": clean_status,
        "delayed_anchor_evidence_status": delayed_status,
        "anchor_data_sufficiency_status": sufficiency,
        "anchor_effect_on_hold_status": effect_on_hold,
        "exact_anchor_delay_days_available": exact_days,
        "affected_delayed_anchor_periods": affected_periods,
        "clean_vs_delayed_anchor_comparison": comparison,
        "main_anchor_finding": (
            "Anchor bucket fields are available, but exact anchor delay days "
            "are not available; clean-anchor and delayed-anchor evidence must "
            "be reported separately before any future gatekeeper rerun."
        ),
        "recommended_next_work_order": NEXT_WORK_ORDER,
    }


def build_delayed_anchor_retest_controls() -> dict:
    """Create BO-004 delayed-anchor retest controls."""
    return {
        "retest_control_id": "BO-004-delayed-anchor-retest-controls",
        "purpose": (
            "Define controls for separating clean-anchor, delayed-anchor, and "
            "unknown-anchor evidence before any future research gate."
        ),
        "required_anchor_controls": [
            "Report clean-anchor and delayed-anchor records separately.",
            "Report anchor exposure by date.",
            "Report anchor exposure by cohort.",
            "Report anchor exposure by ticker if available.",
            "Do not mix clean and delayed anchor evidence without disclosure.",
            "No future price information may be introduced.",
            "Gatekeeper must be rerun after repair before progression.",
        ],
        "required_reporting_views": [
            "full_sample",
            "clean_anchor",
            "delayed_anchor",
            "unknown_anchor",
            "anchor_exposure_by_date",
            "anchor_exposure_by_cohort",
        ],
        "minimum_data_requirements": [
            "Anchor bucket fields must be present or unknown_anchor must be used.",
            "Exact delay days must not be fabricated.",
            "Clean-anchor and delayed-anchor evidence must remain separate.",
        ],
        "local_coverage_requirements": [
            "Acquire local point-in-time price anchor coverage where feasible.",
            "Validate price anchors locally before any rerun.",
        ],
        "next_gatekeeping_requirements": [
            "Gatekeeper must be rerun after repair before progression.",
            "Progression remains blocked while gatekeeper decision is hold.",
        ],
        "safety_constraints": [
            "Do not rerun investor agents for this repair.",
            "Do not change original backtest results.",
            "Do not create recommendations, rankings, allocations, or trade signals.",
        ],
    }


def build_delayed_anchor_repair(
    *,
    delayed_anchor_repair_run_id: str,
    generated_at: str,
    walk_forward: dict,
    outlier: dict,
    decomposition: dict,
    backoffice: dict,
    scorecard: dict,
    analysis: dict,
    rows: list[dict],
) -> DelayedAnchorRepairReport:
    """Build the full BO-004 delayed anchor repair report."""
    anchor_analysis = analyze_anchor_exposure(rows, analysis)
    period_attribution = attribute_anchor_effect_by_period(rows, analysis)
    cohort_attribution = attribute_anchor_effect_by_cohort(rows, analysis)
    classification = _anchor_classification(
        rows=rows,
        anchor_analysis=anchor_analysis,
        period_attribution=period_attribution,
    )
    controls = build_delayed_anchor_retest_controls()
    return DelayedAnchorRepairReport(
        delayed_anchor_repair_run_id=delayed_anchor_repair_run_id,
        generated_at=generated_at,
        walk_forward_repair_run_id=str(
            walk_forward.get("walk_forward_repair_run_id") or ""
        ),
        outlier_repair_run_id=str(walk_forward.get("outlier_repair_run_id") or ""),
        decomposition_run_id=str(walk_forward.get("decomposition_run_id") or ""),
        backoffice_attribution_run_id=str(
            walk_forward.get("backoffice_attribution_run_id") or ""
        ),
        investor_persona_attribution_run_id=str(
            walk_forward.get("investor_persona_attribution_run_id") or ""
        ),
        gatekeeper_run_id=str(walk_forward.get("gatekeeper_run_id") or ""),
        scorecard_run_id=str(walk_forward.get("scorecard_run_id") or ""),
        analysis_run_id=str(walk_forward.get("analysis_run_id") or ""),
        expanded_trial_run_id=str(walk_forward.get("expanded_trial_run_id") or ""),
        backtest_run_id=str(walk_forward.get("backtest_run_id") or ""),
        work_order_id=WORK_ORDER_ID,
        work_order_title=WORK_ORDER_TITLE,
        delayed_anchor_repair_status="completed",
        anchor_exposure_analysis=anchor_analysis,
        period_anchor_attribution=period_attribution,
        cohort_anchor_attribution=cohort_attribution,
        anchor_impact_classification=classification,
        delayed_anchor_retest_controls=controls,
        recommended_next_work_order=NEXT_WORK_ORDER,
    )


def _display(value) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "None"
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return "" if value is None else str(value)


def render_delayed_anchor_repair_report(report: DelayedAnchorRepairReport) -> str:
    """Render BO-004 as Markdown."""
    data = report.to_dict()
    classification = data["anchor_impact_classification"]
    lines = [
        "# Delayed Anchor Exposure Repair Report",
        "",
        "## Executive Summary",
        "",
        f"- Delayed Anchor Repair Run ID: {data['delayed_anchor_repair_run_id']}",
        f"- Walk-Forward Repair Run ID: {data['walk_forward_repair_run_id']}",
        f"- Work Order ID: {data['work_order_id']}",
        f"- Backtest Run ID: {data['backtest_run_id']}",
        f"- Main Anchor Finding: {classification['main_anchor_finding']}",
        (
            "- Anchor Data Sufficiency: "
            f"{classification['anchor_data_sufficiency_status']}"
        ),
        f"- Recommended Next Work Order: {data['recommended_next_work_order']}",
        "",
        "## Important Boundary",
        "",
        (
            "This report analyzes delayed anchor exposure and research repair "
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
        "- Reason: delayed anchor effect.",
        "",
        "## Anchor Exposure Analysis",
        "",
        "| Anchor Bucket | Records | Median Relative 12M | Hit Rate | Interpretation |",
        "|---|---:|---:|---:|---|",
    ]
    for item in data["anchor_exposure_analysis"]:
        lines.append(
            f"| {item['anchor_bucket']} | {item['records']} | "
            f"{item['median_relative_return_12m']} | "
            f"{item['hit_rate_vs_benchmark_12m']} | {item['interpretation']} |"
        )
    lines.extend(
        [
            "",
            "## Period Anchor Attribution",
            "",
            (
                "| Date | Records | Clean Anchor | Delayed Anchor | Unknown Anchor | "
                "Anchor Effect | Interpretation |"
            ),
            "|---|---:|---:|---:|---:|---|---|",
        ]
    )
    for item in data["period_anchor_attribution"]:
        lines.append(
            f"| {item['as_of_date']} | {item['records']} | "
            f"{item['clean_anchor_records']} | "
            f"{item['delayed_anchor_records']} | "
            f"{item['unknown_anchor_records']} | "
            f"{item['anchor_effect_label']} | {item['interpretation']} |"
        )
    lines.extend(
        [
            "",
            "## Cohort Anchor Attribution",
            "",
            (
                "| Cohort | Records | Clean Anchor | Delayed Anchor | Unknown Anchor | "
                "Anchor Effect | Interpretation |"
            ),
            "|---|---:|---:|---:|---:|---|---|",
        ]
    )
    for item in data["cohort_anchor_attribution"]:
        lines.append(
            f"| {item['cohort']} | {item['records']} | "
            f"{item['clean_anchor_records']} | "
            f"{item['delayed_anchor_records']} | "
            f"{item['unknown_anchor_records']} | "
            f"{item['anchor_effect_label']} | {item['interpretation']} |"
        )
    lines.extend(
        [
            "",
            "## Anchor Impact Classification",
            "",
            (
                "- Delayed Anchor Exposure Status: "
                f"{classification['delayed_anchor_exposure_status']}"
            ),
            (
                "- Anchor Data Sufficiency Status: "
                f"{classification['anchor_data_sufficiency_status']}"
            ),
            (
                "- Anchor Effect on Hold Status: "
                f"{classification['anchor_effect_on_hold_status']}"
            ),
            (
                "- Exact Anchor Delay Days Available: "
                f"{str(classification['exact_anchor_delay_days_available']).lower()}"
            ),
            "- Exact delay days were not fabricated.",
            "",
            "## Retest Controls",
            "",
            (
                "- Required Anchor Controls: "
                f"{_display(data['delayed_anchor_retest_controls']['required_anchor_controls'])}"
            ),
            (
                "- Required Reporting Views: "
                f"{_display(data['delayed_anchor_retest_controls']['required_reporting_views'])}"
            ),
            "",
            "## What This Suggests",
            "",
            (
                "- Evidence remains held until delayed anchor exposure is "
                "separated and documented."
            ),
            "- Backoffice should proceed to metadata diversity recheck next.",
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


def write_delayed_anchor_repair_report(
    *,
    outputs_root: Path,
    walk_forward_repair_run_id: str | None = None,
    generated_at: datetime | None = None,
) -> DelayedAnchorRepairFiles:
    """Load BO-004 inputs and write delayed anchor repair artifacts."""
    outputs_root = Path(outputs_root)
    timestamp = generated_at or datetime.now(timezone.utc)
    manifest = load_walk_forward_repair_manifest(
        outputs_root=outputs_root,
        walk_forward_repair_run_id=walk_forward_repair_run_id,
    )
    selected_id = str(
        walk_forward_repair_run_id
        or manifest.get("walk_forward_repair_run_id")
        or ""
    )
    if not selected_id:
        raise ValueError("Walk-forward repair run ID is required.")
    walk_forward = (
        manifest
        if walk_forward_repair_run_id
        else load_walk_forward_repair_report(
            outputs_root=outputs_root,
            walk_forward_repair_run_id=selected_id,
        )
    )
    outlier = load_outlier_repair_report(
        outputs_root=outputs_root,
        outlier_repair_run_id=str(walk_forward.get("outlier_repair_run_id") or ""),
    )
    decomposition = load_backtest_driver_decomposition_report(
        outputs_root=outputs_root,
        decomposition_run_id=str(walk_forward.get("decomposition_run_id") or ""),
    )
    backoffice = load_backoffice_attribution_report(
        outputs_root=outputs_root,
        backoffice_attribution_run_id=str(
            walk_forward.get("backoffice_attribution_run_id") or ""
        ),
    )
    scorecard = load_research_scorecard_report(
        outputs_root=outputs_root,
        scorecard_run_id=str(walk_forward.get("scorecard_run_id") or ""),
    )
    analysis = load_expanded_trial_analysis_report(
        outputs_root=outputs_root,
        analysis_run_id=str(walk_forward.get("analysis_run_id") or ""),
    )
    rows = load_backtest_results(
        outputs_root=outputs_root,
        backtest_run_id=str(walk_forward.get("backtest_run_id") or ""),
    )
    root = outputs_root / "delayed_anchor_repairs"
    root.mkdir(parents=True, exist_ok=True)
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    run_id = base
    suffix = 2
    while (root / run_id).exists():
        run_id = f"{base}_{suffix:02d}"
        suffix += 1
    report = build_delayed_anchor_repair(
        delayed_anchor_repair_run_id=run_id,
        generated_at=timestamp.isoformat(),
        walk_forward=walk_forward,
        outlier=outlier,
        decomposition=decomposition,
        backoffice=backoffice,
        scorecard=scorecard,
        analysis=analysis,
        rows=rows,
    )
    folder = root / run_id
    folder.mkdir(parents=True, exist_ok=False)
    markdown_path = folder / "delayed_anchor_repair_report.md"
    json_path = folder / "delayed_anchor_repair_report.json"
    anchor_path = folder / "anchor_exposure_analysis.csv"
    period_path = folder / "period_anchor_attribution.csv"
    cohort_path = folder / "cohort_anchor_attribution.csv"
    controls_path = folder / "delayed_anchor_retest_controls.json"
    markdown_path.write_text(
        render_delayed_anchor_repair_report(report), encoding="utf-8"
    )
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(anchor_path, report.anchor_exposure_analysis)
    _write_csv(period_path, report.period_anchor_attribution)
    _write_csv(cohort_path, report.cohort_anchor_attribution)
    controls_path.write_text(
        json.dumps(report.delayed_anchor_retest_controls, indent=2),
        encoding="utf-8",
    )
    latest_path = root / "latest_delayed_anchor_repair_manifest.json"
    latest_payload = {
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
        "delayed_anchor_repair_status": report.delayed_anchor_repair_status,
        "anchor_data_sufficiency_status": report.anchor_impact_classification[
            "anchor_data_sufficiency_status"
        ],
        "recommended_next_work_order": report.recommended_next_work_order,
        "output_folder": str(folder),
        "report_path": str(markdown_path),
        "report_json_path": str(json_path),
        "anchor_csv_path": str(anchor_path),
        "period_csv_path": str(period_path),
        "cohort_csv_path": str(cohort_path),
        "retest_controls_path": str(controls_path),
        "safety_notice": report.safety_notice,
    }
    latest_path.write_text(json.dumps(latest_payload, indent=2), encoding="utf-8")
    return DelayedAnchorRepairFiles(
        output_folder=folder,
        markdown_path=markdown_path,
        json_path=json_path,
        anchor_csv_path=anchor_path,
        period_csv_path=period_path,
        cohort_csv_path=cohort_path,
        retest_controls_path=controls_path,
        latest_manifest_path=latest_path,
        report=report,
    )
