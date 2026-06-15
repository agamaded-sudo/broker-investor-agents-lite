"""Attribution analysis for a completed expanded readiness trial."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import median

import yaml

SAFETY_NOTICE = (
    "This expanded trial analysis is research-only. It is not a "
    "recommendation, ranking, allocation instruction, rebalancing "
    "instruction, trade signal, execution instruction, or investment advice."
)
NEXT_RESEARCH_ACTION = "build_research_evidence_scorecard"


@dataclass(frozen=True)
class ExpandedTrialAnalysisReport:
    """Structured attribution analysis for an expanded readiness trial."""

    analysis_run_id: str
    generated_at: str
    expanded_trial_run_id: str
    backtest_run_id: str
    prior_backtest_run_id: str
    analysis_status: str
    source_reports: dict
    ticker_attribution: list[dict]
    sector_attribution: list[dict]
    category_attribution: list[dict]
    universe_group_attribution: list[dict]
    date_attribution: list[dict]
    clean_warning_attribution: list[dict]
    metadata_diversity_recheck: dict
    prior_trial_comparison: dict
    expanded_trial_instability_explanation: dict
    next_research_action: str = NEXT_RESEARCH_ACTION
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class ExpandedTrialAnalysisFiles:
    """Generated analysis files and report content."""

    analysis_folder: Path
    markdown_path: Path
    json_path: Path
    ticker_csv_path: Path
    sector_csv_path: Path
    category_csv_path: Path
    universe_group_csv_path: Path
    date_csv_path: Path
    clean_warning_csv_path: Path
    latest_manifest_path: Path
    report: ExpandedTrialAnalysisReport


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict:
    if not path.is_file():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def load_expanded_trial_manifest(
    *,
    outputs_root: Path,
    expanded_trial_run_id: str | None = None,
) -> dict:
    """Load an explicit expanded trial summary or the latest manifest."""
    root = Path(outputs_root) / "expanded_ticker_trials"
    if expanded_trial_run_id:
        path = (
            root
            / str(expanded_trial_run_id)
            / "expanded_ticker_trial_summary.json"
        )
    else:
        path = root / "latest_expanded_ticker_trial_manifest.json"
    if not path.is_file():
        raise FileNotFoundError(f"Expanded trial manifest not found: {path}")
    payload = _load_json(path)
    payload["_manifest_path"] = str(path)
    return payload


def load_backtest_results(path: Path) -> list[dict]:
    """Load complete result rows from an existing backtest CSV."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Backtest results not found: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_trial_ledger(path: Path) -> list[dict]:
    """Load an existing trial ledger when supplemental metadata is needed."""
    path = Path(path)
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _float(row: dict, field: str) -> float | None:
    value = row.get(field)
    if value in {None, "", "Missing"}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bool(row: dict, field: str) -> bool:
    return str(row.get(field) or "").strip().lower() in {"1", "true", "yes"}


def _median(rows: list[dict], field: str) -> float | None:
    values = [value for row in rows if (value := _float(row, field)) is not None]
    return round(median(values), 6) if values else None


def _rate(rows: list[dict], field: str, *, threshold: float = 0.0) -> float | None:
    values = [value for row in rows if (value := _float(row, field)) is not None]
    if not values:
        return None
    return round(sum(value > threshold for value in values) / len(values), 6)


def _summarize_rows(rows: list[dict]) -> dict:
    clean = [
        row
        for row in rows
        if row.get("coverage_guardrail_status") == "clean"
        or row.get("coverage_quality_label") == "clean"
    ]
    drawdowns = [
        value
        for row in rows
        if (value := _float(row, "max_drawdown_12m")) is not None
    ]
    return {
        "records": len(rows),
        "clean_records": len(clean),
        "warning_records": len(rows) - len(clean),
        "median_forward_return_12m": _median(rows, "forward_return_12m"),
        "median_relative_return_12m": _median(rows, "relative_return_12m"),
        "hit_rate_vs_benchmark_12m": _rate(rows, "relative_return_12m"),
        "worst_max_drawdown_12m": min(drawdowns) if drawdowns else None,
    }


def _contribution_label(summary: dict) -> str:
    records = int(summary.get("records") or 0)
    relative = summary.get("median_relative_return_12m")
    hit_rate = summary.get("hit_rate_vs_benchmark_12m")
    if records < 3 or relative is None or hit_rate is None:
        return "insufficient_evidence"
    if relative > 0.05 and hit_rate >= 0.5:
        return "positive_contributor"
    if relative < 0 or hit_rate < 0.4:
        return "negative_contributor"
    return "neutral_mixed"


