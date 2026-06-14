"""Research-only diagnostics for readiness trial backtest results."""

import csv
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from statistics import mean, median

MISSING_METADATA_FIELDS = (
    "readiness_label",
    "source_verification_status",
    "buffett_interest_level",
    "munger_interest_level",
    "fisher_interest_level",
    "lynch_interest_level",
    "bogle_interest_level",
)
INTEREST_FIELDS = tuple(
    field for field in MISSING_METADATA_FIELDS if field.endswith("_interest_level")
)
ATTRIBUTION_FIELDS = (
    "readiness_label",
    "source_verification_status",
    "promotion_blocking_bucket",
    *INTEREST_FIELDS,
)
OUTLIER_GAP_THRESHOLD = 0.15
HORIZON_STRENGTH_THRESHOLD = 0.10
SAFETY_NOTICE = (
    "This readiness trial diagnostic report is not a recommendation, ranking, "
    "vote, average score, consensus, allocation instruction, rebalancing "
    "instruction, trade signal, execution instruction, or investment advice."
)


@dataclass(frozen=True)
class ReadinessTrialDiagnosticReport:
    """Structured attribution diagnostics for readiness-only results."""

    backtest_run_id: str
    backtest_run_type: str
    sample_size: int
    evaluated_tickers: list[str]
    periods_evaluated: int
    aggregate_metrics: dict
    period_diagnostics: list[dict]
    ticker_diagnostics: list[dict]
    horizon_diagnostics: dict
    outlier_diagnostics: dict
    concentration_diagnostics: dict
    stability_diagnostics: dict
    coverage_quality_diagnostics: dict
    clean_coverage_sensitivity: dict
    metadata_attribution_diagnostics: dict
    missing_metadata_fields: list[str]
    key_findings: list[str]
    diagnostic_status: str
    next_research_action: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready representation."""
        return asdict(self)


@dataclass(frozen=True)
class ReadinessTrialDiagnosticReportFiles:
    """Generated diagnostic report paths and structured content."""

    markdown_path: Path
    json_path: Path
    report: ReadinessTrialDiagnosticReport


def _numeric(row: dict, field: str) -> float | None:
    """Read one optional numeric result field."""
    value = row.get(field)
    if value in {"", None}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _values(rows: list[dict], field: str) -> list[float]:
    """Return all valid numeric values for one field."""
    values = [_numeric(row, field) for row in rows]
    return [value for value in values if value is not None]


def _median(rows: list[dict], field: str) -> float | None:
    values = _values(rows, field)
    return round(median(values), 6) if values else None


def _average(rows: list[dict], field: str) -> float | None:
    values = _values(rows, field)
    return round(mean(values), 6) if values else None


def _rate(rows: list[dict], field: str) -> float | None:
    values = _values(rows, field)
    if not values:
        return None
    return round(sum(value > 0 for value in values) / len(values), 6)


def _missing_metadata(rows: list[dict]) -> list[str]:
    """Identify grouping fields absent from every result row."""
    return [
        field
        for field in MISSING_METADATA_FIELDS
        if not any(
            str(row.get(field) or "").strip().lower()
            not in {"", "missing", "null", "none"}
            for row in rows
        )
    ]


def _metadata_values(rows: list[dict], field: str) -> list[str]:
    """Return distinct non-missing metadata values."""
    return sorted(
        {
            str(row.get(field)).strip()
            for row in rows
            if str(row.get(field) or "").strip().lower()
            not in {"", "missing", "null", "none"}
        }
    )


def _metadata_status_counts(rows: list[dict]) -> dict[str, int]:
    """Count enrichment statuses in evaluated rows."""
    counts: dict[str, int] = {}
    for row in rows:
        status = str(
            row.get("metadata_enrichment_status") or "not_available"
        )
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _grouped_metadata_availability(rows: list[dict]) -> dict[str, bool]:
    """Report whether grouped metadata has non-missing evidence."""
    return {
        field: bool(_metadata_values(rows, field))
        for field in MISSING_METADATA_FIELDS
    }


def assess_group_diversity(groups: list[dict]) -> dict:
    """Assess whether grouped metadata permits a useful comparison."""
    populated = [
        group
        for group in groups
        if str(group.get("group_name") or "").strip().lower()
        not in {"", "missing", "null", "none"}
    ]
    total_records = sum(int(group.get("sample_size") or 0) for group in populated)
    group_count = len(populated)
    sample_sizes = [int(group.get("sample_size") or 0) for group in populated]
    max_group_share = (
        round(max(sample_sizes) / total_records, 6)
        if sample_sizes and total_records
        else None
    )
    groups_at_least_five = sum(size >= 5 for size in sample_sizes)
    has_useful_diversity = (
        group_count >= 2
        and groups_at_least_five >= 2
        and max_group_share is not None
        and max_group_share < 0.90
    )
    small_sample_limited = (
        group_count >= 2 and any(size < 5 for size in sample_sizes)
    )
    if group_count == 0:
        status = "metadata_missing"
        interpretation = "No populated groups are available for attribution."
    elif group_count == 1 or (
        max_group_share is not None and max_group_share >= 0.90
    ):
        status = "low_diversity"
        interpretation = (
            "Metadata is present, but one group dominates the evaluated rows, "
            "so it cannot explain performance differences."
        )
    elif small_sample_limited:
        status = "small_sample_limited"
        interpretation = (
            "Multiple groups are present, but at least one comparison group "
            "has fewer than 5 records."
        )
    elif has_useful_diversity:
        status = "comparison_available"
        interpretation = (
            "At least two groups have 5 or more records, allowing a "
            "preliminary non-causal comparison."
        )
    else:
        status = "limited_diversity"
        interpretation = (
            "Group coverage exists but remains too limited for useful "
            "attribution."
        )
    return {
        "group_count": group_count,
        "total_records": total_records,
        "max_group_share": max_group_share,
        "smallest_group_sample_size": min(sample_sizes) if sample_sizes else 0,
        "groups_with_sample_size_at_least_5": groups_at_least_five,
        "has_useful_diversity": has_useful_diversity,
        "small_sample_limited": small_sample_limited,
        "attribution_status": status,
        "diversity_interpretation": interpretation,
    }


def compare_grouped_metric(field: str, groups: list[dict]) -> dict:
    """Build a conservative comparison for one grouped metadata field."""
    diversity = assess_group_diversity(groups)
    comparison_groups = [
        {
            "group_name": group.get("group_name"),
            "sample_size": int(group.get("sample_size") or 0),
            "median_forward_return_12m": group.get(
                "median_forward_return_12m"
            ),
            "median_relative_return_12m": group.get(
                "median_relative_return_12m"
            ),
            "hit_rate_vs_benchmark_12m": group.get(
                "hit_rate_vs_benchmark_12m"
            ),
            "small_sample_warning": bool(group.get("small_sample_warning")),
        }
        for group in groups
        if str(group.get("group_name") or "").strip().lower()
        not in {"", "missing", "null", "none"}
    ]
    complete_groups = [
        group
        for group in comparison_groups
        if group["median_forward_return_12m"] is not None
        and group["median_relative_return_12m"] is not None
    ]
    if len(complete_groups) < 2:
        interpretation = diversity["diversity_interpretation"]
    else:
        higher_absolute = max(
            complete_groups,
            key=lambda group: group["median_forward_return_12m"],
        )
        higher_relative = max(
            complete_groups,
            key=lambda group: group["median_relative_return_12m"],
        )
        sample_warning = any(
            group["small_sample_warning"] for group in complete_groups
        )
        interpretation = (
            f"{higher_absolute['group_name']} has the higher median absolute "
            f"12M outcome, while {higher_relative['group_name']} has the "
            "higher median relative 12M outcome in this small sample."
        )
        if sample_warning:
            interpretation += (
                " At least one group is small-sample limited, so this "
                "association is preliminary and not decision-grade."
            )
        else:
            interpretation += (
                " This is an association only and does not establish causal "
                "or decision-grade evidence."
            )
    return {
        "field": field,
        "groups": comparison_groups,
        "group_diversity": diversity,
        "interpretation": interpretation,
    }


def build_metadata_attribution_diagnostics(
    *,
    metrics: dict,
    missing_metadata_fields: list[str],
    concentration_details: list[str],
) -> dict:
    """Build metadata-aware, non-causal attribution diagnostics."""
    grouped_metrics = metrics.get("grouped_metrics", {})
    status_counts = dict(metrics.get("metadata_enrichment_status_counts") or {})
    availability = {
        field: bool(
            [
                group
                for group in grouped_metrics.get(field, [])
                if str(group.get("group_name") or "").strip().lower()
                not in {"", "missing", "null", "none"}
            ]
        )
        for field in ATTRIBUTION_FIELDS
    }
    comparisons = {
        field: compare_grouped_metric(
            field,
            list(grouped_metrics.get(field, [])),
        )
        for field in ATTRIBUTION_FIELDS
    }
    diversity = {
        field: comparison["group_diversity"]
        for field, comparison in comparisons.items()
    }
    enrichment_detected = any(
        status not in {"missing", "not_available"}
        and int(count or 0) > 0
        for status, count in status_counts.items()
    ) or any(availability.values())
    interest_attribution = {
        field: comparisons[field] for field in INTEREST_FIELDS
    }
    low_diversity_interest = all(
        item["group_diversity"]["has_useful_diversity"] is False
        for item in interest_attribution.values()
    )
    blocker_attribution = comparisons["promotion_blocking_bucket"]
    findings = []
    if enrichment_detected:
        findings.append("Metadata enrichment is detected.")
    readiness = comparisons["readiness_label"]
    if readiness["group_diversity"]["group_count"] >= 2:
        findings.append(
            "Readiness label groups show preliminary differences, but at "
            "least one group may be small-sample limited."
        )
    if low_diversity_interest and any(
        availability[field] for field in INTEREST_FIELDS
    ):
        findings.append(
            "Investor interest metadata is present but has low diversity and "
            "cannot yet explain outcome differences."
        )
    if availability["promotion_blocking_bucket"] and not blocker_attribution[
        "group_diversity"
    ]["has_useful_diversity"]:
        findings.append(
            "Promotion blocker metadata is present but has low diversity."
        )
    findings.append("No causal or decision-grade inference is made.")
    limitations = [
        "Groups with fewer than 5 records are small-sample limited.",
        "Low-diversity fields cannot explain performance differences.",
        "High-return outliers may influence group averages.",
        "Dedupe removes repeated runs but reduces the evaluated sample.",
        "Grouped associations do not establish causal relationships.",
        "These attribution diagnostics are not decision-grade.",
    ]
    return {
        "metadata_enrichment_detected": enrichment_detected,
        "metadata_enrichment_status_counts": status_counts,
        "missing_metadata_fields": list(missing_metadata_fields),
        "grouped_metadata_availability": availability,
        "group_diversity": diversity,
        "attribution_findings": findings,
        "attribution_limitations": limitations,
        "readiness_label_attribution": readiness,
        "source_verification_attribution": comparisons[
            "source_verification_status"
        ],
        "investor_interest_attribution": interest_attribution,
        "promotion_blocking_attribution": blocker_attribution,
        "concentration_details": list(concentration_details),
    }


def _period_interpretation(period: dict) -> str:
    """Describe one period without implying an action."""
    absolute = period.get("median_forward_return_12m")
    relative = period.get("median_relative_return_12m")
    short_3m = period.get("median_forward_return_3m")
    short_6m = period.get("median_forward_return_6m")
    if absolute is not None and absolute < 0 and relative is not None and relative > 0:
        return (
            "Relative 12M outcome was positive while the absolute median 12M "
            "outcome was weak or negative."
        )
    if (
        absolute is not None
        and absolute > 0
        and (
            (short_3m is not None and short_3m < 0)
            or (short_6m is not None and short_6m < 0)
        )
    ):
        return (
            "The 12M outcome was positive despite a weaker shorter-horizon "
            "cohort result."
        )
    if relative is not None and relative > 0:
        return (
            "The cohort had a positive median relative 12M outcome, subject "
            "to its small period sample."
        )
    return "The cohort result is mixed or incomplete and remains diagnostic."


def _period_diagnostics(manifest: dict) -> list[dict]:
    """Load and annotate optional walk-forward period metrics."""
    path_value = manifest.get("walk_forward_metrics_path")
    if not path_value or not Path(path_value).is_file():
        return []
    payload = json.loads(Path(path_value).read_text(encoding="utf-8"))
    diagnostics = []
    for period in payload.get("periods", []):
        item = {
            field: period.get(field)
            for field in (
                "period",
                "sample_size",
                "tickers",
                "median_forward_return_3m",
                "median_forward_return_6m",
                "median_forward_return_12m",
                "median_relative_return_12m",
                "hit_rate_vs_benchmark_12m",
                "positive_return_rate_12m",
                "median_max_drawdown_12m",
                "concentration_warning",
            )
        }
        item["period_interpretation"] = _period_interpretation(period)
        diagnostics.append(item)
    return diagnostics


def _clean_coverage_sensitivity(manifest: dict) -> dict:
    """Load the run-local clean-coverage sensitivity report."""
    path_value = manifest.get(
        "clean_coverage_sensitivity_report_json_path"
    )
    if not path_value or not Path(path_value).is_file():
        return {
            "sensitivity_status": "not_available",
            "clean_only_available": False,
            "warning_heavy_comparison_summary": "Not available.",
            "delayed_anchor_comparison_summary": "Not available.",
            "interpretation": (
                "Clean-coverage sensitivity is not available for this run."
            ),
        }
    payload = json.loads(Path(path_value).read_text(encoding="utf-8"))
    subsets = payload.get("subset_diagnostics", {})
    clean = subsets.get("clean_records", {})
    warning_heavy = subsets.get("warning_heavy", {})
    non_warning = subsets.get("non_warning_heavy", {})
    delayed = subsets.get("delayed_anchor", {})
    no_delayed = subsets.get("no_delayed_anchor", {})
    findings = list(payload.get("key_findings") or [])
    return {
        "sensitivity_status": payload.get(
            "sensitivity_status",
            "not_available",
        ),
        "clean_only_available": bool(clean.get("available")),
        "warning_heavy_comparison_summary": (
            f"warning_heavy sample={warning_heavy.get('sample_size', 0)}; "
            f"non_warning_heavy sample={non_warning.get('sample_size', 0)}."
        ),
        "delayed_anchor_comparison_summary": (
            f"delayed_anchor sample={delayed.get('sample_size', 0)}; "
            f"no_delayed_anchor sample={no_delayed.get('sample_size', 0)}."
        ),
        "interpretation": (
            next(iter(findings), "")
            or "Clean-coverage sensitivity produced no finding."
        ),
    }


def _ticker_interpretation(ticker: str, diagnostic: dict) -> str:
    """Describe ticker contribution using only calculated evidence."""
    average_12m = diagnostic["average_forward_return_12m"]
    median_12m = diagnostic["median_forward_return_12m"]
    if (
        average_12m is not None
        and median_12m is not None
        and average_12m - median_12m > OUTLIER_GAP_THRESHOLD
    ):
        return (
            f"{ticker}'s average 12M outcome is materially above its median, "
            "indicating sensitivity to a high-return observation."
        )
    if median_12m is not None and median_12m < 0:
        return f"{ticker}'s median 12M outcome is negative in this trial."
    if median_12m is None:
        return f"{ticker} has no complete 12M outcome in this trial."
    return (
        f"{ticker}'s median 12M outcome is positive, but the record count "
        "remains limited."
    )


def _ticker_diagnostics(rows: list[dict]) -> list[dict]:
    """Group result diagnostics by ticker."""
    groups: dict[str, list[dict]] = {}
    for row in rows:
        ticker = str(row.get("ticker") or "Missing")
        groups.setdefault(ticker, []).append(row)
    diagnostics = []
    for ticker, group in sorted(groups.items()):
        ordered = sorted(
            (
                row
                for row in group
                if _numeric(row, "forward_return_12m") is not None
            ),
            key=lambda row: _numeric(row, "forward_return_12m") or 0.0,
        )
        diagnostic = {
            "ticker": ticker,
            "records": len(group),
            "median_forward_return_3m": _median(
                group, "forward_return_3m"
            ),
            "median_forward_return_6m": _median(
                group, "forward_return_6m"
            ),
            "median_forward_return_12m": _median(
                group, "forward_return_12m"
            ),
            "average_forward_return_12m": _average(
                group, "forward_return_12m"
            ),
            "median_relative_return_12m": _median(
                group, "relative_return_12m"
            ),
            "hit_rate_vs_benchmark_12m": _rate(
                group, "relative_return_12m"
            ),
            "positive_return_rate_12m": _rate(
                group, "forward_return_12m"
            ),
            "source_verification_status": _metadata_values(
                group, "source_verification_status"
            ),
            "promotion_blocking_bucket": _metadata_values(
                group, "promotion_blocking_bucket"
            ),
            "investor_interest_levels": {
                field: _metadata_values(group, field)
                for field in MISSING_METADATA_FIELDS
                if field.endswith("_interest_level")
            },
            "best_12m_record_date": (
                str(ordered[-1].get("signal_date") or "") if ordered else None
            ),
            "worst_12m_record_date": (
                str(ordered[0].get("signal_date") or "") if ordered else None
            ),
            "range_forward_return_12m": (
                round(
                    (_numeric(ordered[-1], "forward_return_12m") or 0.0)
                    - (_numeric(ordered[0], "forward_return_12m") or 0.0),
                    6,
                )
                if ordered
                else None
            ),
        }
        diagnostic["ticker_interpretation"] = _ticker_interpretation(
            ticker, diagnostic
        )
        diagnostics.append(diagnostic)
    return diagnostics


def _record_summary(row: dict) -> dict:
    return {
        "ticker": str(row.get("ticker") or ""),
        "signal_date": str(row.get("signal_date") or ""),
        "forward_return_12m": _numeric(row, "forward_return_12m"),
        "relative_return_12m": _numeric(row, "relative_return_12m"),
    }


def _outlier_diagnostics(rows: list[dict], metrics: dict) -> dict:
    """Compare average and median outcomes and identify extreme records."""
    ordered = sorted(
        (
            row
            for row in rows
            if _numeric(row, "forward_return_12m") is not None
        ),
        key=lambda row: _numeric(row, "forward_return_12m") or 0.0,
    )
    average_12m = metrics.get("average_forward_return_12m")
    median_12m = metrics.get("median_forward_return_12m")
    gap = (
        round(float(average_12m) - float(median_12m), 6)
        if average_12m is not None and median_12m is not None
        else None
    )
    material = gap is not None and gap > OUTLIER_GAP_THRESHOLD
    return {
        "average_forward_return_12m": average_12m,
        "median_forward_return_12m": median_12m,
        "average_median_gap_12m": gap,
        "material_outlier_influence": material,
        "interpretation": (
            "Average return appears lifted by high-return outliers."
            if material
            else "Average and median 12M outcomes do not show a material gap."
        ),
        "top_records": [
            _record_summary(row) for row in reversed(ordered[-3:])
        ],
        "bottom_records": [_record_summary(row) for row in ordered[:3]],
    }


def _horizon_diagnostics(metrics: dict) -> dict:
    """Compare shorter and longer aggregate horizons."""
    median_3m = metrics.get("median_forward_return_3m")
    median_6m = metrics.get("median_forward_return_6m")
    median_12m = metrics.get("median_forward_return_12m")
    stronger = (
        median_12m is not None
        and median_3m is not None
        and median_6m is not None
        and float(median_12m) - max(float(median_3m), float(median_6m))
        > HORIZON_STRENGTH_THRESHOLD
    )
    return {
        "median_forward_return_3m": median_3m,
        "median_forward_return_6m": median_6m,
        "median_forward_return_12m": median_12m,
        "hit_rate_vs_benchmark_3m": metrics.get(
            "hit_rate_vs_benchmark_3m"
        ),
        "hit_rate_vs_benchmark_6m": metrics.get(
            "hit_rate_vs_benchmark_6m"
        ),
        "hit_rate_vs_benchmark_12m": metrics.get(
            "hit_rate_vs_benchmark_12m"
        ),
        "twelve_month_materially_stronger": stronger,
        "interpretation": (
            "The current readiness events appear more meaningful at 12M than "
            "at shorter horizons. This is an observation, not a trading rule."
            if stronger
            else (
                "The current horizon results do not establish a materially "
                "stronger 12M pattern."
            )
        ),
    }


def build_readiness_trial_diagnostic_report(
    *,
    manifest: dict,
    metrics: dict,
    rows: list[dict],
) -> ReadinessTrialDiagnosticReport:
    """Build diagnostics from completed readiness trial artifacts."""
    if manifest.get("backtest_run_type") != "readiness_trial":
        raise ValueError(
            "Readiness trial diagnostic reports require a readiness_trial run."
        )
    evaluated = [
        row
        for row in rows
        if str(row.get("data_status") or "").startswith("complete")
    ]
    periods = _period_diagnostics(manifest)
    tickers = _ticker_diagnostics(evaluated)
    outliers = _outlier_diagnostics(evaluated, metrics)
    horizon = _horizon_diagnostics(metrics)
    missing = _missing_metadata(evaluated)
    metadata_attribution = build_metadata_attribution_diagnostics(
        metrics=metrics,
        missing_metadata_fields=missing,
        concentration_details=list(
            metrics.get("concentration_details") or []
        ),
    )
    guardrail_counts = dict(
        metrics.get("coverage_guardrail_status_counts") or {}
    )
    clean_records = int(metrics.get("clean_record_count") or 0)
    warning_records = int(metrics.get("warning_record_count") or 0)
    warning_heavy_records = int(
        metrics.get("warning_heavy_record_count") or 0
    )
    delayed_count = sum(
        str(row.get("has_delayed_price_anchor") or "").lower()
        in {"true", "1", "yes"}
        for row in evaluated
    )
    if warning_heavy_records:
        coverage_interpretation = (
            "Warning-heavy records are present, so outcome diagnostics "
            "require additional caution."
        )
    elif delayed_count:
        coverage_interpretation = (
            "Delayed anchors are present. The sample remains useful for "
            "readiness research but is not a clean historical execution "
            "simulation."
        )
    elif clean_records < 5:
        coverage_interpretation = (
            "Too few clean records are available for a clean-only "
            "interpretation."
        )
    else:
        coverage_interpretation = (
            "Clean records are available, while all results remain "
            "readiness-only diagnostics."
        )
    coverage_quality = {
        "coverage_quality_counts": dict(
            metrics.get("coverage_quality_counts") or {}
        ),
        "coverage_severity_counts": dict(
            metrics.get("coverage_severity_counts") or {}
        ),
        "coverage_guardrail_status_counts": guardrail_counts,
        "grouped_coverage_metrics": {
            field: list(
                metrics.get("grouped_metrics", {}).get(field, [])
            )
            for field in (
                "coverage_quality_label",
                "coverage_quality_severity",
                "coverage_guardrail_status",
            )
        },
        "clean_record_count": clean_records,
        "warning_record_count": warning_records,
        "warning_heavy_record_count": warning_heavy_records,
        "unsupported_dates_excluded": int(
            metrics.get("unsupported_dates_excluded_count")
            or guardrail_counts.get("unsupported_excluded", 0)
        ),
        "delayed_anchor_record_count": delayed_count,
        "interpretation": coverage_interpretation,
        "limitations": [
            "Coverage labels describe data quality, not outcome validity.",
            "Delayed anchors do not simulate exact historical execution.",
            "Limited financial coverage remains readiness-only.",
            "Warning records are retained unless explicitly excluded.",
        ],
    }
    clean_coverage_sensitivity = _clean_coverage_sensitivity(manifest)
    complete_tickers = [
        item
        for item in tickers
        if item["average_forward_return_12m"] is not None
        and item["median_forward_return_12m"] is not None
        and item["range_forward_return_12m"] is not None
    ]
    top_contributor = (
        max(
            complete_tickers,
            key=lambda item: item["average_forward_return_12m"],
        )["ticker"]
        if complete_tickers
        else None
    )
    weakest_ticker = (
        min(
            complete_tickers,
            key=lambda item: item["median_forward_return_12m"],
        )["ticker"]
        if complete_tickers
        else None
    )
    most_volatile = (
        max(
            complete_tickers,
            key=lambda item: item["range_forward_return_12m"],
        )["ticker"]
        if complete_tickers
        else None
    )
    nvda_major_driver = (
        top_contributor == "NVDA"
        and bool(outliers["top_records"])
        and outliers["top_records"][0]["ticker"] == "NVDA"
        and outliers["material_outlier_influence"]
    )
    concentration = {
        "evaluated_ticker_count": len(tickers),
        "duplicate_records_removed": int(
            manifest.get("duplicate_records_removed") or 0
        ),
        "concentration_warning": bool(metrics.get("concentration_warning")),
        "concentration_details": list(
            metrics.get("concentration_details") or []
        ),
        "missing_metadata_fields": missing,
        "top_contributor_by_average_12m": top_contributor,
        "weakest_ticker_by_median_12m": weakest_ticker,
        "most_volatile_ticker_by_range_12m": most_volatile,
        "nvda_major_driver": nvda_major_driver,
        "metadata_enrichment_status_counts": _metadata_status_counts(
            evaluated
        ),
        "grouped_metadata_availability": (
            _grouped_metadata_availability(evaluated)
        ),
    }
    stability = {
        "walk_forward_enabled": bool(manifest.get("walk_forward_enabled")),
        "walk_forward_stability_judgment": manifest.get(
            "walk_forward_stability_judgment"
        )
        or "not_enabled",
        "periods_evaluated": len(periods),
        "periods_with_positive_relative_12m": sum(
            (period.get("median_relative_return_12m") or 0) > 0
            for period in periods
        ),
        "periods_with_negative_or_weak_absolute_12m": sum(
            (period.get("median_forward_return_12m") or 0) <= 0
            for period in periods
        ),
        "strongest_period_by_median_relative_12m": (
            max(
                periods,
                key=lambda period: (
                    period.get("median_relative_return_12m")
                    if period.get("median_relative_return_12m") is not None
                    else float("-inf")
                ),
            ).get("period")
            if periods
            else None
        ),
        "weakest_period_by_median_relative_12m": (
            min(
                periods,
                key=lambda period: (
                    period.get("median_relative_return_12m")
                    if period.get("median_relative_return_12m") is not None
                    else float("inf")
                ),
            ).get("period")
            if periods
            else None
        ),
    }
    if len(evaluated) < 5:
        diagnostic_status = "insufficient_data"
    elif stability["walk_forward_stability_judgment"] in {
        "unstable",
        "mixed",
    }:
        diagnostic_status = "unstable_needs_deeper_review"
    elif outliers["material_outlier_influence"] or missing:
        diagnostic_status = "promising_but_unproven"
    else:
        diagnostic_status = "diagnostic_only"
    next_action = "expand_dates_tickers_and_enrich_metadata"
    key_findings = [
        (
            f"{len(evaluated)} deduped readiness records were evaluated across "
            f"{len(tickers)} tickers."
        ),
        outliers["interpretation"],
        horizon["interpretation"],
        (
            f"Walk-forward stability is "
            f"{stability['walk_forward_stability_judgment']}."
        ),
    ]
    if nvda_major_driver:
        key_findings.append(
            "NVDA is a major driver of the high 12M average in this sample."
        )
    if missing:
        key_findings.append(
            "Missing metadata prevents grouped attribution by readiness "
            "quality or investor interest."
        )
    key_findings.extend(
        metadata_attribution["attribution_findings"]
    )
    key_findings.append(coverage_interpretation)
    aggregate_fields = (
        "median_forward_return_3m",
        "median_forward_return_6m",
        "median_forward_return_12m",
        "average_forward_return_12m",
        "median_relative_return_12m",
        "hit_rate_vs_benchmark_12m",
        "worst_max_drawdown_12m",
    )
    return ReadinessTrialDiagnosticReport(
        backtest_run_id=str(manifest.get("backtest_run_id") or ""),
        backtest_run_type="readiness_trial",
        sample_size=len(evaluated),
        evaluated_tickers=[item["ticker"] for item in tickers],
        periods_evaluated=len(periods),
        aggregate_metrics={
            field: metrics.get(field) for field in aggregate_fields
        },
        period_diagnostics=periods,
        ticker_diagnostics=tickers,
        horizon_diagnostics=horizon,
        outlier_diagnostics=outliers,
        concentration_diagnostics=concentration,
        stability_diagnostics=stability,
        coverage_quality_diagnostics=coverage_quality,
        clean_coverage_sensitivity=clean_coverage_sensitivity,
        metadata_attribution_diagnostics=metadata_attribution,
        missing_metadata_fields=missing,
        key_findings=key_findings,
        diagnostic_status=diagnostic_status,
        next_research_action=next_action,
    )


def _display(value: object) -> str:
    if value is None:
        return "Missing"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _render_attribution_table(attribution: dict) -> list[str]:
    """Render one compact grouped metadata comparison table."""
    lines = [
        (
            "| Group | Sample Size | Median 12M | Median Relative 12M | "
            "Hit Rate 12M | Small Sample Warning | Interpretation |"
        ),
        "|---|---:|---:|---:|---:|---|---|",
    ]
    groups = attribution.get("groups", [])
    for group in groups:
        lines.append(
            f"| {group['group_name']} | {group['sample_size']} | "
            f"{_display(group['median_forward_return_12m'])} | "
            f"{_display(group['median_relative_return_12m'])} | "
            f"{_display(group['hit_rate_vs_benchmark_12m'])} | "
            f"{_display(group['small_sample_warning'])} | "
            f"{attribution['interpretation']} |"
        )
    if not groups:
        lines.append(
            "| Missing | 0 | Missing | Missing | Missing | True | "
            "No populated group is available. |"
        )
    return lines


def _render_interest_attribution(attributions: dict) -> list[str]:
    """Render compact investor-interest diversity diagnostics."""
    lines = [
        "| Investor Field | Available | Groups | Max Group Share | "
        "Attribution Usefulness | Interpretation |",
        "|---|---|---:|---:|---|---|",
    ]
    for field in INTEREST_FIELDS:
        attribution = attributions[field]
        diversity = attribution["group_diversity"]
        available = bool(attribution["groups"])
        lines.append(
            f"| {field} | {'Yes' if available else 'No'} | "
            f"{diversity['group_count']} | "
            f"{_display(diversity['max_group_share'])} | "
            f"{'useful' if diversity['has_useful_diversity'] else 'limited'} | "
            f"{diversity['diversity_interpretation']} |"
        )
    return lines


def _render_diversity_summary(diversity_by_field: dict) -> list[str]:
    """Render compact diversity status for every grouped metadata field."""
    lines = [
        "| Field | Groups | Total Records | Max Group Share | "
        "Smallest Group | Useful Diversity | Status |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for field in ATTRIBUTION_FIELDS:
        diversity = diversity_by_field[field]
        lines.append(
            f"| {field} | {diversity['group_count']} | "
            f"{diversity['total_records']} | "
            f"{_display(diversity['max_group_share'])} | "
            f"{diversity['smallest_group_sample_size']} | "
            f"{_display(diversity['has_useful_diversity'])} | "
            f"{diversity['attribution_status']} |"
        )
    return lines


def render_readiness_trial_diagnostic_report(
    report: ReadinessTrialDiagnosticReport,
) -> str:
    """Render the standalone readiness trial diagnostic report."""
    attribution = report.metadata_attribution_diagnostics
    if report.diagnostic_status == "insufficient_data":
        main_finding = (
            "The readiness trial has insufficient data for a reliable "
            "diagnostic interpretation."
        )
    elif report.diagnostic_status == "unstable_needs_deeper_review":
        if (
            attribution["metadata_enrichment_detected"]
            and not report.missing_metadata_fields
        ):
            main_finding = (
                "The readiness trial shows useful 12M relative evidence, but "
                "results remain unstable and sensitive to outliers, limited "
                "coverage, and low metadata diversity."
            )
        else:
            main_finding = (
                "The readiness trial shows useful 12M relative evidence, but "
                "results remain unstable and sensitive to outliers, limited "
                "coverage, and missing metadata."
            )
    else:
        main_finding = (
            "The readiness trial provides diagnostic evidence that requires "
            "broader coverage and metadata before interpretation."
        )
    lines = [
        "# Readiness Trial Diagnostic Report",
        "",
        "## Diagnostic Summary",
        "",
        f"- Diagnostic Status: {report.diagnostic_status}",
        f"- Sample Size: {report.sample_size}",
        f"- Periods Evaluated: {report.periods_evaluated}",
        f"- Evaluated Tickers: {', '.join(report.evaluated_tickers)}",
        f"- Main Finding: {main_finding}",
        "",
        "## Aggregate Result Review",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for field, value in report.aggregate_metrics.items():
        lines.append(f"| {field} | {_display(value)} |")
    lines.extend(
        [
            "",
            "These are diagnostic research metrics only.",
            "",
            "## Walk-Forward Period Review",
            "",
            (
                "| Period | Sample Size | Median 12M | Median Relative 12M | "
                "Hit Rate 12M | Interpretation |"
            ),
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for period in report.period_diagnostics:
        lines.append(
            f"| {period['period']} | {period['sample_size']} | "
            f"{_display(period['median_forward_return_12m'])} | "
            f"{_display(period['median_relative_return_12m'])} | "
            f"{_display(period['hit_rate_vs_benchmark_12m'])} | "
            f"{period['period_interpretation']} |"
        )
    lines.extend(
        [
            "",
            "## Ticker Contribution Review",
            "",
            (
                "| Ticker | Records | Median 12M | Average 12M | "
                "Median Relative 12M | Hit Rate 12M | Interpretation |"
            ),
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for ticker in report.ticker_diagnostics:
        lines.append(
            f"| {ticker['ticker']} | {ticker['records']} | "
            f"{_display(ticker['median_forward_return_12m'])} | "
            f"{_display(ticker['average_forward_return_12m'])} | "
            f"{_display(ticker['median_relative_return_12m'])} | "
            f"{_display(ticker['hit_rate_vs_benchmark_12m'])} | "
            f"{ticker['ticker_interpretation']} |"
        )
    outliers = report.outlier_diagnostics
    lines.extend(
        [
            "",
            "## Outlier Review",
            "",
            (
                "- Average vs Median 12M Gap: "
                f"{_display(outliers['average_median_gap_12m'])}"
            ),
            f"- Interpretation: {outliers['interpretation']}",
            (
                "- NVDA Major Driver: "
                f"{report.concentration_diagnostics['nvda_major_driver']}"
            ),
            "",
            "### Highest 12M Records",
            "",
            "| Ticker | Signal Date | Forward 12M | Relative 12M |",
            "|---|---|---:|---:|",
        ]
    )
    for record in outliers["top_records"]:
        lines.append(
            f"| {record['ticker']} | {record['signal_date']} | "
            f"{_display(record['forward_return_12m'])} | "
            f"{_display(record['relative_return_12m'])} |"
        )
    lines.extend(
        [
            "",
            "### Lowest 12M Records",
            "",
            "| Ticker | Signal Date | Forward 12M | Relative 12M |",
            "|---|---|---:|---:|",
        ]
    )
    for record in outliers["bottom_records"]:
        lines.append(
            f"| {record['ticker']} | {record['signal_date']} | "
            f"{_display(record['forward_return_12m'])} | "
            f"{_display(record['relative_return_12m'])} |"
        )
    horizon = report.horizon_diagnostics
    lines.extend(
        [
            "",
            "## Horizon Review",
            "",
            "| Horizon | Median Return | Hit Rate vs Benchmark |",
            "|---|---:|---:|",
            (
                "| 3M | "
                f"{_display(horizon['median_forward_return_3m'])} | "
                f"{_display(horizon['hit_rate_vs_benchmark_3m'])} |"
            ),
            (
                "| 6M | "
                f"{_display(horizon['median_forward_return_6m'])} | "
                f"{_display(horizon['hit_rate_vs_benchmark_6m'])} |"
            ),
            (
                "| 12M | "
                f"{_display(horizon['median_forward_return_12m'])} | "
                f"{_display(horizon['hit_rate_vs_benchmark_12m'])} |"
            ),
            "",
            horizon["interpretation"],
            "",
            "## Stability Review",
            "",
            (
                "- Walk-Forward Stability Judgment: "
                f"{report.stability_diagnostics['walk_forward_stability_judgment']}"
            ),
            (
                "- Periods With Positive Relative 12M: "
                f"{report.stability_diagnostics['periods_with_positive_relative_12m']}"
            ),
            (
                "- Periods With Negative or Weak Absolute 12M: "
                f"{report.stability_diagnostics['periods_with_negative_or_weak_absolute_12m']}"
            ),
            (
                "- Strongest Period by Median Relative 12M: "
                f"{_display(report.stability_diagnostics['strongest_period_by_median_relative_12m'])}"
            ),
            (
                "- Weakest Period by Median Relative 12M: "
                f"{_display(report.stability_diagnostics['weakest_period_by_median_relative_12m'])}"
            ),
            (
                "- The period variation indicates that aggregate results "
                "should not be treated as stable evidence."
            ),
            "",
            "## Coverage Quality Guardrails",
            "",
            (
                "- Coverage Quality Counts: "
                f"{report.coverage_quality_diagnostics['coverage_quality_counts']}"
            ),
            (
                "- Coverage Severity Counts: "
                f"{report.coverage_quality_diagnostics['coverage_severity_counts']}"
            ),
            (
                "- Clean Records: "
                f"{report.coverage_quality_diagnostics['clean_record_count']}"
            ),
            (
                "- Warning Records: "
                f"{report.coverage_quality_diagnostics['warning_record_count']}"
            ),
            (
                "- Warning-Heavy Records: "
                f"{report.coverage_quality_diagnostics['warning_heavy_record_count']}"
            ),
            (
                "- Unsupported Dates Excluded: "
                f"{report.coverage_quality_diagnostics['unsupported_dates_excluded']}"
            ),
            (
                "- Interpretation: "
                f"{report.coverage_quality_diagnostics['interpretation']}"
            ),
            "",
            "| Guardrail Group | Sample Size | Median 12M | "
            "Median Relative 12M | Hit Rate 12M |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for group in report.coverage_quality_diagnostics[
        "grouped_coverage_metrics"
    ]["coverage_guardrail_status"]:
        lines.append(
            f"| {group['group_name']} | {group['sample_size']} | "
            f"{_display(group['median_forward_return_12m'])} | "
            f"{_display(group['median_relative_return_12m'])} | "
            f"{_display(group['hit_rate_vs_benchmark_12m'])} |"
        )
    lines.extend(
        [
            "",
            *[
                f"- Limitation: {limitation}"
                for limitation in report.coverage_quality_diagnostics[
                    "limitations"
                ]
            ],
            "",
            "## Clean-Coverage Sensitivity",
            "",
            (
                "- Sensitivity Status: "
                f"{report.clean_coverage_sensitivity['sensitivity_status']}"
            ),
            (
                "- Clean-Only Available: "
                f"{'Yes' if report.clean_coverage_sensitivity['clean_only_available'] else 'No'}"
            ),
            (
                "- Warning-Heavy Comparison: "
                f"{report.clean_coverage_sensitivity['warning_heavy_comparison_summary']}"
            ),
            (
                "- Delayed-Anchor Comparison: "
                f"{report.clean_coverage_sensitivity['delayed_anchor_comparison_summary']}"
            ),
            (
                "- Interpretation: "
                f"{report.clean_coverage_sensitivity['interpretation']}"
            ),
            "",
            "## Metadata Attribution Review",
            "",
            (
                "- Metadata Enrichment Detected: "
                f"{'Yes' if attribution['metadata_enrichment_detected'] else 'No'}"
            ),
            (
                "- Metadata Status Counts: "
                f"{attribution['metadata_enrichment_status_counts']}"
            ),
            (
                "- Missing Metadata Fields: "
                f"{', '.join(attribution['missing_metadata_fields']) or 'None'}"
            ),
            (
                "- Grouped Metadata Availability: "
                f"{attribution['grouped_metadata_availability']}"
            ),
            "",
            "### Group Diversity Summary",
            "",
            *_render_diversity_summary(attribution["group_diversity"]),
            "",
            "### Readiness Label Attribution",
            "",
            *_render_attribution_table(
                attribution["readiness_label_attribution"]
            ),
            "",
            "### Source Verification Attribution",
            "",
            *_render_attribution_table(
                attribution["source_verification_attribution"]
            ),
            "",
            "### Investor Interest Attribution",
            "",
            *_render_interest_attribution(
                attribution["investor_interest_attribution"]
            ),
            "",
            (
                "Investor interest metadata is present but has low diversity "
                "and cannot yet explain performance differences."
                if all(
                    not item["group_diversity"]["has_useful_diversity"]
                    for item in attribution[
                        "investor_interest_attribution"
                    ].values()
                )
                else (
                    "Some investor interest fields permit preliminary "
                    "non-causal comparisons; small groups remain limited."
                )
            ),
            "",
            "### Promotion Blocking Attribution",
            "",
            *_render_attribution_table(
                attribution["promotion_blocking_attribution"]
            ),
            "",
            (
                "Promotion blocker metadata is present, but the current trial "
                "set lacks useful diversity."
                if not attribution["promotion_blocking_attribution"][
                    "group_diversity"
                ]["has_useful_diversity"]
                else (
                    "Promotion blocker groups permit a preliminary non-causal "
                    "comparison."
                )
            ),
            "",
            "### Attribution Limitations",
            "",
            *[
                f"- {limitation}"
                for limitation in attribution["attribution_limitations"]
            ],
            "",
            "## Data Quality / Metadata Gaps",
            "",
            (
                "- Duplicate Records Removed: "
                f"{report.concentration_diagnostics['duplicate_records_removed']}"
            ),
            (
                "- Concentration Warning: "
                f"{report.concentration_diagnostics['concentration_warning']}"
            ),
            (
                "- Evaluated Ticker Count: "
                f"{report.concentration_diagnostics['evaluated_ticker_count']}"
            ),
            (
                "- Leading Average 12M Contributor: "
                f"{_display(report.concentration_diagnostics['top_contributor_by_average_12m'])}"
            ),
            (
                "- Widest 12M Range: "
                f"{_display(report.concentration_diagnostics['most_volatile_ticker_by_range_12m'])}"
            ),
            "",
            (
                "Metadata enrichment status counts: "
                f"{report.concentration_diagnostics['metadata_enrichment_status_counts']}"
            ),
            (
                "Grouped metadata availability: "
                f"{report.concentration_diagnostics['grouped_metadata_availability']}"
            ),
        ]
    )
    lines.extend(
        [
            "",
            (
                "Missing metadata prevents grouped attribution by readiness "
                "quality or investor agent interest when fields remain absent."
                if report.missing_metadata_fields
                else (
                    "Rows with available metadata can now be grouped "
                    "separately. This does not imply investor validation."
                )
            ),
            "",
            "## What This Suggests",
            "",
            "- The pipeline is now producing useful diagnostic evidence.",
            "- The readiness concept may deserve broader research testing.",
            (
            "- The current dataset remains too small and concentrated for "
                "validation."
            ),
            "- More dates and/or more tickers are needed.",
            (
                "- Remaining metadata gaps should be reduced to explain why "
                "cases performed differently."
                if report.missing_metadata_fields
                else (
                    "- More variation within metadata groups is needed to "
                    "explain why cases performed differently."
                )
            ),
            "",
            "## What This Does Not Suggest",
            "",
            "- It does not prove a strategy.",
            "- It does not validate investor agent performance.",
            "- It does not create a recommendation.",
            "- It does not create a trade signal.",
            "- It does not justify allocation or rebalancing.",
            "",
            "## Next Research Action",
            "",
            f"- Action Code: {report.next_research_action}",
            "- Expand historical date coverage or add more tickers.",
            (
                "- Enrich remaining readiness metadata fields."
                if report.missing_metadata_fields
                else "- Expand variation across readiness metadata groups."
            ),
            "- Preserve dedupe controls.",
            "- Consider ticker/year diagnostic charts in a later task.",
            "",
            "## Safety Notice",
            "",
            report.safety_notice,
            "",
        ]
    )
    return "\n".join(lines)


def write_readiness_trial_diagnostic_report(
    *,
    output_dir: Path,
    manifest: dict,
    metrics: dict,
    rows: list[dict],
) -> ReadinessTrialDiagnosticReportFiles:
    """Build and persist diagnostic report artifacts."""
    report = build_readiness_trial_diagnostic_report(
        manifest=manifest,
        metrics=metrics,
        rows=rows,
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "readiness_trial_diagnostic_report.json"
    markdown_path = output_dir / "readiness_trial_diagnostic_report.md"
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_readiness_trial_diagnostic_report(report),
        encoding="utf-8",
    )
    return ReadinessTrialDiagnosticReportFiles(
        markdown_path=markdown_path,
        json_path=json_path,
        report=report,
    )


def regenerate_readiness_trial_diagnostic_report(
    backtest_folder: Path,
) -> ReadinessTrialDiagnosticReportFiles:
    """Regenerate diagnostics from an existing readiness backtest folder."""
    backtest_folder = Path(backtest_folder)
    manifest_path = backtest_folder / "backtest_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Backtest manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    metrics = json.loads(
        Path(manifest["metrics_summary_path"]).read_text(encoding="utf-8")
    )
    with Path(manifest["results_path"]).open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))
    files = write_readiness_trial_diagnostic_report(
        output_dir=backtest_folder,
        manifest=manifest,
        metrics=metrics,
        rows=rows,
    )
    manifest.update(
        {
            "readiness_trial_diagnostic_report_path": str(
                files.markdown_path
            ),
            "readiness_trial_diagnostic_report_json_path": str(
                files.json_path
            ),
            "diagnostic_status": files.report.diagnostic_status,
            "next_research_action": files.report.next_research_action,
        }
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    return files
