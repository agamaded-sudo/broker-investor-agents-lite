"""Before/after audit report for clean historical coverage improvements."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This clean coverage before/after comparison is not a recommendation, "
    "ranking, vote, average score, consensus, allocation instruction, "
    "rebalancing instruction, trade signal, execution instruction, or "
    "investment advice."
)
SUMMARY_FIELDS = (
    "metric",
    "before",
    "after",
    "delta",
)


@dataclass(frozen=True)
class CleanCoverageComparisonReport:
    """Structured comparison of two readiness trial backtest runs."""

    comparison_run_id: str
    generated_at: str
    before_run_id: str | None
    after_run_id: str | None
    before_manifest_path: str | None
    after_manifest_path: str | None
    before_summary: dict
    after_summary: dict
    comparison_deltas: dict
    key_findings: list[str]
    limitations: list[str]
    comparison_status: str
    next_research_action: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready representation."""
        return asdict(self)


@dataclass(frozen=True)
class CleanCoverageComparisonFiles:
    """Generated comparison artifact paths and structured content."""

    comparison_folder: Path
    markdown_path: Path
    json_path: Path
    summary_csv_path: Path
    latest_manifest_path: Path
    report: CleanCoverageComparisonReport


def _load_json(path: Path | None) -> dict:
    if path is None or not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _numeric_delta(after: object, before: object) -> float | int | None:
    if after is None or before is None:
        return None
    try:
        result = float(after) - float(before)
    except (TypeError, ValueError):
        return None
    if result.is_integer():
        return int(result)
    return round(result, 6)


def _limited_financials_count(metrics: dict) -> int:
    counts = metrics.get("coverage_quality_counts") or {}
    return sum(
        int(count or 0)
        for label, count in counts.items()
        if "limited_financials" in str(label)
    )


def load_clean_coverage_run_summary(
    *,
    outputs_root: Path,
    run_id: str,
) -> dict:
    """Load one backtest manifest and linked metrics into a stable summary."""
    folder = Path(outputs_root) / "backtests" / str(run_id)
    manifest_path = folder / "backtest_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"Backtest manifest not found for run {run_id}: {manifest_path}"
        )
    manifest = _load_json(manifest_path)
    if manifest.get("backtest_run_type") != "readiness_trial":
        raise ValueError(f"Backtest run {run_id} is not a readiness_trial.")
    metrics_path_value = manifest.get("metrics_summary_path")
    metrics_path = (
        Path(metrics_path_value) if metrics_path_value else None
    )
    metrics = _load_json(metrics_path)
    sensitivity_path_value = manifest.get(
        "clean_coverage_sensitivity_report_json_path"
    )
    sensitivity_path = (
        Path(sensitivity_path_value) if sensitivity_path_value else None
    )
    sensitivity = _load_json(sensitivity_path)
    clean = sensitivity.get("subset_diagnostics", {}).get(
        "clean_records",
        {},
    )
    return {
        "backtest_run_id": str(manifest.get("backtest_run_id") or run_id),
        "manifest_path": str(manifest_path),
        "sample_size": int(
            manifest.get("overall_sample_size")
            or manifest.get("evaluated_rows")
            or metrics.get("sample_size")
            or 0
        ),
        "diagnostic_status": manifest.get("diagnostic_status"),
        "decision_status": manifest.get("decision_status"),
        "statistical_validity": manifest.get("statistical_validity"),
        "walk_forward_stability_judgment": manifest.get(
            "walk_forward_stability_judgment"
        ),
        "clean_record_count": int(manifest.get("clean_record_count") or 0),
        "warning_record_count": int(
            manifest.get("warning_record_count") or 0
        ),
        "warning_heavy_record_count": int(
            manifest.get("warning_heavy_record_count") or 0
        ),
        "limited_financials_record_count": _limited_financials_count(
            metrics
        ),
        "clean_coverage_sensitivity_status": manifest.get(
            "clean_coverage_sensitivity_status"
        ),
        "clean_only_available": bool(manifest.get("clean_only_available")),
        "delayed_anchor_record_count": int(
            manifest.get("delayed_anchor_record_count") or 0
        ),
        "no_delayed_anchor_record_count": int(
            manifest.get("no_delayed_anchor_record_count") or 0
        ),
        "delayed_anchor_impact_status": manifest.get(
            "delayed_anchor_impact_status"
        ),
        "outlier_dependence_status": manifest.get(
            "outlier_dependence_status"
        ),
        "nvda_record_count": int(manifest.get("nvda_record_count") or 0),
        "ex_nvda_positive": bool(manifest.get("ex_nvda_positive")),
        "ex_top_2_positive": bool(manifest.get("ex_top_2_positive")),
        "median_forward_return_12m": metrics.get(
            "median_forward_return_12m"
        ),
        "average_forward_return_12m": metrics.get(
            "average_forward_return_12m"
        ),
        "median_relative_return_12m": metrics.get(
            "median_relative_return_12m"
        ),
        "hit_rate_vs_benchmark_12m": metrics.get(
            "hit_rate_vs_benchmark_12m"
        ),
        "worst_max_drawdown_12m": metrics.get("worst_max_drawdown_12m"),
        "clean_subset": {
            "available": bool(clean.get("available")),
            "sample_size": int(clean.get("sample_size") or 0),
            "median_forward_return_12m": clean.get(
                "median_forward_return_12m"
            ),
            "median_relative_return_12m": clean.get(
                "median_relative_return_12m"
            ),
            "hit_rate_vs_benchmark_12m": clean.get(
                "hit_rate_vs_benchmark_12m"
            ),
            "worst_max_drawdown_12m": clean.get(
                "worst_max_drawdown_12m"
            ),
        },
    }