def _group_rows(
    rows: list[dict],
    field: str,
    *,
    label_field: str,
    metadata: dict[str, dict] | None = None,
) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        ticker_metadata = (metadata or {}).get(str(row.get("ticker")), {})
        value = ticker_metadata.get(field) or row.get(field) or "Unknown"
        grouped.setdefault(str(value), []).append(row)
    output = []
    for label, group in sorted(grouped.items()):
        summary = _summarize_rows(group)
        tickers = sorted({str(row.get("ticker")) for row in group})
        output.append(
            {
                label_field: label,
                "tickers": tickers,
                "ticker_count": len(tickers),
                **summary,
                "instability_label": _contribution_label(summary),
            }
        )
    return output


def summarize_by_ticker(
    rows: list[dict],
    ticker_metadata: dict[str, dict],
) -> list[dict]:
    """Build one conservative attribution row per ticker."""
    grouped = _group_rows(rows, "ticker", label_field="ticker")
    for item in grouped:
        metadata = ticker_metadata.get(item["ticker"], {})
        item.update(
            {
                "sector": metadata.get("sector", "Unknown"),
                "category": metadata.get("category", "Unknown"),
                "universe_group": metadata.get("universe_group", "Unknown"),
                "contribution_to_instability": item.pop(
                    "instability_label"
                ),
                "main_limitation": metadata.get(
                    "main_limitation", "coverage metadata unavailable"
                ),
            }
        )
    return grouped


def summarize_by_sector(
    rows: list[dict], ticker_metadata: dict[str, dict]
) -> list[dict]:
    """Group expanded results by validated sector metadata."""
    return _group_rows(
        rows,
        "sector",
        label_field="sector",
        metadata=ticker_metadata,
    )


def summarize_by_category(
    rows: list[dict], ticker_metadata: dict[str, dict]
) -> list[dict]:
    """Group expanded results by validated research category."""
    return _group_rows(
        rows,
        "category",
        label_field="category",
        metadata=ticker_metadata,
    )


def summarize_by_universe_group(
    rows: list[dict], ticker_metadata: dict[str, dict]
) -> list[dict]:
    """Compare named universe groups, the added cohort, and full trial."""
    output = _group_rows(
        rows,
        "universe_group",
        label_field="universe_group",
        metadata=ticker_metadata,
    )
    expanded = [
        row
        for row in rows
        if ticker_metadata.get(str(row.get("ticker")), {}).get(
            "universe_group"
        )
        != "current_core"
    ]
    for label, group in (
        ("expanded_cohort", expanded),
        ("full_expanded_trial", rows),
    ):
        summary = _summarize_rows(group)
        output.append(
            {
                "universe_group": label,
                "tickers": sorted({str(row.get("ticker")) for row in group}),
                "ticker_count": len(
                    {str(row.get("ticker")) for row in group}
                ),
                **summary,
                "instability_label": _contribution_label(summary),
            }
        )
    return output


def summarize_by_date(rows: list[dict]) -> list[dict]:
    """Group results by historical as-of date."""
    grouped = _group_rows(rows, "as_of_date", label_field="as_of_date")
    for item in grouped:
        relative = item.get("median_relative_return_12m")
        hit_rate = item.get("hit_rate_vs_benchmark_12m")
        if relative is None or hit_rate is None:
            period_label = "unstable_period"
        elif relative > 0.05 and hit_rate >= 0.5:
            period_label = "supportive_period"
        elif relative < 0 and hit_rate < 0.5:
            period_label = "negative_period"
        elif abs(relative) <= 0.05:
            period_label = "neutral_period"
        else:
            period_label = "unstable_period"
        item["period_label"] = period_label
        item.pop("instability_label")
    return grouped


def summarize_clean_vs_warning(rows: list[dict]) -> list[dict]:
    """Compare clean, warning, delayed, and non-delayed evidence."""
    subsets = {
        "clean_records": [
            row
            for row in rows
            if row.get("coverage_guardrail_status") == "clean"
            or row.get("coverage_quality_label") == "clean"
        ],
        "warning_records": [
            row
            for row in rows
            if row.get("coverage_guardrail_status") != "clean"
            and row.get("coverage_quality_label") != "clean"
        ],
        "delayed_price_anchor": [
            row for row in rows if _bool(row, "has_delayed_price_anchor")
        ],
        "no_delayed_anchor": [
            row for row in rows if not _bool(row, "has_delayed_price_anchor")
        ],
    }
    output = []
    for label, subset in subsets.items():
        summary = _summarize_rows(subset)
        output.append(
            {
                "subset": label,
                **summary,
                "conclusion": _contribution_label(summary),
            }
        )
    return output


