"""Coverage-quality sensitivity diagnostics for readiness-only backtests."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from statistics import mean, median

SAFETY_NOTICE = (
    "This clean-coverage sensitivity report is not a recommendation, ranking, "
    "vote, average score, consensus, allocation instruction, rebalancing "
    "instruction, trade signal, execution instruction, or investment advice."
)
SUBSET_FILTERS = {
    "all_records": "All complete readiness trial records.",
    "clean_records": "Coverage guardrail status or quality label is clean.",
    "research_usable_with_warnings": (
        "Coverage guardrail status is research_usable_with_warnings."
    ),
    "warning_heavy": "Coverage guardrail status is warning_heavy.",
    "no_delayed_anchor": "Delayed price anchor flag is false.",
    "delayed_anchor": "Delayed price anchor flag is true.",
    "limited_financials": "Limited financials flag is true.",
    "non_warning_heavy": (
        "Coverage guardrail status is not warning_heavy."
    ),
}


@dataclass(frozen=True)
class CleanCoverageSensitivityReport:
    """Structured quality-subset sensitivity diagnostics."""

    backtest_run_id: str
    backtest_run_type: str
    total_sample_size: int
    coverage_quality_detected: bool
    subset_diagnostics: dict[str, dict]
    key_findings: list[str]
    limitations: list[str]
    sensitivity_status: str
    next_research_action: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class CleanCoverageSensitivityReportFiles:
    """Generated sensitivity artifact paths and content."""

    markdown_path: Path
    json_path: Path
    report: CleanCoverageSensitivityReport


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _numeric_values(rows: list[dict], field: str) -> list[float]:
    values = []
    for row in rows:
        try:
            if row.get(field) not in {"", None}:
                values.append(float(row[field]))
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


def summarize_sensitivity_subset(
    *,
    subset_name: str,
    rows: list[dict],
    total_sample_size: int,
) -> dict:
    """Summarize one quality subset without fabricating absent metrics."""
    sample_size = len(rows)
    available = sample_size > 0
    if not available:
        interpretation = (
            "Clean-only sensitivity is not available yet."
            if subset_name == "clean_records"
            else f"No records are available for {subset_name}."
        )
    elif sample_size < 5:
        interpretation = (
            f"{subset_name} is available but remains small-sample limited."
        )
    else:
        interpretation = (
            f"{subset_name} provides a research-only subset comparison."
        )
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
            {str(row.get("ticker") or "") for row in rows if row.get("ticker")}
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
            round(min(_numeric_values(rows, "max_drawdown_12m")), 6)
            if _numeric_values(rows, "max_drawdown_12m")
            else None
        ),
        "small_sample_warning": sample_size < 5,
        "available": available,
        "interpretation": interpretation,
    }


def build_coverage_sensitivity_diagnostics(rows: list[dict]) -> dict[str, dict]:
    """Build every requested coverage-quality subset."""
    evaluated = [
        row
        for row in rows
        if str(row.get("data_status") or "").startswith("complete")
    ]
    subsets = {
        "all_records": evaluated,
        "clean_records": [
            row
            for row in evaluated
            if str(row.get("coverage_guardrail_status") or "") == "clean"
            or str(row.get("coverage_quality_label") or "") == "clean"
        ],
        "research_usable_with_warnings": [
            row
            for row in evaluated
            if str(row.get("coverage_guardrail_status") or "")
            == "research_usable_with_warnings"
        ],
        "warning_heavy": [
            row
            for row in evaluated
            if str(row.get("coverage_guardrail_status") or "")
            == "warning_heavy"
        ],
        "no_delayed_anchor": [
            row
            for row in evaluated
            if not _as_bool(row.get("has_delayed_price_anchor"))
        ],
        "delayed_anchor": [
            row
            for row in evaluated
            if _as_bool(row.get("has_delayed_price_anchor"))
        ],
        "limited_financials": [
            row
            for row in evaluated
            if _as_bool(row.get("has_limited_financials"))
        ],
        "non_warning_heavy": [
            row
            for row in evaluated
            if str(row.get("coverage_guardrail_status") or "")
            != "warning_heavy"
        ],
    }
    return {
        name: summarize_sensitivity_subset(
            subset_name=name,
            rows=subset,
            total_sample_size=len(evaluated),
        )
        for name, subset in subsets.items()
    }


def _materially_stronger(first: dict, second: dict) -> bool:
    first_value = first.get("median_forward_return_12m")
    second_value = second.get("median_forward_return_12m")
    return (
        first_value is not None
        and second_value is not None
        and float(first_value) - float(second_value) >= 0.15
    )


def build_clean_coverage_sensitivity_report(
    *,
    manifest: dict,
    rows: list[dict],
) -> CleanCoverageSensitivityReport:
    """Build a conservative sensitivity report from result rows."""
    if manifest.get("backtest_run_type") != "readiness_trial":
        raise ValueError(
            "Clean-coverage sensitivity requires a readiness_trial run."
        )
    subsets = build_coverage_sensitivity_diagnostics(rows)
    all_records = subsets["all_records"]
    clean = subsets["clean_records"]
    warning_heavy = subsets["warning_heavy"]
    non_warning = subsets["non_warning_heavy"]
    no_delayed = subsets["no_delayed_anchor"]
    delayed = subsets["delayed_anchor"]
    quality_detected = any(
        str(row.get("coverage_quality_label") or "")
        not in {"", "not_available", "Missing"}
        for row in rows
    )
    all_positive = (
        all_records["median_forward_return_12m"] is not None
        and all_records["median_forward_return_12m"] > 0
        and all_records["median_relative_return_12m"] is not None
        and all_records["median_relative_return_12m"] > 0
    )
    findings = []
    if not quality_detected:
        status = "insufficient_coverage_metadata"
        next_action = "add_clean_historical_fixture_coverage"
        findings.append(
            "Coverage quality metadata is insufficient for sensitivity review."
        )
    elif not clean["available"]:
        status = "clean_not_available"
        next_action = "add_clean_historical_fixture_coverage"
        findings.append("Clean-only interpretation is not available yet.")
        if all_positive:
            findings.append(
                "The current promising result is based on warning-bearing "
                "records, not clean historical evidence."
            )
    elif clean["sample_size"] < 5:
        status = "clean_sample_too_small"
        next_action = "add_clean_historical_fixture_coverage"
        findings.append(
            "Clean-only sensitivity is available but remains small-sample "
            "limited."
        )
    elif all_positive and (
        clean["median_forward_return_12m"] is not None
        and clean["median_forward_return_12m"] > 0
        and clean["median_relative_return_12m"] is not None
        and clean["median_relative_return_12m"] > 0
    ):
        status = "clean_supported_preliminary"
        next_action = "expand_ticker_universe_with_coverage_validation"
        findings.append(
            "Clean records are available for preliminary comparison, while "
            "the evidence remains diagnostic."
        )
    else:
        status = "mixed_evidence"
        next_action = "expand_ticker_universe_with_coverage_validation"
        findings.append(
            "Coverage subsets show mixed evidence and require broader review."
        )
    if _materially_stronger(warning_heavy, non_warning):
        findings.append(
            "Warning-heavy records appear stronger in this sample; this may "
            "reflect cohort or date composition and is not higher-quality "
            "evidence."
        )
    if no_delayed["available"] and (
        no_delayed["median_forward_return_12m"] or 0
    ) > 0:
        if subsets["limited_financials"]["available"]:
            findings.append(
                "Non-delayed-anchor records remain positive in this sample, "
                "but some coverage still includes limited financial warnings."
            )
        else:
            findings.append(
                "Non-delayed-anchor records remain positive and the current "
                "evaluated sample has no limited-financials records."
            )
    if _materially_stronger(delayed, no_delayed):
        findings.append(
            "Delayed-anchor records may be contributing to the stronger "
            "aggregate result; interpret cautiously."
        )
    return CleanCoverageSensitivityReport(
        backtest_run_id=str(manifest.get("backtest_run_id") or ""),
        backtest_run_type="readiness_trial",
        total_sample_size=all_records["sample_size"],
        coverage_quality_detected=quality_detected,
        subset_diagnostics=subsets,
        key_findings=findings,
        limitations=[
            "Subsets may differ by date and ticker composition.",
            "Small subsets are not decision-grade.",
            "Warning records are not automatically excluded.",
            "Coverage associations do not establish causal relationships.",
        ],
        sensitivity_status=status,
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


def render_clean_coverage_sensitivity_report(
    report: CleanCoverageSensitivityReport,
) -> str:
    """Render the standalone sensitivity report."""
    subsets = report.subset_diagnostics
    clean = subsets["clean_records"]
    warning_heavy = subsets["warning_heavy"]
    non_warning = subsets["non_warning_heavy"]
    delayed = subsets["delayed_anchor"]
    no_delayed = subsets["no_delayed_anchor"]
    limited = subsets["limited_financials"]
    lines = [
        "# Clean-Coverage Sensitivity Report",
        "",
        "## Executive Summary",
        "",
        f"- Sensitivity Status: {report.sensitivity_status}",
        f"- Total Sample Size: {report.total_sample_size}",
        f"- Clean Records: {clean['sample_size']}",
        (
            "- Warning Records: "
            f"{subsets['research_usable_with_warnings']['sample_size'] + warning_heavy['sample_size']}"
        ),
        f"- Warning-Heavy Records: {warning_heavy['sample_size']}",
        f"- Main Finding: {report.key_findings[0]}",
        "",
        "## Subset Comparison",
        "",
        (
            "| Subset | Sample | Share | Median 12M | Median Relative 12M | "
            "Hit Rate 12M | Worst Drawdown | Available | Interpretation |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for subset in subsets.values():
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
            "## Clean-Only Sensitivity",
            "",
            clean["interpretation"],
            "",
            "## Warning-Heavy Sensitivity",
            "",
            (
                f"- Warning-Heavy Sample: {warning_heavy['sample_size']}"
            ),
            f"- Non-Warning-Heavy Sample: {non_warning['sample_size']}",
            (
                "- Comparison remains sensitive to cohort and date "
                "composition."
            ),
            "",
            "## Delayed Anchor Sensitivity",
            "",
            f"- Delayed Anchor Sample: {delayed['sample_size']}",
            f"- No Delayed Anchor Sample: {no_delayed['sample_size']}",
            (
                "- Delayed anchor differences describe data timing, not an "
                "entry rule."
            ),
            "",
            "## Limited Financials Sensitivity",
            "",
            f"- Limited Financials Sample: {limited['sample_size']}",
            f"- Interpretation: {limited['interpretation']}",
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


def write_clean_coverage_sensitivity_report(
    *,
    output_dir: Path,
    manifest: dict,
    rows: list[dict],
) -> CleanCoverageSensitivityReportFiles:
    """Build and persist clean-coverage sensitivity artifacts."""
    output_dir = Path(output_dir)
    report = build_clean_coverage_sensitivity_report(
        manifest=manifest,
        rows=rows,
    )
    json_path = output_dir / "clean_coverage_sensitivity_report.json"
    markdown_path = output_dir / "clean_coverage_sensitivity_report.md"
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_clean_coverage_sensitivity_report(report),
        encoding="utf-8",
    )
    return CleanCoverageSensitivityReportFiles(
        markdown_path=markdown_path,
        json_path=json_path,
        report=report,
    )