def find_latest_clean_coverage_runs(
    outputs_root: Path,
) -> tuple[str, str]:
    """Find latest pre-clean and post-clean readiness trial run IDs."""
    backtests_root = Path(outputs_root) / "backtests"
    before = []
    after = []
    for folder in backtests_root.iterdir() if backtests_root.is_dir() else []:
        manifest_path = folder / "backtest_manifest.json"
        if not manifest_path.is_file():
            continue
        try:
            manifest = _load_json(manifest_path)
        except (OSError, json.JSONDecodeError):
            continue
        status = manifest.get("clean_coverage_sensitivity_status")
        run_id = str(manifest.get("backtest_run_id") or folder.name)
        if status == "clean_not_available":
            before.append(run_id)
        elif status in {
            "clean_supported_preliminary",
            "clean_sample_too_small",
        }:
            after.append(run_id)
    if not before or not after:
        raise ValueError(
            "Auto comparison requires a clean_not_available run and a "
            "clean-supported run."
        )
    return max(before), max(after)


def _comparison_deltas(before: dict, after: dict) -> dict:
    return {
        "clean_records_delta": _numeric_delta(
            after.get("clean_record_count"),
            before.get("clean_record_count"),
        ),
        "warning_records_delta": _numeric_delta(
            after.get("warning_record_count"),
            before.get("warning_record_count"),
        ),
        "warning_heavy_records_delta": _numeric_delta(
            after.get("warning_heavy_record_count"),
            before.get("warning_heavy_record_count"),
        ),
        "limited_financials_records_delta": _numeric_delta(
            after.get("limited_financials_record_count"),
            before.get("limited_financials_record_count"),
        ),
        "clean_only_available_changed": (
            after.get("clean_only_available")
            != before.get("clean_only_available")
        ),
        "sensitivity_status_changed": (
            after.get("clean_coverage_sensitivity_status")
            != before.get("clean_coverage_sensitivity_status")
        ),
        "limited_financials_removed": (
            int(before.get("limited_financials_record_count") or 0) > 0
            and int(after.get("limited_financials_record_count") or 0) == 0
        ),
        "diagnostic_status_changed": (
            after.get("diagnostic_status") != before.get("diagnostic_status")
        ),
        "decision_status_changed": (
            after.get("decision_status") != before.get("decision_status")
        ),
        "median_12m_delta": _numeric_delta(
            after.get("median_forward_return_12m"),
            before.get("median_forward_return_12m"),
        ),
        "average_12m_delta": _numeric_delta(
            after.get("average_forward_return_12m"),
            before.get("average_forward_return_12m"),
        ),
        "median_relative_12m_delta": _numeric_delta(
            after.get("median_relative_return_12m"),
            before.get("median_relative_return_12m"),
        ),
        "hit_rate_12m_delta": _numeric_delta(
            after.get("hit_rate_vs_benchmark_12m"),
            before.get("hit_rate_vs_benchmark_12m"),
        ),
        "worst_drawdown_delta": _numeric_delta(
            after.get("worst_max_drawdown_12m"),
            before.get("worst_max_drawdown_12m"),
        ),
    }


