"""Outlier and ex-NVDA sensitivity diagnostics for readiness backtests."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from statistics import mean, median

MATERIAL_AVERAGE_DROP = 0.15
SAFETY_NOTICE = (
    "This outlier and Ex-NVDA sensitivity report is not a recommendation, "
    "ranking, vote, average score, consensus, allocation instruction, "
    "rebalancing instruction, trade signal, execution instruction, or "
    "investment advice."
)
SUBSET_FILTERS = {
    "all_records": "All complete readiness trial records.",
    "ex_nvda": "All complete records except ticker NVDA.",
    "nvda_only": "Complete records where ticker is NVDA.",
    "ex_top_1_forward_12m": (
        "All complete records except the highest forward 12M return."
    ),
    "ex_top_2_forward_12m": (
        "All complete records except the two highest forward 12M returns."
    ),
    "ex_top_3_forward_12m": (
        "All complete records except the three highest forward 12M returns."
    ),
    "capped_top_12m": (
        "Forward 12M returns are capped at the third-highest observed value "
        "for report-only sensitivity."
    ),
    "non_extreme_records": (
        "All complete records except the highest and lowest forward 12M "
        "returns."
    ),
}


@dataclass(frozen=True)
class OutlierSensitivityReport:
    """Structured outlier and ticker-exclusion sensitivity diagnostics."""

    backtest_run_id: str
    backtest_run_type: str
    total_sample_size: int
    subset_diagnostics: dict[str, dict]
    top_outliers: list[dict]
    outlier_impact_assessment: dict
    key_findings: list[str]
    limitations: list[str]
    outlier_dependence_status: str
    next_research_action: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready representation."""
        return asdict(self)


@dataclass(frozen=True)
class OutlierSensitivityReportFiles:
    """Generated outlier sensitivity artifact paths and content."""

    markdown_path: Path
    json_path: Path
    report: OutlierSensitivityReport


def _numeric_value(row: dict, field: str) -> float | None:
    value = row.get(field)
    if value in {"", None}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _numeric_values(rows: list[dict], field: str) -> list[float]:
    return [
        value
        for row in rows
        if (value := _numeric_value(row, field)) is not None
    ]


def _stat(rows: list[dict], field: str, calculator) -> float | None:
    values = _numeric_values(rows, field)
    return round(calculator(values), 6) if values else None


def _rate(rows: list[dict], field: str) -> float | None:
    values = _numeric_values(rows, field)
    if not values:
        return None
    return round(sum(value > 0 for value in values) / len(values), 6)


def _complete_rows(rows: list[dict]) -> list[dict]:
    return [
        row
        for row in rows
        if str(row.get("data_status") or "").startswith("complete")
    ]


def identify_top_outliers(rows: list[dict], limit: int = 3) -> list[dict]:
    """Return the highest forward 12M records in descending order."""
    ranked = sorted(
        (
            row
            for row in _complete_rows(rows)
            if _numeric_value(row, "forward_return_12m") is not None
        ),
        key=lambda row: _numeric_value(row, "forward_return_12m")
        or float("-inf"),
        reverse=True,
    )
    return [
        {
            "rank": rank,
            "ticker": str(row.get("ticker") or ""),
            "signal_date": str(row.get("signal_date") or ""),
            "forward_return_12m": _numeric_value(
                row, "forward_return_12m"
            ),
            "relative_return_12m": _numeric_value(
                row, "relative_return_12m"
            ),
        }
        for rank, row in enumerate(ranked[:limit], start=1)
    ]


def summarize_outlier_subset(
    *,
    subset_name: str,
    rows: list[dict],
    total_sample_size: int,
) -> dict:
    """Summarize one outlier subset without fabricating absent metrics."""
    sample_size = len(rows)
    available = sample_size > 0
    if not available:
        interpretation = f"No records are available for {subset_name}."
    elif sample_size < 5:
        interpretation = (
            f"{subset_name} is available but remains small-sample limited."
        )
    else:
        interpretation = (
            f"{subset_name} provides a research-only sensitivity comparison."
        )
    drawdowns = _numeric_values(rows, "max_drawdown_12m")
    return {
        "subset_name": subset_name,
        "filter_description": SUBSET_FILTERS[subset_name],
        "sample_size": sample_size,
        "share_of_total": (
            round(sample_size / total_sample_size, 6)
            if total_sample_size
            else 0.0
        ),
        "evaluated_tickers": sorted(
            {str(row.get("ticker")) for row in rows if row.get("ticker")}
        ),
        "median_forward_return_3m": _stat(
            rows, "forward_return_3m", median
        ),
        "median_forward_return_6m": _stat(
            rows, "forward_return_6m", median
        ),
        "median_forward_return_12m": _stat(
            rows, "forward_return_12m", median
        ),
        "average_forward_return_12m": _stat(
            rows, "forward_return_12m", mean
        ),
        "median_relative_return_12m": _stat(
            rows, "relative_return_12m", median
        ),
        "average_relative_return_12m": _stat(
            rows, "relative_return_12m", mean
        ),
        "hit_rate_vs_benchmark_12m": _rate(
            rows, "relative_return_12m"
        ),
        "positive_return_rate_12m": _rate(
            rows, "forward_return_12m"
        ),
        "median_max_drawdown_12m": _stat(
            rows, "max_drawdown_12m", median
        ),
        "worst_max_drawdown_12m": (
            round(min(drawdowns), 6) if drawdowns else None
        ),
        "small_sample_warning": sample_size < 5,
        "available": available,
        "interpretation": interpretation,
    }