def _top_share(values: list[str]) -> float:
    if not values:
        return 0.0
    counts = {value: values.count(value) for value in set(values)}
    return round(max(counts.values()) / len(values), 6)


def summarize_metadata_diversity(
    rows: list[dict],
    ticker_metadata: dict[str, dict],
) -> dict:
    """Recheck structural and readiness metadata diversity."""
    tickers = [str(row.get("ticker") or "Unknown") for row in rows]
    sectors = [
        ticker_metadata.get(ticker, {}).get("sector", "Unknown")
        for ticker in tickers
    ]
    categories = [
        ticker_metadata.get(ticker, {}).get("category", "Unknown")
        for ticker in tickers
    ]
    groups = [
        ticker_metadata.get(ticker, {}).get("universe_group", "Unknown")
        for ticker in tickers
    ]
    readiness_fields = (
        "readiness_label",
        "source_verification_status",
        "promotion_blocking_bucket",
        "buffett_interest_level",
        "munger_interest_level",
        "fisher_interest_level",
        "lynch_interest_level",
        "bogle_interest_level",
    )
    field_diversity = {
        field: {
            "unique_values": sorted(
                {
                    str(row.get(field))
                    for row in rows
                    if row.get(field) not in {None, "", "Missing"}
                }
            ),
            "unique_count": len(
                {
                    str(row.get(field))
                    for row in rows
                    if row.get(field) not in {None, "", "Missing"}
                }
            ),
            "top_value_share": _top_share(
                [
                    str(row.get(field))
                    for row in rows
                    if row.get(field) not in {None, "", "Missing"}
                ]
            ),
        }
        for field in readiness_fields
    }
    low_diversity_fields = [
        field
        for field, summary in field_diversity.items()
        if summary["unique_count"] <= 1 or summary["top_value_share"] >= 0.9
    ]
    structural_diverse = (
        len(set(tickers)) >= 10
        and len(set(sectors)) >= 3
        and len(set(categories)) >= 3
        and len(set(groups)) >= 4
        and _top_share(tickers) <= 0.2
    )
    if structural_diverse and not low_diversity_fields:
        status = "diversified_enough_for_research"
    elif structural_diverse:
        status = "partially_concentrated"
    else:
        status = "concentrated_needs_expansion"
    return {
        "unique_ticker_count": len(set(tickers)),
        "unique_sector_count": len(set(sectors)),
        "unique_category_count": len(set(categories)),
        "unique_universe_group_count": len(set(groups)),
        "top_ticker_concentration_ratio": _top_share(tickers),
        "top_sector_concentration_ratio": _top_share(sectors),
        "top_category_concentration_ratio": _top_share(categories),
        "top_universe_group_concentration_ratio": _top_share(groups),
        "field_diversity": field_diversity,
        "low_diversity_fields": low_diversity_fields,
        "metadata_diversity_status": status,
        "interpretation": (
            "Ticker and research-cohort coverage expanded materially, but "
            "several readiness and investor-interest fields remain dominated "
            "by one value."
            if low_diversity_fields
            else "Structural and readiness metadata provide usable research diversity."
        ),
    }


def _ticker_metadata(
    coverage_report: dict,
    eligible_universe: dict,
) -> dict[str, dict]:
    summaries = coverage_report.get("ticker_summaries") or []
    if summaries:
        return {
            str(item.get("ticker")): dict(item)
            for item in summaries
            if item.get("ticker")
        }
    values = eligible_universe.get("eligible_tickers") or []
    return {
        str(item.get("ticker")): dict(item)
        for item in values
        if isinstance(item, dict) and item.get("ticker")
    }


