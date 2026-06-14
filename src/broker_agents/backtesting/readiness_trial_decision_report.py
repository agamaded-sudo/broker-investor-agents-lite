"""Conservative interpretation of readiness-only trial backtests."""

import csv
from dataclasses import asdict, dataclass
import json
from pathlib import Path

MISSING_METADATA_FIELDS = (
    "readiness_label",
    "source_verification_status",
    "buffett_interest_level",
    "munger_interest_level",
    "fisher_interest_level",
    "lynch_interest_level",
    "bogle_interest_level",
)
SAFETY_NOTICE = (
    "This readiness trial decision report is not a recommendation, ranking, "
    "vote, average score, consensus, allocation instruction, rebalancing "
    "instruction, trade signal, execution instruction, or investment advice."
)


@dataclass(frozen=True)
class ReadinessTrialDecisionReport:
    """Structured judgment about readiness trial data quality."""

    backtest_run_id: str
    backtest_run_type: str
    ledger_path: str
    sample_size: int
    records_before_dedupe: int
    records_after_dedupe: int
    duplicate_records_removed: int
    evaluated_records: int
    skipped_records: int
    concentration_warning: bool
    small_sample_warning: bool
    synthetic_data_warning: bool
    tickers_evaluated: list[str]
    missing_metadata_fields: list[str]
    statistical_validity: str
    decision_status: str
    interpretation: str
    what_this_means: list[str]
    what_this_does_not_mean: list[str]
    next_required_action: str
    warnings: list[str]
    results_snapshot: dict
    walk_forward_enabled: bool
    walk_forward_periods_evaluated: int
    walk_forward_stability_judgment: str
    best_period: str | None
    weakest_period: str | None
    period_summaries: list[dict]
    coverage_guardrail_status_counts: dict[str, int]
    clean_record_count: int
    warning_record_count: int
    warning_heavy_record_count: int
    coverage_interpretation: str
    clean_coverage_sensitivity_status: str
    clean_only_available: bool
    clean_coverage_sensitivity_interpretation: str
    delayed_anchor_impact_status: str
    delayed_anchor_materially_stronger: bool
    no_delayed_anchor_positive: bool
    delayed_anchor_impact_interpretation: str
    outlier_sensitivity_status: str
    ex_nvda_positive: bool
    ex_top_2_positive: bool
    outlier_sensitivity_interpretation: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready representation."""
        return asdict(self)


@dataclass(frozen=True)
class ReadinessTrialDecisionReportFiles:
    """Paths and structured content for generated decision reports."""

    markdown_path: Path
    json_path: Path
    report: ReadinessTrialDecisionReport


def _missing_metadata(rows: list[dict]) -> list[str]:
    """Return grouping fields with no populated values."""
    return [
        field
        for field in MISSING_METADATA_FIELDS
        if not any(
            str(row.get(field) or "").strip().lower()
            not in {"", "missing", "null", "none"}
            for row in rows
        )
    ]


def _display_metric(value: object) -> str:
    """Format diagnostic metrics without implying precision."""
    if value is None or value == "":
        return "Missing"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _walk_forward_metrics(manifest: dict) -> dict:
    """Load optional walk-forward metrics from the completed run."""
    path_value = manifest.get("walk_forward_metrics_path")
    if not manifest.get("walk_forward_enabled") or not path_value:
        return {}
    path = Path(path_value)
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _coverage_sensitivity(manifest: dict) -> dict:
    """Load optional clean-coverage sensitivity diagnostics."""
    path_value = manifest.get(
        "clean_coverage_sensitivity_report_json_path"
    )
    if not path_value or not Path(path_value).is_file():
        return {}
    return json.loads(Path(path_value).read_text(encoding="utf-8"))


def _delayed_anchor_impact(manifest: dict) -> dict:
    """Load optional delayed-anchor impact diagnostics."""
    path_value = manifest.get("delayed_anchor_impact_report_json_path")
    if not path_value or not Path(path_value).is_file():
        return {}
    return json.loads(Path(path_value).read_text(encoding="utf-8"))


def _outlier_sensitivity(manifest: dict) -> dict:
    """Load optional outlier sensitivity diagnostics."""
    path_value = manifest.get("outlier_sensitivity_report_json_path")
    if not path_value or not Path(path_value).is_file():
        return {}
    return json.loads(Path(path_value).read_text(encoding="utf-8"))


def _walk_forward_stability(periods: list[dict]) -> str:
    """Judge period stability conservatively without strategy claims."""
    valid = [
        period
        for period in periods
        if period.get("median_relative_return_12m") is not None
    ]
    if len(valid) < 3:
        return "insufficient_periods"
    relative = [
        float(period["median_relative_return_12m"]) for period in valid
    ]
    forward = [
        float(period["median_forward_return_12m"])
        for period in valid
        if period.get("median_forward_return_12m") is not None
    ]
    hit_rates = [
        float(period["hit_rate_vs_benchmark_12m"])
        for period in valid
        if period.get("hit_rate_vs_benchmark_12m") is not None
    ]
    concentrated = any(
        bool(period.get("concentration_warning")) for period in valid
    )
    sign_disagreement = (
        any(value < 0 for value in relative)
        and any(value > 0 for value in relative)
    ) or (
        any(value < 0 for value in forward)
        and any(value > 0 for value in forward)
    )
    material_hit_rate_variation = (
        len(hit_rates) > 1 and max(hit_rates) - min(hit_rates) >= 0.50
    )
    if sign_disagreement:
        return "unstable"
    if concentrated or material_hit_rate_variation:
        return "mixed"
    if all(value > 0 for value in relative):
        return "stable_positive"
    if all(value < 0 for value in relative):
        return "stable_negative"
    return "mixed"


def build_readiness_trial_decision_report(
    *,
    manifest: dict,
    metrics: dict,
    rows: list[dict],
) -> ReadinessTrialDecisionReport:
    """Build a conservative decision report from readiness trial artifacts."""
    if manifest.get("backtest_run_type") != "readiness_trial":
        raise ValueError(
            "Readiness trial decision reports require a readiness_trial run."
        )

    sample_size = int(metrics.get("sample_size") or 0)
    tickers = [
        str(ticker)
        for ticker in metrics.get("evaluated_tickers", [])
        if str(ticker)
    ]
    duplicate_records_removed = int(
        manifest.get("duplicate_records_removed") or 0
    )
    concentration_warning = bool(metrics.get("concentration_warning"))
    missing_metadata_fields = _missing_metadata(rows)
    warnings = []

    if sample_size < 5:
        warnings.append("Sample size is too small for inference.")
    if concentration_warning:
        warnings.append(
            "Results are concentrated and not diversified across tickers or "
            "categories."
        )
    if duplicate_records_removed:
        warnings.append(
            "Dedupe removed repeated runs; this prevents run-inflation but "
            "reduces evaluated sample."
        )
    if len(tickers) == 1:
        warnings.append(
            "Single-ticker result cannot validate a repeatable process."
        )
    if missing_metadata_fields:
        warnings.append("Missing metadata limits grouped analysis.")
    warnings.append(
        "This evaluates readiness-only artifacts, not investment signals."
    )
    guardrail_counts = dict(
        metrics.get("coverage_guardrail_status_counts") or {}
    )
    clean_record_count = int(metrics.get("clean_record_count") or 0)
    warning_record_count = int(metrics.get("warning_record_count") or 0)
    warning_heavy_record_count = int(
        metrics.get("warning_heavy_record_count") or 0
    )
    if warning_heavy_record_count:
        warnings.append(
            "Warning-heavy coverage records require additional caution."
        )
        coverage_interpretation = (
            "Warning-heavy records are present; coverage quality limits "
            "interpretation."
        )
    elif warning_record_count:
        coverage_interpretation = (
            "Usable records include coverage warnings that remain visible "
            "in grouped diagnostics."
        )
    elif clean_record_count:
        coverage_interpretation = (
            "Evaluated records are classified as clean, while the trial "
            "remains diagnostic."
        )
    else:
        coverage_interpretation = (
            "Coverage guardrail metadata is not available for this older "
            "trial input."
        )
    sensitivity = _coverage_sensitivity(manifest)
    clean_subset = sensitivity.get("subset_diagnostics", {}).get(
        "clean_records",
        {},
    )
    sensitivity_status = str(
        sensitivity.get("sensitivity_status") or "not_available"
    )
    sensitivity_interpretation = (
        next(iter(sensitivity.get("key_findings") or []), "")
        or "Clean-coverage sensitivity is not available for this run."
    )
    anchor_impact = _delayed_anchor_impact(manifest)
    impact_assessment = anchor_impact.get("impact_assessment", {})
    anchor_materially_stronger = bool(
        impact_assessment.get("delayed_anchor_materially_stronger")
    )
    anchor_interpretation = str(
        impact_assessment.get("interpretation")
        or "Delayed-anchor impact is not available for this run."
    )
    outlier_sensitivity = _outlier_sensitivity(manifest)
    outlier_assessment = outlier_sensitivity.get(
        "outlier_impact_assessment",
        {},
    )
    outlier_status = str(
        outlier_sensitivity.get("outlier_dependence_status")
        or "not_available"
    )
    outlier_interpretation = str(
        outlier_assessment.get("interpretation")
        or "Outlier sensitivity is not available for this run."
    )
    outlier_dependence = outlier_status in {
        "result_sensitive_to_nvda",
        "result_sensitive_to_top_outliers",
        "nvda_lifts_average_but_result_survives",
        "insufficient_sample",
    }

    if sample_size < 5:
        statistical_validity = "insufficient_sample"
        decision_status = "not_decision_grade"
        next_required_action = "expand_sample_before_interpretation"
    elif (
        concentration_warning
        or missing_metadata_fields
        or warning_heavy_record_count >= max(1, sample_size // 2)
        or sensitivity_status == "clean_not_available"
        or anchor_materially_stronger
        or outlier_dependence
    ):
        statistical_validity = "limited_sample"
        decision_status = "needs_more_samples"
        next_required_action = "expand_sample_before_interpretation"
    else:
        statistical_validity = "diagnostic_only"
        decision_status = "ready_for_broader_trial"
        next_required_action = "run_broader_readiness_trial"

    interpretation = (
        f"The backtest evaluated {sample_size} record"
        f"{'' if sample_size == 1 else 's'} after dedupe. "
        "The result validates the research pipeline, but the available sample "
        "does not support performance inference."
    )
    results_snapshot = {
        "median_forward_return_3m": metrics.get(
            "median_forward_return_3m"
        ),
        "median_forward_return_6m": metrics.get(
            "median_forward_return_6m"
        ),
        "median_forward_return_12m": metrics.get(
            "median_forward_return_12m"
        ),
        "median_relative_return_12m": metrics.get(
            "median_relative_return_12m"
        ),
        "hit_rate_vs_benchmark_12m": metrics.get(
            "hit_rate_vs_benchmark_12m"
        ),
    }
    walk_forward_metrics = _walk_forward_metrics(manifest)
    period_summaries = list(walk_forward_metrics.get("periods") or [])
    periods_with_relative = [
        period
        for period in period_summaries
        if period.get("median_relative_return_12m") is not None
    ]
    best_period = (
        str(
            max(
                periods_with_relative,
                key=lambda period: float(
                    period["median_relative_return_12m"]
                ),
            )["period"]
        )
        if periods_with_relative
        else None
    )
    weakest_period = (
        str(
            min(
                periods_with_relative,
                key=lambda period: float(
                    period["median_relative_return_12m"]
                ),
            )["period"]
        )
        if periods_with_relative
        else None
    )
    walk_forward_enabled = bool(
        manifest.get("walk_forward_enabled") and period_summaries
    )
    walk_forward_stability = (
        _walk_forward_stability(period_summaries)
        if walk_forward_enabled
        else "not_enabled"
    )
    return ReadinessTrialDecisionReport(
        backtest_run_id=str(manifest.get("backtest_run_id") or ""),
        backtest_run_type="readiness_trial",
        ledger_path=str(manifest.get("ledger_path") or ""),
        sample_size=sample_size,
        records_before_dedupe=int(
            manifest.get("total_records_before_dedupe") or 0
        ),
        records_after_dedupe=int(
            manifest.get("evaluated_records_after_dedupe") or 0
        ),
        duplicate_records_removed=duplicate_records_removed,
        evaluated_records=int(manifest.get("evaluated_records") or 0),
        skipped_records=int(manifest.get("skipped_records") or 0),
        concentration_warning=concentration_warning,
        small_sample_warning=bool(metrics.get("small_sample_warning")),
        synthetic_data_warning=bool(metrics.get("synthetic_data_warning")),
        tickers_evaluated=tickers,
        missing_metadata_fields=missing_metadata_fields,
        statistical_validity=statistical_validity,
        decision_status=decision_status,
        interpretation=interpretation,
        what_this_means=[
            "The pipeline works end-to-end.",
            "The readiness trial backtest successfully produced outputs.",
            (
                "The current result is useful for validating infrastructure, "
                "not performance."
            ),
        ],
        what_this_does_not_mean=[
            "It does not prove a strategy.",
            "It does not validate investor agent performance.",
            "It does not produce a recommendation.",
            "It does not produce a trade signal.",
        ],
        next_required_action=next_required_action,
        warnings=warnings,
        results_snapshot=results_snapshot,
        walk_forward_enabled=walk_forward_enabled,
        walk_forward_periods_evaluated=len(period_summaries),
        walk_forward_stability_judgment=walk_forward_stability,
        best_period=best_period,
        weakest_period=weakest_period,
        period_summaries=period_summaries,
        coverage_guardrail_status_counts=guardrail_counts,
        clean_record_count=clean_record_count,
        warning_record_count=warning_record_count,
        warning_heavy_record_count=warning_heavy_record_count,
        coverage_interpretation=coverage_interpretation,
        clean_coverage_sensitivity_status=str(
            sensitivity_status
        ),
        clean_only_available=bool(clean_subset.get("available")),
        clean_coverage_sensitivity_interpretation=(
            sensitivity_interpretation
        ),
        delayed_anchor_impact_status=str(
            anchor_impact.get("impact_status") or "not_available"
        ),
        delayed_anchor_materially_stronger=anchor_materially_stronger,
        no_delayed_anchor_positive=bool(
            impact_assessment.get("no_delayed_anchor_positive")
        ),
        delayed_anchor_impact_interpretation=anchor_interpretation,
        outlier_sensitivity_status=outlier_status,
        ex_nvda_positive=bool(
            outlier_assessment.get("ex_nvda_positive")
        ),
        ex_top_2_positive=bool(
            outlier_assessment.get("ex_top_2_positive")
        ),
        outlier_sensitivity_interpretation=outlier_interpretation,
    )


def render_readiness_trial_decision_report(
    report: ReadinessTrialDecisionReport,
    *,
    price_provider: str,
) -> str:
    """Render a human-readable readiness trial decision report."""
    dedupe_interpretation = (
        "Dedupe removed repeated runs; this prevents run-inflation but "
        "reduces evaluated sample."
        if report.duplicate_records_removed
        else "No repeated records were removed by the selected dedupe mode."
    )
    lines = [
        "# Readiness Trial Backtest Decision Report",
        "",
        "## Executive Decision",
        "",
        f"- Decision Status: {report.decision_status}",
        f"- Statistical Validity: {report.statistical_validity}",
        (
            f"- Reason: Sample size is {report.sample_size} after dedupe"
            + (
                " and results are concentrated."
                if report.concentration_warning
                else "."
            )
        ),
        "",
        "## Technical Status",
        "",
        "- Backtest Completed: Yes",
        f"- Backtest Run Type: {report.backtest_run_type}",
        f"- Evaluated Records: {report.evaluated_records}",
        f"- Skipped Records: {report.skipped_records}",
        f"- Price Provider: {price_provider}",
        f"- Synthetic Data Warning: {report.synthetic_data_warning}",
        "",
        "## Statistical Validity",
        "",
        f"- Sample Size: {report.sample_size}",
        f"- Small Sample Warning: {report.small_sample_warning}",
        f"- Concentration Warning: {report.concentration_warning}",
        (
            "- Tickers Evaluated: "
            + (", ".join(report.tickers_evaluated) or "None")
        ),
        f"- Validity Judgment: {report.statistical_validity}",
        "",
    ]
    lines.extend(f"- Warning: {warning}" for warning in report.warnings)
    lines.extend(
        [
            "",
            "## Dedupe Impact",
            "",
            f"- Records Before Dedupe: {report.records_before_dedupe}",
            f"- Records After Dedupe: {report.records_after_dedupe}",
            (
                "- Duplicate Records Removed: "
                f"{report.duplicate_records_removed}"
            ),
            f"- Interpretation: {dedupe_interpretation}",
            "",
            "## Results Snapshot",
            "",
            "| Diagnostic Metric | Value |",
            "|---|---:|",
            (
                "| Median 3M Return | "
                f"{_display_metric(report.results_snapshot['median_forward_return_3m'])} |"
            ),
            (
                "| Median 6M Return | "
                f"{_display_metric(report.results_snapshot['median_forward_return_6m'])} |"
            ),
            (
                "| Median 12M Return | "
                f"{_display_metric(report.results_snapshot['median_forward_return_12m'])} |"
            ),
            (
                "| Median Relative 12M Return | "
                f"{_display_metric(report.results_snapshot['median_relative_return_12m'])} |"
            ),
            (
                "| Hit Rate vs Benchmark 12M | "
                f"{_display_metric(report.results_snapshot['hit_rate_vs_benchmark_12m'])} |"
            ),
            "",
            "These metrics are diagnostic only and are not decision-grade.",
            "",
            "## Missing Metadata",
            "",
        ]
    )
    if report.missing_metadata_fields:
        lines.extend(
            f"- {field}" for field in report.missing_metadata_fields
        )
    else:
        lines.append("- No required grouped metadata fields are wholly missing.")
    lines.extend(
        [
            "",
            "## Coverage Quality",
            "",
            (
                "- Coverage Guardrail Status Counts: "
                f"{report.coverage_guardrail_status_counts}"
            ),
            f"- Clean Record Count: {report.clean_record_count}",
            f"- Warning Record Count: {report.warning_record_count}",
            (
                "- Warning-Heavy Record Count: "
                f"{report.warning_heavy_record_count}"
            ),
            f"- Coverage Interpretation: {report.coverage_interpretation}",
            (
                "- Clean-Coverage Sensitivity Status: "
                f"{report.clean_coverage_sensitivity_status}"
            ),
            (
                "- Clean-Only Available: "
                f"{'Yes' if report.clean_only_available else 'No'}"
            ),
            (
                "- Sensitivity Interpretation: "
                f"{report.clean_coverage_sensitivity_interpretation}"
            ),
            "",
            "### Delayed Anchor Impact",
            "",
            (
                "- Delayed Anchor Impact Status: "
                f"{report.delayed_anchor_impact_status}"
            ),
            (
                "- Delayed Anchor Materially Stronger: "
                f"{report.delayed_anchor_materially_stronger}"
            ),
            (
                "- No-Delayed-Anchor Positive: "
                f"{report.no_delayed_anchor_positive}"
            ),
            (
                "- Interpretation: "
                f"{report.delayed_anchor_impact_interpretation}"
            ),
            "",
            "### Outlier Sensitivity",
            "",
            (
                "- Outlier Sensitivity Status: "
                f"{report.outlier_sensitivity_status}"
            ),
            f"- Ex-NVDA Positive: {report.ex_nvda_positive}",
            f"- Ex-Top-2 Positive: {report.ex_top_2_positive}",
            (
                "- Interpretation: "
                f"{report.outlier_sensitivity_interpretation}"
            ),
        ]
    )
    if report.walk_forward_enabled:
        lines.extend(
            [
                "",
                "## Walk-Forward Stability",
                "",
                "- Walk-Forward Enabled: Yes",
                (
                    "- Periods Evaluated: "
                    f"{report.walk_forward_periods_evaluated}"
                ),
                (
                    "- Best Period by median_relative_return_12m: "
                    f"{report.best_period or 'Missing'}"
                ),
                (
                    "- Weakest Period by median_relative_return_12m: "
                    f"{report.weakest_period or 'Missing'}"
                ),
                (
                    "- Stability Judgment: "
                    f"{report.walk_forward_stability_judgment}"
                ),
                "",
                (
                    "| Period | Sample Size | Tickers | Median 12M Return | "
                    "Median Relative 12M Return | Hit Rate vs Benchmark 12M | "
                    "Concentration Warning |"
                ),
                "|---|---:|---|---:|---:|---:|---|",
            ]
        )
        for period in report.period_summaries:
            lines.append(
                f"| {period['period']} | {period['sample_size']} | "
                f"{period['tickers']} | "
                f"{_display_metric(period['median_forward_return_12m'])} | "
                f"{_display_metric(period['median_relative_return_12m'])} | "
                f"{_display_metric(period['hit_rate_vs_benchmark_12m'])} | "
                f"{period['concentration_warning']} |"
            )
    lines.extend(
        [
            "",
            "## What This Means",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in report.what_this_means)
    lines.extend(["", "## What This Does Not Mean", ""])
    lines.extend(f"- {item}" for item in report.what_this_does_not_mean)
    lines.extend(
        [
            "",
            "## Next Required Action",
            "",
            f"- Action Code: {report.next_required_action}",
            (
                "- Expand the sample across multiple tickers and/or multiple "
                "as-of dates before interpretation."
            ),
            "- Consider multi-ticker historical readiness batch generation.",
            "- Preserve dedupe controls.",
            "",
            "## Safety Notice",
            "",
            report.safety_notice,
            "",
        ]
    )
    return "\n".join(lines)


def write_readiness_trial_decision_report(
    *,
    output_dir: Path,
    manifest: dict,
    metrics: dict,
    rows: list[dict],
) -> ReadinessTrialDecisionReportFiles:
    """Build and persist readiness trial decision report artifacts."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_readiness_trial_decision_report(
        manifest=manifest,
        metrics=metrics,
        rows=rows,
    )
    json_path = output_dir / "readiness_trial_decision_report.json"
    markdown_path = output_dir / "readiness_trial_decision_report.md"
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_readiness_trial_decision_report(
            report,
            price_provider=str(
                manifest.get("price_provider_name")
                or manifest.get("price_provider")
                or "Unknown"
            ),
        ),
        encoding="utf-8",
    )
    return ReadinessTrialDecisionReportFiles(
        markdown_path=markdown_path,
        json_path=json_path,
        report=report,
    )


def regenerate_readiness_trial_decision_report(
    backtest_folder: Path,
) -> ReadinessTrialDecisionReportFiles:
    """Regenerate a decision report from an existing readiness run folder."""
    backtest_folder = Path(backtest_folder)
    manifest_path = backtest_folder / "backtest_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Backtest manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    metrics_path = Path(manifest["metrics_summary_path"])
    results_path = Path(manifest["results_path"])
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    with results_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    files = write_readiness_trial_decision_report(
        output_dir=backtest_folder,
        manifest=manifest,
        metrics=metrics,
        rows=rows,
    )
    manifest.update(
        {
            "readiness_trial_decision_report_path": str(
                files.markdown_path
            ),
            "readiness_trial_decision_report_json_path": str(files.json_path),
            "decision_status": files.report.decision_status,
            "statistical_validity": files.report.statistical_validity,
            "next_required_action": files.report.next_required_action,
            "walk_forward_stability_judgment": (
                files.report.walk_forward_stability_judgment
            ),
        }
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    return files