def _capped_rows(ranked: list[dict]) -> list[dict]:
    if not ranked:
        return []
    values = [
        value
        for row in ranked
        if (value := _numeric_value(row, "forward_return_12m")) is not None
    ]
    if not values:
        return [dict(row) for row in ranked]
    cap = sorted(values, reverse=True)[min(2, len(values) - 1)]
    capped = []
    for row in ranked:
        copied = dict(row)
        value = _numeric_value(row, "forward_return_12m")
        if value is not None:
            copied["forward_return_12m"] = min(value, cap)
        capped.append(copied)
    return capped


def build_outlier_sensitivity_diagnostics(
    rows: list[dict],
) -> dict[str, dict]:
    """Build ticker and extreme-return exclusion subsets."""
    evaluated = _complete_rows(rows)
    ranked = sorted(
        evaluated,
        key=lambda row: _numeric_value(row, "forward_return_12m")
        if _numeric_value(row, "forward_return_12m") is not None
        else float("-inf"),
        reverse=True,
    )
    subsets = {
        "all_records": evaluated,
        "ex_nvda": [
            row
            for row in evaluated
            if str(row.get("ticker") or "").upper() != "NVDA"
        ],
        "nvda_only": [
            row
            for row in evaluated
            if str(row.get("ticker") or "").upper() == "NVDA"
        ],
        "ex_top_1_forward_12m": ranked[1:],
        "ex_top_2_forward_12m": ranked[2:],
        "ex_top_3_forward_12m": ranked[3:],
        "capped_top_12m": _capped_rows(ranked),
        "non_extreme_records": ranked[1:-1] if len(ranked) >= 3 else [],
    }
    return {
        name: summarize_outlier_subset(
            subset_name=name,
            rows=subset,
            total_sample_size=len(evaluated),
        )
        for name, subset in subsets.items()
    }


def _positive(subset: dict) -> bool:
    return (
        subset.get("available")
        and subset.get("median_forward_return_12m") is not None
        and float(subset["median_forward_return_12m"]) > 0
        and subset.get("median_relative_return_12m") is not None
        and float(subset["median_relative_return_12m"]) > 0
        and subset.get("hit_rate_vs_benchmark_12m") is not None
        and float(subset["hit_rate_vs_benchmark_12m"]) >= 0.5
    )


