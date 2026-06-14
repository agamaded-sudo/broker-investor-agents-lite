"""Delayed price-anchor impact diagnostics for readiness-only backtests."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from statistics import mean, median

MATERIAL_RELATIVE_GAP = 0.05
SAFETY_NOTICE = (
    "This delayed anchor impact report is not a recommendation, ranking, "
    "vote, average score, consensus, allocation instruction, rebalancing "
    "instruction, trade signal, execution instruction, or investment advice."
)
SUBSET_FILTERS = {
    "all_records": "All complete readiness trial records.",
    "delayed_anchor": "Delayed price anchor flag is true.",
    "no_delayed_anchor": "Delayed price anchor flag is false.",
    "delayed_anchor_and_warning_heavy": (
        "Delayed price anchor flag is true and guardrail status is "
        "warning_heavy."
    ),
    "no_delayed_anchor_but_limited_financials": (
        "Delayed price anchor flag is false and limited financials is true."
    ),
}


@dataclass(frozen=True)
class DelayedAnchorImpactReport:
    """Structured delayed-anchor impact diagnostics."""

    backtest_run_id: str
    backtest_run_type: str
    total_sample_size: int
    delayed_anchor_present: bool
    subset_diagnostics: dict[str, dict]
    impact_assessment: dict
    key_findings: list[str]
    limitations: list[str]
    impact_status: str
    next_research_action: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready representation."""
        return asdict(self)


@dataclass(frozen=True)
class DelayedAnchorImpactReportFiles:
    """Generated delayed-anchor artifact paths and content."""

    markdown_path: Path
    json_path: Path
    report: DelayedAnchorImpactReport


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _numeric_values(rows: list[dict], field: str) -> list[float]:
    values = []
    for row in rows:
        value = row.get(field)
        if value in {"", None}:
            continue
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            continue
    return values


def _stat(rows: list[dict], field: str, calculator) -> float | None:
    values = _numeric_values(rows, field)
    return round(calculator(values), 6) if values else None


def _rate(rows: list[dict], field: str) -> float | None:
    values = _numeric_values(rows, field)
    if not values:
        return None
    return round(sum(value > 0 for value in values) / len(values), 6)