def compare_to_prior_trial(
    *,
    expanded_summary: dict,
    expanded_manifest: dict,
    expanded_metrics: dict,
    prior_manifest: dict,
    prior_metrics: dict,
    prior_clean_report: dict,
) -> dict:
    """Compare headline research diagnostics without changing decisions."""
    prior_clean = (
        prior_clean_report.get("subset_diagnostics", {}).get(
            "clean_records", {}
        )
    )
    return {
        "prior_backtest_run_id": prior_manifest.get("backtest_run_id"),
        "expanded_backtest_run_id": expanded_manifest.get("backtest_run_id"),
        "prior": {
            "sample_size": prior_manifest.get("overall_sample_size"),
            "clean_records": prior_manifest.get("clean_record_count"),
            "warning_records": prior_manifest.get("warning_record_count"),
            "warning_heavy_records": prior_manifest.get(
                "warning_heavy_record_count"
            ),
            "median_relative_return_12m": prior_metrics.get(
                "median_relative_return_12m"
            ),
            "hit_rate_vs_benchmark_12m": prior_metrics.get(
                "hit_rate_vs_benchmark_12m"
            ),
            "diagnostic_status": prior_manifest.get("diagnostic_status"),
            "decision_status": prior_manifest.get("decision_status"),
            "walk_forward_stability": prior_manifest.get(
                "walk_forward_stability_judgment"
            ),
            "clean_median_relative_return_12m": prior_clean.get(
                "median_relative_return_12m"
            ),
        },
        "expanded": {
            "sample_size": expanded_summary.get("sample_size_after_dedupe"),
            "clean_records": expanded_manifest.get("clean_record_count"),
            "warning_records": expanded_manifest.get("warning_record_count"),
            "warning_heavy_records": expanded_manifest.get(
                "warning_heavy_record_count"
            ),
            "median_relative_return_12m": expanded_metrics.get(
                "median_relative_return_12m"
            ),
            "hit_rate_vs_benchmark_12m": expanded_metrics.get(
                "hit_rate_vs_benchmark_12m"
            ),
            "diagnostic_status": expanded_manifest.get("diagnostic_status"),
            "decision_status": expanded_manifest.get("decision_status"),
            "walk_forward_stability": expanded_manifest.get(
                "walk_forward_stability_judgment"
            ),
        },
        "explanation": (
            "The broader universe increased clean and total observations, but "
            "median benchmark-relative performance and hit rate weakened. The "
            "decision remained conservative while diagnostic stability declined."
        ),
    }


def _find_group(items: list[dict], field: str, value: str) -> dict:
    return next((item for item in items if item.get(field) == value), {})


def _instability_explanation(
    *,
    metrics: dict,
    ticker_attribution: list[dict],
    universe_groups: list[dict],
    dates: list[dict],
    clean_warning: list[dict],
    metadata_diversity: dict,
    backtest_manifest: dict,
    prior_comparison: dict,
) -> dict:
    drivers = []
    secondary = []
    evidence = []
    counter_evidence = []
    if (metrics.get("median_relative_return_12m") or 0) < 0:
        drivers.append("benchmark_underperformance")
        evidence.append(
            "Expanded median relative 12M return is below zero."
        )
    core = _find_group(universe_groups, "universe_group", "current_core")
    added = _find_group(universe_groups, "universe_group", "expanded_cohort")
    if (
        core.get("median_relative_return_12m") is not None
        and added.get("median_relative_return_12m") is not None
        and added["median_relative_return_12m"]
        < core["median_relative_return_12m"]
    ):
        drivers.append("expanded_cohort_underperformance")
        evidence.append(
            "The added eight-ticker cohort is weaker than the current-core cohort."
        )
    labels = {item.get("period_label") for item in dates}
    if "supportive_period" in labels and "negative_period" in labels:
        drivers.append("period_sensitivity")
        evidence.append("Supportive and negative historical periods coexist.")
    clean = _find_group(clean_warning, "subset", "clean_records")
    warning = _find_group(clean_warning, "subset", "warning_records")
    prior_clean_relative = (
        prior_comparison.get("prior", {}).get(
            "clean_median_relative_return_12m"
        )
    )
    if (
        clean.get("median_relative_return_12m") is not None
        and prior_clean_relative is not None
        and clean["median_relative_return_12m"] < prior_clean_relative
    ):
        secondary.append("clean_records_weaker_than_prior")
    if (
        warning.get("median_relative_return_12m") is not None
        and clean.get("median_relative_return_12m") is not None
        and warning["median_relative_return_12m"]
        < clean["median_relative_return_12m"]
    ):
        secondary.append("warning_records_weaker_than_clean")
    if backtest_manifest.get("outlier_dependence_status") not in {
        None,
        "no_outlier_issue_detected",
        "outliers_present_but_result_survives",
    }:
        secondary.append("ticker_outlier_dependence")
    if backtest_manifest.get("delayed_anchor_present"):
        secondary.append("delayed_anchor_effect")
    if metadata_diversity["metadata_diversity_status"] != (
        "diversified_enough_for_research"
    ):
        secondary.append("metadata_diversity_issue")
    negative_tickers = [
        item["ticker"]
        for item in ticker_attribution
        if item["contribution_to_instability"] == "negative_contributor"
    ]
    if negative_tickers:
        evidence.append(
            "Negative contributor tickers: " + ", ".join(negative_tickers) + "."
        )
    if (metrics.get("median_forward_return_12m") or 0) > 0:
        counter_evidence.append(
            "Median absolute 12M return remains positive."
        )
    if int(backtest_manifest.get("clean_record_count") or 0) > 0:
        counter_evidence.append(
            "The expanded sample includes clean records, so weakness is not "
            "explained solely by missing clean coverage."
        )
    issue = (
        "The weakening is primarily a broader-cohort and benchmark-relative "
        "research result, with timing and metadata cautions as secondary "
        "limitations rather than a pure data-quality failure."
    )
    return {
        "primary_instability_drivers": list(dict.fromkeys(drivers)),
        "secondary_instability_drivers": list(dict.fromkeys(secondary)),
        "evidence_supporting_instability": evidence,
        "evidence_against_instability": counter_evidence,
        "what_changed_from_prior_trial": (
            "The universe expanded from four to twelve tickers and the sample "
            "from 20 to 60. Median relative return and benchmark hit rate fell, "
            "while diagnostic status moved to unstable_needs_deeper_review."
        ),
        "whether_issue_is_data_quality_or_research_signal": issue,
        "recommended_next_research_action": NEXT_RESEARCH_ACTION,
    }