def compare_outlier_subsets(
    subsets: dict[str, dict],
    top_outliers: list[dict],
) -> dict:
    """Assess whether NVDA or extreme winners dominate the result."""
    all_records = subsets["all_records"]
    ex_nvda = subsets["ex_nvda"]
    nvda_only = subsets["nvda_only"]
    ex_top_1 = subsets["ex_top_1_forward_12m"]
    ex_top_2 = subsets["ex_top_2_forward_12m"]
    ex_top_3 = subsets["ex_top_3_forward_12m"]
    nvda_present = nvda_only["available"]

    def drop(field: str) -> float | None:
        all_value = all_records.get(field)
        ex_value = ex_nvda.get(field)
        if all_value is None or ex_value is None:
            return None
        return round(float(all_value) - float(ex_value), 6)

    median_drop = drop("median_forward_return_12m")
    average_drop = drop("average_forward_return_12m")
    hit_rate_drop = drop("hit_rate_vs_benchmark_12m")
    ex_nvda_positive = _positive(ex_nvda)
    ex_top_1_positive = _positive(ex_top_1)
    ex_top_2_positive = _positive(ex_top_2)
    ex_top_3_positive = _positive(ex_top_3)
    average_materially_lifted = (
        average_drop is not None and average_drop >= MATERIAL_AVERAGE_DROP
    )
    if all_records["sample_size"] < 5:
        status = "insufficient_sample"
    elif nvda_present and not ex_nvda_positive:
        status = "result_sensitive_to_nvda"
    elif not ex_top_1_positive or not ex_top_2_positive:
        status = "result_sensitive_to_top_outliers"
    elif nvda_present and average_materially_lifted:
        status = "nvda_lifts_average_but_result_survives"
    elif ex_nvda_positive and ex_top_2_positive:
        status = "outliers_present_but_result_survives"
    else:
        status = "no_outlier_issue_detected"

    if status == "nvda_lifts_average_but_result_survives":
        interpretation = (
            "NVDA materially lifts the average 12M return, while the ex-NVDA "
            "median, relative median, and hit rate remain positive."
        )
    elif status == "result_sensitive_to_nvda":
        interpretation = (
            "The positive result does not survive the conservative ex-NVDA "
            "test and remains sensitive to NVDA."
        )
    elif status == "result_sensitive_to_top_outliers":
        interpretation = (
            "The positive median does not survive one of the top-outlier "
            "exclusions and remains outlier-sensitive."
        )
    elif status == "outliers_present_but_result_survives":
        interpretation = (
            "Extreme winners are present, but ex-NVDA and ex-top-2 subsets "
            "retain positive median, relative, and hit-rate evidence."
        )
    elif status == "insufficient_sample":
        interpretation = (
            "The evaluated sample is too small for a stable outlier "
            "sensitivity assessment."
        )
    else:
        interpretation = (
            "The available exclusions do not show a material outlier "
            "dependence at the selected thresholds."
        )
    top = top_outliers[0] if top_outliers else {}
    return {
        "nvda_present": nvda_present,
        "nvda_record_count": nvda_only["sample_size"],
        "nvda_share_of_total": nvda_only["share_of_total"],
        "all_records_median_12m": all_records.get(
            "median_forward_return_12m"
        ),
        "ex_nvda_median_12m": ex_nvda.get("median_forward_return_12m"),
        "all_records_average_12m": all_records.get(
            "average_forward_return_12m"
        ),
        "ex_nvda_average_12m": ex_nvda.get("average_forward_return_12m"),
        "all_records_hit_rate_12m": all_records.get(
            "hit_rate_vs_benchmark_12m"
        ),
        "ex_nvda_hit_rate_12m": ex_nvda.get(
            "hit_rate_vs_benchmark_12m"
        ),
        "median_drop_ex_nvda": median_drop,
        "average_drop_ex_nvda": average_drop,
        "hit_rate_drop_ex_nvda": hit_rate_drop,
        "top_1_outlier_ticker": top.get("ticker"),
        "top_1_outlier_signal_date": top.get("signal_date"),
        "top_1_forward_return_12m": top.get("forward_return_12m"),
        "top_1_relative_return_12m": top.get("relative_return_12m"),
        "top_3_outlier_tickers": [
            item["ticker"] for item in top_outliers[:3]
        ],
        "outlier_dependence_status": status,
        "ex_nvda_positive": ex_nvda_positive,
        "ex_top_1_positive": ex_top_1_positive,
        "ex_top_2_positive": ex_top_2_positive,
        "ex_top_3_positive": ex_top_3_positive,
        "average_materially_lifted_by_nvda": average_materially_lifted,
        "interpretation": interpretation,
    }