def build_clean_coverage_comparison_report(
    *,
    comparison_run_id: str,
    generated_at: str,
    before_summary: dict | None,
    after_summary: dict | None,
) -> CleanCoverageComparisonReport:
    """Build a conservative before/after comparison."""
    before = before_summary or {}
    after = after_summary or {}
    if not before or not after:
        return CleanCoverageComparisonReport(
            comparison_run_id=comparison_run_id,
            generated_at=generated_at,
            before_run_id=before.get("backtest_run_id"),
            after_run_id=after.get("backtest_run_id"),
            before_manifest_path=before.get("manifest_path"),
            after_manifest_path=after.get("manifest_path"),
            before_summary=before,
            after_summary=after,
            comparison_deltas={},
            key_findings=[
                "Both before and after readiness trial runs are required."
            ],
            limitations=["Comparison inputs are incomplete."],
            comparison_status="insufficient_comparison_inputs",
            next_research_action="provide_complete_comparison_inputs",
        )
    deltas = _comparison_deltas(before, after)
    clean_delta = int(deltas["clean_records_delta"] or 0)
    heavy_delta = int(deltas["warning_heavy_records_delta"] or 0)
    if clean_delta > 0 and heavy_delta <= 0:
        status = "clean_coverage_improved"
    elif clean_delta < 0 or heavy_delta > 0:
        status = "clean_coverage_regressed"
    else:
        status = "clean_coverage_unchanged"
    findings = [
        (
            f"Clean records changed from {before['clean_record_count']} to "
            f"{after['clean_record_count']}."
        ),
        (
            "Warning-heavy records changed from "
            f"{before['warning_heavy_record_count']} to "
            f"{after['warning_heavy_record_count']}."
        ),
    ]
    if deltas["clean_only_available_changed"]:
        findings.append(
            "Clean-only sensitivity became available after fixture coverage "
            "improved."
        )
    if deltas["limited_financials_removed"]:
        findings.append(
            "Limited-financials records were removed from the evaluated "
            "post-change sample."
        )
    if (
        before.get("diagnostic_status") == after.get("diagnostic_status")
        and before.get("decision_status") == after.get("decision_status")
    ):
        findings.append(
            "The diagnostic and decision statuses remained conservative."
        )
    return CleanCoverageComparisonReport(
        comparison_run_id=comparison_run_id,
        generated_at=generated_at,
        before_run_id=before["backtest_run_id"],
        after_run_id=after["backtest_run_id"],
        before_manifest_path=before["manifest_path"],
        after_manifest_path=after["manifest_path"],
        before_summary=before,
        after_summary=after,
        comparison_deltas=deltas,
        key_findings=findings,
        limitations=[
            "The runs use local deterministic research fixtures.",
            "Before/after association does not establish strategy validity.",
            "Delayed-anchor and outlier cautions remain applicable.",
            "Clean evidence remains preliminary and research-only.",
        ],
        comparison_status=status,
        next_research_action=(
            "expand_ticker_universe_with_coverage_validation"
        ),
    )