def summarize_anchor_subset(
    *,
    subset_name: str,
    rows: list[dict],
    total_sample_size: int,
) -> dict:
    """Summarize one anchor subset without fabricating absent metrics."""
    sample_size = len(rows)
    available = sample_size > 0
    interpretation = (
        f"No records are available for {subset_name}."
        if not available
        else (
            f"{subset_name} is available but remains small-sample limited."
            if sample_size < 5
            else f"{subset_name} provides a research-only impact comparison."
        )
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
        "evaluated_dates": sorted(
            {
                str(row.get("signal_date"))
                for row in rows
                if row.get("signal_date")
            }
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


def build_delayed_anchor_impact_diagnostics(
    rows: list[dict],
) -> dict[str, dict]:
    """Build all anchor-focused result subsets."""
    evaluated = [
        row
        for row in rows
        if str(row.get("data_status") or "").startswith("complete")
    ]
    delayed = [
        row
        for row in evaluated
        if _as_bool(row.get("has_delayed_price_anchor"))
    ]
    not_delayed = [
        row
        for row in evaluated
        if not _as_bool(row.get("has_delayed_price_anchor"))
    ]
    subsets = {
        "all_records": evaluated,
        "delayed_anchor": delayed,
        "no_delayed_anchor": not_delayed,
        "delayed_anchor_and_warning_heavy": [
            row
            for row in delayed
            if str(row.get("coverage_guardrail_status") or "")
            == "warning_heavy"
        ],
        "no_delayed_anchor_but_limited_financials": [
            row
            for row in not_delayed
            if _as_bool(row.get("has_limited_financials"))
        ],
    }
    return {
        name: summarize_anchor_subset(
            subset_name=name,
            rows=subset,
            total_sample_size=len(evaluated),
        )
        for name, subset in subsets.items()
    }


def compare_delayed_vs_non_delayed(subsets: dict[str, dict]) -> dict:
    """Assess delayed-anchor impact using conservative thresholds."""
    delayed = subsets["delayed_anchor"]
    not_delayed = subsets["no_delayed_anchor"]
    delayed_relative = delayed.get("median_relative_return_12m")
    not_delayed_relative = not_delayed.get("median_relative_return_12m")
    delayed_absolute = delayed.get("median_forward_return_12m")
    not_delayed_absolute = not_delayed.get("median_forward_return_12m")
    relative_gap = (
        round(float(delayed_relative) - float(not_delayed_relative), 6)
        if delayed_relative is not None and not_delayed_relative is not None
        else None
    )
    absolute_gap = (
        round(float(delayed_absolute) - float(not_delayed_absolute), 6)
        if delayed_absolute is not None and not_delayed_absolute is not None
        else None
    )
    delayed_stronger = (
        relative_gap is not None and relative_gap >= MATERIAL_RELATIVE_GAP
    )
    no_delayed_positive = (
        not_delayed_relative is not None
        and float(not_delayed_relative) > 0
        and not_delayed.get("hit_rate_vs_benchmark_12m") is not None
        and float(not_delayed["hit_rate_vs_benchmark_12m"]) >= 0.5
    )
    if not not_delayed["available"]:
        status = "no_delayed_anchor_data"
    elif not delayed["available"]:
        status = "delayed_anchor_not_present"
    elif delayed["sample_size"] < 5 or not_delayed["sample_size"] < 5:
        status = "insufficient_sample"
    elif delayed_stronger:
        status = "delayed_anchor_may_be_lifting_results"
    elif no_delayed_positive:
        status = "delayed_anchor_present_non_delayed_positive"
    else:
        status = "delayed_anchor_present_no_delayed_positive"
    if delayed_stronger and no_delayed_positive:
        interpretation = (
            "Delayed-anchor records appear stronger and may be lifting "
            "aggregate results, but non-delayed-anchor records remain "
            "positive. Interpretation remains research-only because "
            "non-delayed records may still include limited financial warnings."
        )
    elif delayed_stronger:
        interpretation = (
            "Delayed-anchor records appear materially stronger while "
            "non-delayed evidence is not positive; additional caution is "
            "required."
        )
    elif no_delayed_positive:
        interpretation = (
            "Non-delayed-anchor records remain positive and delayed-anchor "
            "records do not appear materially stronger at the selected "
            "threshold."
        )
    else:
        interpretation = (
            "The anchor subsets do not provide positive non-delayed evidence "
            "or a material delayed-anchor gap."
        )
    return {
        "delayed_anchor_present": delayed["available"],
        "delayed_anchor_sample_size": delayed["sample_size"],
        "no_delayed_anchor_sample_size": not_delayed["sample_size"],
        "delayed_anchor_median_relative_12m": delayed_relative,
        "no_delayed_anchor_median_relative_12m": not_delayed_relative,
        "delayed_anchor_hit_rate_12m": delayed.get(
            "hit_rate_vs_benchmark_12m"
        ),
        "no_delayed_anchor_hit_rate_12m": not_delayed.get(
            "hit_rate_vs_benchmark_12m"
        ),
        "relative_median_gap_12m": relative_gap,
        "absolute_median_gap_12m": absolute_gap,
        "delayed_anchor_materially_stronger": delayed_stronger,
        "no_delayed_anchor_positive": no_delayed_positive,
        "impact_status": status,
        "interpretation": interpretation,
    }


def build_delayed_anchor_impact_report(
    *,
    manifest: dict,
    rows: list[dict],
) -> DelayedAnchorImpactReport:
    """Build delayed-anchor impact diagnostics for one readiness trial."""
    if manifest.get("backtest_run_type") != "readiness_trial":
        raise ValueError(
            "Delayed anchor impact requires a readiness_trial run."
        )
    subsets = build_delayed_anchor_impact_diagnostics(rows)
    assessment = compare_delayed_vs_non_delayed(subsets)
    findings = [assessment["interpretation"]]
    clean_available = bool(manifest.get("clean_only_available"))
    if not clean_available:
        findings.append(
            "Clean-only evidence is unavailable, so neither anchor subset "
            "should be treated as clean historical evidence."
        )
    if subsets["no_delayed_anchor_but_limited_financials"]["available"]:
        findings.append(
            "Non-delayed-anchor rows still carry limited financial coverage "
            "warnings."
        )
    next_action = (
        "build_clean_anchor_price_fixture_coverage"
        if assessment["delayed_anchor_present"]
        else "add_clean_historical_fixture_coverage"
    )
    return DelayedAnchorImpactReport(
        backtest_run_id=str(manifest.get("backtest_run_id") or ""),
        backtest_run_type="readiness_trial",
        total_sample_size=subsets["all_records"]["sample_size"],
        delayed_anchor_present=assessment["delayed_anchor_present"],
        subset_diagnostics=subsets,
        impact_assessment=assessment,
        key_findings=findings,
        limitations=[
            "Anchor subsets may differ by date and ticker composition.",
            "Delayed anchors describe data timing, not exact execution.",
            "Non-delayed records may retain other coverage warnings.",
            "Subset associations do not establish causal relationships.",
        ],
        impact_status=assessment["impact_status"],
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


def render_delayed_anchor_impact_report(
    report: DelayedAnchorImpactReport,
) -> str:
    """Render the standalone delayed-anchor impact report."""
    delayed = report.subset_diagnostics["delayed_anchor"]
    not_delayed = report.subset_diagnostics["no_delayed_anchor"]
    assessment = report.impact_assessment
    lines = [
        "# Delayed Anchor Impact Report",
        "",
        "## Executive Summary",
        "",
        f"- Impact Status: {report.impact_status}",
        f"- Total Sample Size: {report.total_sample_size}",
        f"- Delayed Anchor Records: {delayed['sample_size']}",
        f"- No-Delayed-Anchor Records: {not_delayed['sample_size']}",
        f"- Main Finding: {report.key_findings[0]}",
        "",
        "## Anchor Subset Comparison",
        "",
        (
            "| Subset | Sample | Share | Median 12M | Median Relative 12M | "
            "Hit Rate 12M | Worst Drawdown | Available | Interpretation |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for subset in report.subset_diagnostics.values():
        lines.append(
            f"| {subset['subset_name']} | {subset['sample_size']} | "
            f"{_display(subset['share_of_total'])} | "
            f"{_display(subset['median_forward_return_12m'])} | "
            f"{_display(subset['median_relative_return_12m'])} | "
            f"{_display(subset['hit_rate_vs_benchmark_12m'])} | "
            f"{_display(subset['worst_max_drawdown_12m'])} | "
            f"{_display(subset['available'])} | "
            f"{subset['interpretation']} |"
        )
    lines.extend(
        [
            "",
            "## Delayed vs Non-Delayed Impact Assessment",
            "",
            (
                "- Absolute Median 12M Gap: "
                f"{_display(assessment['absolute_median_gap_12m'])}"
            ),
            (
                "- Relative Median 12M Gap: "
                f"{_display(assessment['relative_median_gap_12m'])}"
            ),
            (
                "- Delayed Anchor Materially Stronger: "
                f"{assessment['delayed_anchor_materially_stronger']}"
            ),
            (
                "- No-Delayed-Anchor Positive: "
                f"{assessment['no_delayed_anchor_positive']}"
            ),
            f"- Interpretation: {assessment['interpretation']}",
            "",
            "## Non-Delayed Anchor Evidence",
            "",
            f"- Sample Size: {not_delayed['sample_size']}",
            (
                "- Non-delayed records may remain positive while still "
                "carrying limited financial coverage warnings."
            ),
            "",
            "## Delayed Anchor Caution",
            "",
            (
                "Delayed anchors describe data timing and do not simulate "
                "exact historical execution."
            ),
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


def write_delayed_anchor_impact_report(
    *,
    output_dir: Path,
    manifest: dict,
    rows: list[dict],
) -> DelayedAnchorImpactReportFiles:
    """Build and persist delayed-anchor impact artifacts."""
    output_dir = Path(output_dir)
    report = build_delayed_anchor_impact_report(
        manifest=manifest,
        rows=rows,
    )
    json_path = output_dir / "delayed_anchor_impact_report.json"
    markdown_path = output_dir / "delayed_anchor_impact_report.md"
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_delayed_anchor_impact_report(report),
        encoding="utf-8",
    )
    return DelayedAnchorImpactReportFiles(
        markdown_path=markdown_path,
        json_path=json_path,
        report=report,
    )