def analyze_expanded_trial_results(
    *,
    outputs_root: Path,
    expanded_trial_run_id: str | None = None,
    backtest_run_id: str | None = None,
    prior_backtest_run_id: str = "20260614_205804",
    analysis_run_id: str | None = None,
    generated_at: datetime | None = None,
) -> ExpandedTrialAnalysisReport:
    """Analyze one completed expanded readiness trial from existing outputs."""
    outputs_root = Path(outputs_root)
    expanded = load_expanded_trial_manifest(
        outputs_root=outputs_root,
        expanded_trial_run_id=expanded_trial_run_id,
    )
    expanded_id = str(expanded.get("expanded_trial_run_id") or "")
    selected_backtest = str(
        backtest_run_id or expanded.get("backtest_run_id") or ""
    )
    if not expanded_id or not selected_backtest:
        raise ValueError("Expanded trial and backtest run IDs are required.")
    timestamp = generated_at or datetime.now(timezone.utc)
    run_id = analysis_run_id or timestamp.strftime("%Y%m%d_%H%M%S")

    backtest_folder = outputs_root / "backtests" / selected_backtest
    backtest_manifest_path = backtest_folder / "backtest_manifest.json"
    backtest_manifest = _load_json(backtest_manifest_path)
    if not backtest_manifest:
        raise FileNotFoundError(
            f"Backtest manifest not found: {backtest_manifest_path}"
        )
    results_path = backtest_folder / "backtest_results.csv"
    rows = load_backtest_results(results_path)
    if not rows:
        raise ValueError(f"Backtest results are empty: {results_path}")
    metrics = _load_json(backtest_folder / "backtest_metrics_summary.json")
    source_report_names = {
        "diagnostic": "readiness_trial_diagnostic_report.json",
        "decision": "readiness_trial_decision_report.json",
        "clean_coverage": "clean_coverage_sensitivity_report.json",
        "delayed_anchor": "delayed_anchor_impact_report.json",
        "outlier": "outlier_sensitivity_report.json",
        "walk_forward": "walk_forward_metrics.json",
    }
    source_reports = {
        name: {
            "path": str(backtest_folder / filename),
            "available": bool(_load_json(backtest_folder / filename)),
        }
        for name, filename in source_report_names.items()
    }

    source_validation_id = str(expanded.get("source_validation_run_id") or "")
    coverage_folder = (
        outputs_root / "expanded_ticker_coverage" / source_validation_id
    )
    coverage_report = _load_json(
        coverage_folder / "expanded_ticker_coverage_report.json"
    )
    eligible_path_value = expanded.get("eligible_universe_path")
    eligible_path = (
        Path(eligible_path_value)
        if eligible_path_value
        else coverage_folder / "expanded_ticker_eligible_universe.yaml"
    )
    eligible_universe = _load_yaml(eligible_path)
    ticker_metadata = _ticker_metadata(coverage_report, eligible_universe)

    ticker_attribution = summarize_by_ticker(rows, ticker_metadata)
    sector_attribution = summarize_by_sector(rows, ticker_metadata)
    category_attribution = summarize_by_category(rows, ticker_metadata)
    universe_attribution = summarize_by_universe_group(rows, ticker_metadata)
    date_attribution = summarize_by_date(rows)
    clean_warning = summarize_clean_vs_warning(rows)
    metadata_diversity = summarize_metadata_diversity(rows, ticker_metadata)

    prior_folder = outputs_root / "backtests" / prior_backtest_run_id
    prior_manifest = _load_json(prior_folder / "backtest_manifest.json")
    prior_metrics = _load_json(
        prior_folder / "backtest_metrics_summary.json"
    )
    prior_clean_report = _load_json(
        prior_folder / "clean_coverage_sensitivity_report.json"
    )
    prior_comparison = compare_to_prior_trial(
        expanded_summary=expanded,
        expanded_manifest=backtest_manifest,
        expanded_metrics=metrics,
        prior_manifest=prior_manifest,
        prior_metrics=prior_metrics,
        prior_clean_report=prior_clean_report,
    )
    explanation = _instability_explanation(
        metrics=metrics,
        ticker_attribution=ticker_attribution,
        universe_groups=universe_attribution,
        dates=date_attribution,
        clean_warning=clean_warning,
        metadata_diversity=metadata_diversity,
        backtest_manifest=backtest_manifest,
        prior_comparison=prior_comparison,
    )
    missing_metadata = not ticker_metadata
    status = (
        "instability_partially_explained"
        if missing_metadata
        or len(explanation["primary_instability_drivers"]) < 2
        else "instability_explained_preliminary"
    )
    return ExpandedTrialAnalysisReport(
        analysis_run_id=run_id,
        generated_at=timestamp.isoformat(),
        expanded_trial_run_id=expanded_id,
        backtest_run_id=selected_backtest,
        prior_backtest_run_id=prior_backtest_run_id,
        analysis_status=status,
        source_reports=source_reports,
        ticker_attribution=ticker_attribution,
        sector_attribution=sector_attribution,
        category_attribution=category_attribution,
        universe_group_attribution=universe_attribution,
        date_attribution=date_attribution,
        clean_warning_attribution=clean_warning,
        metadata_diversity_recheck=metadata_diversity,
        prior_trial_comparison=prior_comparison,
        expanded_trial_instability_explanation=explanation,
    )