def _display(value: object) -> str:
    if value is None:
        return "Missing"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def render_clean_coverage_comparison_report(
    report: CleanCoverageComparisonReport,
) -> str:
    """Render the comparison audit as Markdown."""
    before = report.before_summary
    after = report.after_summary
    deltas = report.comparison_deltas
    main_finding = (
        report.key_findings[0]
        if report.key_findings
        else "Comparison inputs are incomplete."
    )
    lines = [
        "# Clean Coverage Before/After Comparison Report",
        "",
        "## Executive Summary",
        "",
        f"- Comparison Status: {report.comparison_status}",
        f"- Before Run: {report.before_run_id or 'Missing'}",
        f"- After Run: {report.after_run_id or 'Missing'}",
        f"- Main Finding: {main_finding}",
    ]
    if not before or not after:
        lines.extend(["", "## Safety Notice", "", report.safety_notice, ""])
        return "\n".join(lines)
    coverage_rows = (
        ("Clean Records", "clean_record_count", "clean_records_delta"),
        ("Warning Records", "warning_record_count", "warning_records_delta"),
        (
            "Warning-Heavy Records",
            "warning_heavy_record_count",
            "warning_heavy_records_delta",
        ),
        (
            "Limited Financials Records",
            "limited_financials_record_count",
            "limited_financials_records_delta",
        ),
        (
            "Clean-Only Available",
            "clean_only_available",
            "clean_only_available_changed",
        ),
        (
            "Clean Coverage Sensitivity Status",
            "clean_coverage_sensitivity_status",
            "sensitivity_status_changed",
        ),
    )
    diagnostic_rows = (
        ("Sample Size", "sample_size", None),
        ("Median 12M", "median_forward_return_12m", "median_12m_delta"),
        (
            "Median Relative 12M",
            "median_relative_return_12m",
            "median_relative_12m_delta",
        ),
        (
            "Hit Rate 12M",
            "hit_rate_vs_benchmark_12m",
            "hit_rate_12m_delta",
        ),
        (
            "Worst Drawdown",
            "worst_max_drawdown_12m",
            "worst_drawdown_delta",
        ),
        ("Diagnostic Status", "diagnostic_status", "diagnostic_status_changed"),
        ("Decision Status", "decision_status", "decision_status_changed"),
    )
    lines.extend(
        [
            "",
            "## Coverage Quality Comparison",
            "",
            "| Metric | Before | After | Delta |",
            "|---|---:|---:|---:|",
        ]
    )
    for label, field, delta_field in coverage_rows:
        lines.append(
            f"| {label} | {_display(before.get(field))} | "
            f"{_display(after.get(field))} | "
            f"{_display(deltas.get(delta_field))} |"
        )
    lines.extend(
        [
            "",
            "## Diagnostic Result Comparison",
            "",
            "| Metric | Before | After | Delta |",
            "|---|---:|---:|---:|",
        ]
    )
    for label, field, delta_field in diagnostic_rows:
        delta = (
            _numeric_delta(after.get(field), before.get(field))
            if delta_field is None
            else deltas.get(delta_field)
        )
        lines.append(
            f"| {label} | {_display(before.get(field))} | "
            f"{_display(after.get(field))} | {_display(delta)} |"
        )
    before_clean = before["clean_subset"]
    after_clean = after["clean_subset"]
    lines.extend(
        [
            "",
            "## Clean Subset Comparison",
            "",
            (
                "- Before Clean Subset Available: "
                f"{_display(before_clean['available'])}"
            ),
            (
                "- After Clean Subset Available: "
                f"{_display(after_clean['available'])}"
            ),
            f"- After Clean Sample Size: {after_clean['sample_size']}",
            (
                "- After Clean Median 12M: "
                f"{_display(after_clean['median_forward_return_12m'])}"
            ),
            (
                "- After Clean Median Relative 12M: "
                f"{_display(after_clean['median_relative_return_12m'])}"
            ),
            (
                "- After Clean Hit Rate 12M: "
                f"{_display(after_clean['hit_rate_vs_benchmark_12m'])}"
            ),
            (
                "- Before clean-only evidence was unavailable."
                if not before_clean["available"]
                else "- Before clean-only evidence was available."
            ),
            "",
            "## Delayed Anchor and Outlier Context",
            "",
            (
                "- Delayed Anchor Impact Status Before/After: "
                f"{before['delayed_anchor_impact_status']} / "
                f"{after['delayed_anchor_impact_status']}"
            ),
            (
                "- Outlier Dependence Status Before/After: "
                f"{before['outlier_dependence_status']} / "
                f"{after['outlier_dependence_status']}"
            ),
            f"- Ex-NVDA Positive After: {_display(after['ex_nvda_positive'])}",
            f"- Ex-Top-2 Positive After: {_display(after['ex_top_2_positive'])}",
            "",
            "## Interpretation",
            "",
        ]
    )
    lines.extend(f"- {finding}" for finding in report.key_findings)
    lines.extend(
        [
            "- Clean evidence is preliminary, not validation.",
            "- Broader ticker and date coverage is still required.",
            "",
            "## What This Suggests",
            "",
            "- Fixture coverage improvement improved evidence quality.",
            "- The research pipeline can distinguish evidence quality.",
            "- Broader ticker/date expansion is now more meaningful.",
            "",
            "## What This Does Not Suggest",
            "",
            "- It does not prove a strategy.",
            "- It does not validate investor agents.",
            "- It does not create recommendations.",
            "- It does not create trade signals.",
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


def _summary_rows(report: CleanCoverageComparisonReport) -> list[dict]:
    before = report.before_summary
    after = report.after_summary
    deltas = report.comparison_deltas
    fields = (
        ("clean_record_count", "clean_records_delta"),
        ("warning_record_count", "warning_records_delta"),
        ("warning_heavy_record_count", "warning_heavy_records_delta"),
        (
            "limited_financials_record_count",
            "limited_financials_records_delta",
        ),
        ("median_forward_return_12m", "median_12m_delta"),
        ("median_relative_return_12m", "median_relative_12m_delta"),
        ("hit_rate_vs_benchmark_12m", "hit_rate_12m_delta"),
        ("worst_max_drawdown_12m", "worst_drawdown_delta"),
    )
    return [
        {
            "metric": field,
            "before": before.get(field),
            "after": after.get(field),
            "delta": deltas.get(delta_field),
        }
        for field, delta_field in fields
    ]


def _allocate_comparison_id(root: Path, timestamp: datetime) -> str:
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    candidate = base
    suffix = 2
    while (root / candidate).exists():
        candidate = f"{base}_{suffix:02d}"
        suffix += 1
    return candidate


def write_clean_coverage_comparison_report(
    *,
    outputs_root: Path,
    before_run_id: str,
    after_run_id: str,
    generated_at: datetime | None = None,
) -> CleanCoverageComparisonFiles:
    """Load two runs and persist a comparison bundle."""
    timestamp = generated_at or datetime.now(timezone.utc)
    root = Path(outputs_root) / "clean_coverage_comparisons"
    root.mkdir(parents=True, exist_ok=True)
    comparison_run_id = _allocate_comparison_id(root, timestamp)
    folder = root / comparison_run_id
    folder.mkdir(parents=True, exist_ok=False)
    before = load_clean_coverage_run_summary(
        outputs_root=outputs_root,
        run_id=before_run_id,
    )
    after = load_clean_coverage_run_summary(
        outputs_root=outputs_root,
        run_id=after_run_id,
    )
    report = build_clean_coverage_comparison_report(
        comparison_run_id=comparison_run_id,
        generated_at=timestamp.isoformat(),
        before_summary=before,
        after_summary=after,
    )
    markdown_path = folder / "clean_coverage_before_after_report.md"
    json_path = folder / "clean_coverage_before_after_report.json"
    summary_csv_path = folder / "clean_coverage_before_after_summary.csv"
    latest_manifest_path = (
        root / "latest_clean_coverage_comparison_manifest.json"
    )
    markdown_path.write_text(
        render_clean_coverage_comparison_report(report),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )
    with summary_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(_summary_rows(report))
    latest_manifest = {
        "comparison_run_id": comparison_run_id,
        "comparison_status": report.comparison_status,
        "before_run_id": before_run_id,
        "after_run_id": after_run_id,
        "comparison_folder": str(folder),
        "report_path": str(markdown_path),
        "report_json_path": str(json_path),
        "summary_csv_path": str(summary_csv_path),
        "generated_at": timestamp.isoformat(),
        "safety_notice": SAFETY_NOTICE,
    }
    latest_manifest_path.write_text(
        json.dumps(latest_manifest, indent=2),
        encoding="utf-8",
    )
    return CleanCoverageComparisonFiles(
        comparison_folder=folder,
        markdown_path=markdown_path,
        json_path=json_path,
        summary_csv_path=summary_csv_path,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
