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
        if not any(str(row.get(field) or "").strip() for row in rows)
    ]


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


def render_readiness_trial_diagnostic_report(
    report: ReadinessTrialDiagnosticReport,
) -> str:
    """Render the standalone readiness trial diagnostic report."""
    if report.diagnostic_status == "insufficient_data":
        main_finding = (
            "The readiness trial has insufficient data for a reliable "
            "diagnostic interpretation."
        )
    elif report.diagnostic_status == "unstable_needs_deeper_review":
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
            "Missing grouped metadata fields:",
            "",
        ]
    )
    lines.extend(
        f"- {field}" for field in report.missing_metadata_fields
    )
    lines.extend(
        [
            "",
            (
                "Missing metadata prevents grouped attribution by readiness "
                "quality or investor agent interest."
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
                "- Metadata enrichment is needed to explain why cases "
                "performed differently."
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
            "- Enrich readiness metadata fields.",
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