def _format(value) -> str:
    if value is None:
        return "Not available"
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _table(
    items: list[dict],
    columns: list[tuple[str, str]],
) -> list[str]:
    headers = [label for _, label in columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for item in items:
        lines.append(
            "| "
            + " | ".join(_format(item.get(field)) for field, _ in columns)
            + " |"
        )
    return lines


def render_expanded_trial_analysis_report(
    report: ExpandedTrialAnalysisReport,
) -> str:
    """Render the complete markdown analysis."""
    data = report.to_dict()
    explanation = data["expanded_trial_instability_explanation"]
    diversity = data["metadata_diversity_recheck"]
    comparison = data["prior_trial_comparison"]
    prior = comparison["prior"]
    expanded = comparison["expanded"]
    primary = explanation["primary_instability_drivers"]
    lines = [
        "# Expanded Trial Results Analysis Report",
        "",
        "## Executive Summary",
        "",
        f"- Analysis Status: {data['analysis_status']}",
        f"- Expanded Trial Run ID: {data['expanded_trial_run_id']}",
        f"- Backtest Run ID: {data['backtest_run_id']}",
        (
            "- Main Finding: The expanded run weakened the preliminary "
            "benchmark-relative evidence and exposed broader-cohort instability."
        ),
        f"- Primary Instability Drivers: {_format(primary)}",
        f"- Next Research Action: {data['next_research_action']}",
        "",
        "## What Changed from the Prior Trial",
        "",
        "| Metric | Prior 4-Ticker | Expanded 12-Ticker |",
        "|---|---:|---:|",
    ]
    for label, key in (
        ("Sample Size", "sample_size"),
        ("Clean Records", "clean_records"),
        ("Warning Records", "warning_records"),
        ("Warning-Heavy Records", "warning_heavy_records"),
        ("Median Relative 12M", "median_relative_return_12m"),
        ("Hit Rate vs Benchmark 12M", "hit_rate_vs_benchmark_12m"),
        ("Diagnostic Status", "diagnostic_status"),
        ("Decision Status", "decision_status"),
        ("Walk-Forward Stability", "walk_forward_stability"),
    ):
        lines.append(
            f"| {label} | {_format(prior.get(key))} | "
            f"{_format(expanded.get(key))} |"
        )
    lines.extend(["", "## Ticker Attribution", ""])
    lines.extend(
        _table(
            data["ticker_attribution"],
            [
                ("ticker", "Ticker"),
                ("records", "Records"),
                ("clean_records", "Clean"),
                ("warning_records", "Warning"),
                ("median_relative_return_12m", "Median Relative 12M"),
                ("hit_rate_vs_benchmark_12m", "Hit Rate 12M"),
                ("contribution_to_instability", "Instability Contribution"),
            ],
        )
    )
    lines.extend(["", "## Universe Group Attribution", ""])
    lines.extend(
        _table(
            data["universe_group_attribution"],
            [
                ("universe_group", "Universe Group"),
                ("ticker_count", "Tickers"),
                ("records", "Records"),
                ("median_relative_return_12m", "Median Relative 12M"),
                ("hit_rate_vs_benchmark_12m", "Hit Rate 12M"),
                ("instability_label", "Interpretation"),
            ],
        )
    )
    for title, key, label in (
        ("Sector Attribution", "sector_attribution", "sector"),
        ("Category Attribution", "category_attribution", "category"),
    ):
        lines.extend(["", f"## {title}", ""])
        lines.extend(
            _table(
                data[key],
                [
                    (label, title.split()[0]),
                    ("ticker_count", "Tickers"),
                    ("records", "Records"),
                    ("median_relative_return_12m", "Median Relative 12M"),
                    ("hit_rate_vs_benchmark_12m", "Hit Rate 12M"),
                    ("instability_label", "Interpretation"),
                ],
            )
        )
    lines.extend(["", "## Date / Period Attribution", ""])
    lines.extend(
        _table(
            data["date_attribution"],
            [
                ("as_of_date", "Date"),
                ("records", "Records"),
                ("clean_records", "Clean"),
                ("warning_records", "Warning"),
                ("median_relative_return_12m", "Median Relative 12M"),
                ("hit_rate_vs_benchmark_12m", "Hit Rate 12M"),
                ("period_label", "Period Label"),
            ],
        )
    )
    lines.extend(["", "## Clean vs Warning Attribution", ""])
    lines.extend(
        _table(
            data["clean_warning_attribution"],
            [
                ("subset", "Subset"),
                ("records", "Records"),
                ("median_relative_return_12m", "Median Relative 12M"),
                ("hit_rate_vs_benchmark_12m", "Hit Rate 12M"),
                ("conclusion", "Conclusion"),
            ],
        )
    )
    lines.extend(
        [
            "",
            "## Metadata Diversity Recheck",
            "",
            f"- Unique Tickers: {diversity['unique_ticker_count']}",
            f"- Unique Sectors: {diversity['unique_sector_count']}",
            f"- Unique Categories: {diversity['unique_category_count']}",
            (
                "- Unique Universe Groups: "
                f"{diversity['unique_universe_group_count']}"
            ),
            (
                "- Top Ticker Concentration Ratio: "
                f"{diversity['top_ticker_concentration_ratio']}"
            ),
            (
                "- Top Sector Concentration Ratio: "
                f"{diversity['top_sector_concentration_ratio']}"
            ),
            (
                "- Top Category Concentration Ratio: "
                f"{diversity['top_category_concentration_ratio']}"
            ),
            (
                "- Top Universe Group Concentration Ratio: "
                f"{diversity['top_universe_group_concentration_ratio']}"
            ),
            (
                "- Metadata Diversity Status: "
                f"{diversity['metadata_diversity_status']}"
            ),
            f"- Low-Diversity Fields: {_format(diversity['low_diversity_fields'])}",
            f"- Interpretation: {diversity['interpretation']}",
            "",
            "## Instability Explanation",
            "",
            (
                "- Primary Drivers: "
                f"{_format(explanation['primary_instability_drivers'])}"
            ),
            (
                "- Secondary Drivers: "
                f"{_format(explanation['secondary_instability_drivers'])}"
            ),
            (
                "- Evidence: "
                f"{_format(explanation['evidence_supporting_instability'])}"
            ),
            (
                "- What Remains Uncertain: Structural metadata improved, but "
                "several readiness fields remain low-diversity and attribution "
                "is not causal."
            ),
            "",
            "## Research Interpretation",
            "",
            "- The expanded run weakened the preliminary evidence.",
            "- The system should not proceed to validation.",
            (
                "- The appropriate next step is evidence scorecard and "
                "gatekeeping, not promotion."
            ),
            "",
            "## What This Suggests",
            "",
            "- The pipeline can detect instability when the sample broadens.",
            "- Prior evidence was not robust enough to generalize.",
            "",
            "## What This Does Not Suggest",
            "",
            "- It does not prove the opposite strategy.",
            "- It does not rank tickers.",
            "- It does not recommend avoiding or buying any ticker.",
            "- It does not validate investor agents.",
            "- It does not create a trade signal.",
            "- It does not justify allocation or rebalancing.",
            "",
            "## Next Research Action",
            "",
            f"- Action Code: {data['next_research_action']}",
            "",
            "## Safety Notice",
            "",
            data["safety_notice"],
            "",
        ]
    )
    return "\n".join(lines)


def _write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(rows[0].keys()) if rows else ["status"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: (
                        ";".join(str(item) for item in value)
                        if isinstance(value, list)
                        else value
                    )
                    for key, value in row.items()
                }
            )