def build_outlier_sensitivity_report(
    *,
    manifest: dict,
    rows: list[dict],
) -> OutlierSensitivityReport:
    """Build a conservative outlier sensitivity report."""
    if manifest.get("backtest_run_type") != "readiness_trial":
        raise ValueError(
            "Outlier sensitivity requires a readiness_trial run."
        )
    subsets = build_outlier_sensitivity_diagnostics(rows)
    top_outliers = identify_top_outliers(rows)
    assessment = compare_outlier_subsets(subsets, top_outliers)
    findings = [assessment["interpretation"]]
    if (
        subsets["all_records"].get("average_forward_return_12m") is not None
        and subsets["all_records"].get("median_forward_return_12m")
        is not None
        and (
            float(subsets["all_records"]["average_forward_return_12m"])
            - float(subsets["all_records"]["median_forward_return_12m"])
            >= MATERIAL_AVERAGE_DROP
        )
    ):
        findings.append(
            "The aggregate average materially exceeds the median and is "
            "sensitive to extreme winners."
        )
    next_action = (
        "run_outlier_controlled_expanded_trial"
        if assessment["ex_nvda_positive"]
        and assessment["ex_top_2_positive"]
        else "expand_ticker_universe_with_coverage_validation"
    )
    return OutlierSensitivityReport(
        backtest_run_id=str(manifest.get("backtest_run_id") or ""),
        backtest_run_type="readiness_trial",
        total_sample_size=subsets["all_records"]["sample_size"],
        subset_diagnostics=subsets,
        top_outliers=top_outliers,
        outlier_impact_assessment=assessment,
        key_findings=findings,
        limitations=[
            "Ticker and outlier subsets may differ by date composition.",
            "Exclusions reduce sample size and do not establish causality.",
            "The capped subset changes report-only values, not backtest data.",
            "Coverage and financial-data warnings remain applicable.",
        ],
        outlier_dependence_status=assessment[
            "outlier_dependence_status"
        ],
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


def render_outlier_sensitivity_report(
    report: OutlierSensitivityReport,
) -> str:
    """Render the standalone outlier sensitivity report."""
    assessment = report.outlier_impact_assessment
    subsets = report.subset_diagnostics
    lines = [
        "# Outlier and Ex-NVDA Sensitivity Report",
        "",
        "## Executive Summary",
        "",
        f"- Outlier Dependence Status: {report.outlier_dependence_status}",
        f"- Total Sample Size: {report.total_sample_size}",
        f"- NVDA Record Count: {assessment['nvda_record_count']}",
        f"- NVDA Share of Total: {_display(assessment['nvda_share_of_total'])}",
        f"- Main Finding: {assessment['interpretation']}",
        "",
        "## Top Outliers",
        "",
        "| Rank | Ticker | Signal Date | Forward 12M | Relative 12M |",
        "|---:|---|---|---:|---:|",
    ]
    for item in report.top_outliers:
        lines.append(
            f"| {item['rank']} | {item['ticker']} | "
            f"{item['signal_date']} | "
            f"{_display(item['forward_return_12m'])} | "
            f"{_display(item['relative_return_12m'])} |"
        )
    lines.extend(
        [
            "",
            "## Subset Comparison",
            "",
            (
                "| Subset | Sample | Share | Median 12M | Average 12M | "
                "Median Relative 12M | Hit Rate 12M | Worst Drawdown | "
                "Available | Interpretation |"
            ),
            "|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for subset in subsets.values():
        lines.append(
            f"| {subset['subset_name']} | {subset['sample_size']} | "
            f"{_display(subset['share_of_total'])} | "
            f"{_display(subset['median_forward_return_12m'])} | "
            f"{_display(subset['average_forward_return_12m'])} | "
            f"{_display(subset['median_relative_return_12m'])} | "
            f"{_display(subset['hit_rate_vs_benchmark_12m'])} | "
            f"{_display(subset['worst_max_drawdown_12m'])} | "
            f"{_display(subset['available'])} | "
            f"{subset['interpretation']} |"
        )
    lines.extend(
        [
            "",
            "## Ex-NVDA Sensitivity",
            "",
            (
                "- All Records Median 12M: "
                f"{_display(assessment['all_records_median_12m'])}"
            ),
            (
                "- Ex-NVDA Median 12M: "
                f"{_display(assessment['ex_nvda_median_12m'])}"
            ),
            (
                "- All Records Average 12M: "
                f"{_display(assessment['all_records_average_12m'])}"
            ),
            (
                "- Ex-NVDA Average 12M: "
                f"{_display(assessment['ex_nvda_average_12m'])}"
            ),
            f"- Ex-NVDA Positive: {assessment['ex_nvda_positive']}",
            "",
            "## Top-Outlier Exclusion Sensitivity",
            "",
            f"- Ex-Top-1 Positive: {assessment['ex_top_1_positive']}",
            f"- Ex-Top-2 Positive: {assessment['ex_top_2_positive']}",
            f"- Ex-Top-3 Positive: {assessment['ex_top_3_positive']}",
            "",
            "## Average vs Median Distortion",
            "",
            (
                "- Average Drop Ex-NVDA: "
                f"{_display(assessment['average_drop_ex_nvda'])}"
            ),
            (
                "- Average Materially Lifted by NVDA: "
                f"{assessment['average_materially_lifted_by_nvda']}"
            ),
            f"- Interpretation: {assessment['interpretation']}",
            "",
            "## What This Suggests",
            "",
        ]
    )
    lines.extend(f"- {finding}" for finding in report.key_findings)
    lines.extend(
        [
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
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in report.limitations)
    lines.extend(["", "## Safety Notice", "", report.safety_notice, ""])
    return "\n".join(lines)


def write_outlier_sensitivity_report(
    *,
    output_dir: Path,
    manifest: dict,
    rows: list[dict],
) -> OutlierSensitivityReportFiles:
    """Build and persist outlier sensitivity artifacts."""
    output_dir = Path(output_dir)
    report = build_outlier_sensitivity_report(
        manifest=manifest,
        rows=rows,
    )
    json_path = output_dir / "outlier_sensitivity_report.json"
    markdown_path = output_dir / "outlier_sensitivity_report.md"
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_outlier_sensitivity_report(report),
        encoding="utf-8",
    )
    return OutlierSensitivityReportFiles(
        markdown_path=markdown_path,
        json_path=json_path,
        report=report,
    )