def write_expanded_trial_analysis_report(
    *,
    outputs_root: Path,
    expanded_trial_run_id: str | None = None,
    backtest_run_id: str | None = None,
    prior_backtest_run_id: str = "20260614_205804",
    generated_at: datetime | None = None,
) -> ExpandedTrialAnalysisFiles:
    """Analyze existing outputs and write JSON, Markdown, and attribution CSVs."""
    timestamp = generated_at or datetime.now(timezone.utc)
    root = Path(outputs_root) / "expanded_trial_analyses"
    root.mkdir(parents=True, exist_ok=True)
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    analysis_run_id = base
    suffix = 2
    while (root / analysis_run_id).exists():
        analysis_run_id = f"{base}_{suffix:02d}"
        suffix += 1
    report = analyze_expanded_trial_results(
        outputs_root=outputs_root,
        expanded_trial_run_id=expanded_trial_run_id,
        backtest_run_id=backtest_run_id,
        prior_backtest_run_id=prior_backtest_run_id,
        analysis_run_id=analysis_run_id,
        generated_at=timestamp,
    )
    folder = root / analysis_run_id
    folder.mkdir(parents=True, exist_ok=False)
    json_path = folder / "expanded_trial_analysis_report.json"
    markdown_path = folder / "expanded_trial_analysis_report.md"
    csv_paths = {
        "ticker": folder / "expanded_trial_ticker_attribution.csv",
        "sector": folder / "expanded_trial_sector_attribution.csv",
        "category": folder / "expanded_trial_category_attribution.csv",
        "universe_group": (
            folder / "expanded_trial_universe_group_attribution.csv"
        ),
        "date": folder / "expanded_trial_date_attribution.csv",
        "clean_warning": (
            folder / "expanded_trial_clean_warning_attribution.csv"
        ),
    }
    payload = report.to_dict()
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text(
        render_expanded_trial_analysis_report(report),
        encoding="utf-8",
    )
    _write_csv(csv_paths["ticker"], report.ticker_attribution)
    _write_csv(csv_paths["sector"], report.sector_attribution)
    _write_csv(csv_paths["category"], report.category_attribution)
    _write_csv(
        csv_paths["universe_group"], report.universe_group_attribution
    )
    _write_csv(csv_paths["date"], report.date_attribution)
    _write_csv(csv_paths["clean_warning"], report.clean_warning_attribution)
    latest_path = root / "latest_expanded_trial_analysis_manifest.json"
    latest = {
        "analysis_run_id": report.analysis_run_id,
        "expanded_trial_run_id": report.expanded_trial_run_id,
        "backtest_run_id": report.backtest_run_id,
        "prior_backtest_run_id": report.prior_backtest_run_id,
        "analysis_status": report.analysis_status,
        "metadata_diversity_status": report.metadata_diversity_recheck[
            "metadata_diversity_status"
        ],
        "next_research_action": report.next_research_action,
        "analysis_folder": str(folder),
        "report_path": str(markdown_path),
        "report_json_path": str(json_path),
        "safety_notice": report.safety_notice,
    }
    latest_path.write_text(json.dumps(latest, indent=2), encoding="utf-8")
    return ExpandedTrialAnalysisFiles(
        analysis_folder=folder,
        markdown_path=markdown_path,
        json_path=json_path,
        ticker_csv_path=csv_paths["ticker"],
        sector_csv_path=csv_paths["sector"],
        category_csv_path=csv_paths["category"],
        universe_group_csv_path=csv_paths["universe_group"],
        date_csv_path=csv_paths["date"],
        clean_warning_csv_path=csv_paths["clean_warning"],
        latest_manifest_path=latest_path,
        report=report,
    )
