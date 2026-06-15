"""Coordinate historical readiness batches across multiple as-of dates."""

import csv
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path

from broker_agents.backtesting.readiness_trial_export import (
    export_readiness_ledger_to_trial_ledger,
    validate_readiness_trial_ledger,
)
from broker_agents.backtesting.signal_backtester import run_signal_backtest
from broker_agents.deals.historical_readiness_batch import (
    run_historical_readiness_batch,
)
from broker_agents.deals.historical_date_coverage import (
    build_historical_date_coverage_report,
    resolve_historical_date_preset,
    validate_historical_date_coverage,
)

SAFETY_NOTICE = (
    "This historical readiness multi-date trial produces readiness-only "
    "research artifacts. It is not a recommendation trial, ranking trial, "
    "allocation trial, rebalancing trial, trade signal trial, or execution "
    "instruction trial."
)
RESULT_FIELDS = (
    "as_of_date",
    "status",
    "batch_run_id",
    "batch_folder",
    "batch_manifest",
    "batch_summary",
    "completed_tickers",
    "failed_tickers",
    "total_completed",
    "total_failed",
    "date_coverage_status",
    "coverage_quality_label",
    "coverage_quality_severity",
    "has_delayed_price_anchor",
    "has_limited_financials",
    "warning_count",
    "clean_record_count_estimate",
    "limited_financials_record_count",
    "delayed_anchor_record_count",
    "warnings",
    "error",
)


@dataclass(frozen=True)
class HistoricalReadinessDateBatchRecord:
    """One date-level historical readiness batch result."""

    as_of_date: str
    status: str
    batch_run_id: str | None = None
    batch_folder: str | None = None
    batch_manifest: str | None = None
    batch_summary: str | None = None
    completed_tickers: list[str] = field(default_factory=list)
    failed_tickers: list[str] = field(default_factory=list)
    total_completed: int = 0
    total_failed: int = 0
    date_coverage_status: str = "not_validated"
    coverage_quality_label: str = "unsupported"
    coverage_quality_severity: str = "unsupported"
    has_delayed_price_anchor: bool = False
    has_limited_financials: bool = False
    warning_count: int = 0
    clean_record_count_estimate: int = 0
    limited_financials_record_count: int = 0
    delayed_anchor_record_count: int = 0
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict:
        """Serialize one date batch record."""
        return asdict(self)


@dataclass(frozen=True)
class HistoricalReadinessMultidateResult:
    """Artifacts and counts for one multi-date readiness trial."""

    multidate_run_id: str
    multidate_folder: Path
    manifest_path: Path
    summary_path: Path
    results_path: Path
    latest_manifest_path: Path
    total_expected_runs: int
    total_completed_runs: int
    total_failed_runs: int
    trial_ledger_exported: bool
    trial_ledger_validation_status: str
    readiness_backtest_run: bool
    sample_size_after_dedupe: int | None = None
    decision_status: str | None = None
    statistical_validity: str | None = None
    date_preset: str | None = None
    resolved_as_of_dates: list[str] = field(default_factory=list)
    usable_dates: list[str] = field(default_factory=list)
    skipped_dates: list[str] = field(default_factory=list)
    date_coverage_status: str = "not_run"
    date_coverage_report_path: Path | None = None
    coverage_quality_counts: dict[str, int] = field(default_factory=dict)
    coverage_severity_counts: dict[str, int] = field(default_factory=dict)


def _normalize_values(value: str | list[str], *, uppercase: bool) -> list[str]:
    """Normalize and deduplicate comma-separated or list inputs."""
    values = value.split(",") if isinstance(value, str) else value
    normalized = []
    for item in values:
        cleaned = str(item).strip()
        if not cleaned:
            continue
        normalized.append(cleaned.upper() if uppercase else cleaned)
    return list(dict.fromkeys(normalized))


def _allocate_multidate_run_id(root: Path, timestamp: datetime) -> str:
    """Allocate a collision-safe multi-date run identifier."""
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    candidate = base
    suffix = 2
    while (root / candidate).exists():
        candidate = f"{base}_{suffix:02d}"
        suffix += 1
    return candidate


def _date_record(
    as_of_date: str,
    *,
    batch_manifest_path: Path,
    batch_folder: Path,
    batch_summary_path: Path,
    batch_run_id: str,
    coverage_record: object,
) -> HistoricalReadinessDateBatchRecord:
    """Build a date record from one completed Task 87 batch manifest."""
    manifest = json.loads(
        batch_manifest_path.read_text(encoding="utf-8")
    )
    total_completed = int(manifest.get("total_completed") or 0)
    total_failed = int(manifest.get("total_failed") or 0)
    status = "completed" if total_completed else "failed"
    error = (
        None
        if total_completed
        else "No ticker runs completed for this as-of date."
    )
    return HistoricalReadinessDateBatchRecord(
        as_of_date=as_of_date,
        status=status,
        batch_run_id=batch_run_id,
        batch_folder=str(batch_folder),
        batch_manifest=str(batch_manifest_path),
        batch_summary=str(batch_summary_path),
        completed_tickers=list(manifest.get("completed_tickers") or []),
        failed_tickers=list(manifest.get("failed_tickers") or []),
        total_completed=total_completed,
        total_failed=total_failed,
        date_coverage_status=coverage_record.status,
        coverage_quality_label=coverage_record.coverage_quality_label,
        coverage_quality_severity=coverage_record.coverage_quality_severity,
        has_delayed_price_anchor=(
            coverage_record.has_delayed_price_anchor
        ),
        has_limited_financials=coverage_record.has_limited_financials,
        warning_count=coverage_record.warning_count,
        clean_record_count_estimate=(
            coverage_record.clean_record_count_estimate
        ),
        limited_financials_record_count=(
            coverage_record.limited_financials_record_count
        ),
        delayed_anchor_record_count=(
            coverage_record.delayed_anchor_record_count
        ),
        warnings=list(manifest.get("pipeline_warnings") or []),
        error=error,
    )


def _render_summary(manifest: dict) -> str:
    """Render a non-comparative multi-date research summary."""
    lines = [
        "# Historical Readiness Multi-Date Trial Summary",
        "",
        "## Trial Context",
        "",
        f"- Multi-Date Run ID: {manifest['multidate_run_id']}",
        f"- Generated At: {manifest['generated_at']}",
        f"- Tickers Requested: {', '.join(manifest['tickers_requested'])}",
        (
            "- As-Of Dates Requested: "
            f"{', '.join(manifest['as_of_dates_requested'])}"
        ),
        f"- Date Preset: {manifest.get('date_preset') or 'explicit'}",
        (
            "- Resolved As-Of Dates: "
            f"{', '.join(manifest['resolved_as_of_dates'])}"
        ),
        f"- Usable Dates: {', '.join(manifest['usable_dates']) or 'None'}",
        f"- Skipped Dates: {', '.join(manifest['skipped_dates']) or 'None'}",
        f"- Date Coverage Status: {manifest['date_coverage_status']}",
        (
            "- Date Coverage Report: "
            f"{manifest['date_coverage_report_path']}"
        ),
        f"- Total Expected Runs: {manifest['total_expected_runs']}",
        f"- Total Completed Runs: {manifest['total_completed_runs']}",
        f"- Total Failed Runs: {manifest['total_failed_runs']}",
        f"- Point-in-Time Enforcement: {manifest['point_in_time_enforcement']}",
        "",
        "## Coverage Quality Summary",
        "",
        (
            "- Coverage Quality Counts: "
            f"{manifest['coverage_quality_counts']}"
        ),
        (
            "- Coverage Severity Counts: "
            f"{manifest['coverage_severity_counts']}"
        ),
        f"- Clean Dates: {manifest['clean_date_count']}",
        f"- Warning-Heavy Dates: {manifest['warning_date_count']}",
        f"- Unsupported Dates Skipped: {manifest['unsupported_date_count']}",
        (
            "- Clean Record Estimate: "
            f"{manifest['clean_record_count_estimate']}"
        ),
        (
            "- Warning Record Estimate: "
            f"{manifest['warning_record_count_estimate']}"
        ),
        (
            "- Date-level warnings may coexist with clean ticker-date "
            "records."
        ),
        "",
        "## Date Batch Results",
        "",
        (
            "| As-Of Date | Status | Quality | Severity | Delayed Anchor | "
            "Limited Financials | Completed Tickers | Failed Tickers | "
            "Completed Runs | Failed Runs | Error |"
        ),
        "|---|---|---|---|---|---|---|---|---:|---:|---|",
    ]
    for record in manifest["date_batch_records"]:
        lines.append(
            "| {date} | {status} | {quality} | {severity} | {delayed} | "
            "{limited} | {completed} | {failed} | {total_completed} | "
            "{total_failed} | {error} |".format(
                date=record["as_of_date"],
                status=record["status"],
                quality=record["coverage_quality_label"],
                severity=record["coverage_quality_severity"],
                delayed=record["has_delayed_price_anchor"],
                limited=record["has_limited_financials"],
                completed=", ".join(record["completed_tickers"]) or "None",
                failed=", ".join(record["failed_tickers"]) or "None",
                total_completed=record["total_completed"],
                total_failed=record["total_failed"],
                error=record["error"] or "",
            )
        )
    lines.extend(
        [
            "",
            "## Aggregate Trial Pipeline",
            "",
            (
                "- Trial Ledger Exported: "
                f"{'Yes' if manifest['trial_ledger_exported'] else 'No'}"
            ),
            (
                "- Trial Ledger Validation: "
                f"{manifest['trial_ledger_validation_status']}"
            ),
            (
                "- Metadata Enrichment Status: "
                f"{manifest['metadata_enrichment_status']}"
            ),
            (
                "- Readiness Backtest Run: "
                f"{'Yes' if manifest['readiness_backtest_run'] else 'No'}"
            ),
            (
                "- Sample Size After Dedupe: "
                f"{manifest.get('sample_size_after_dedupe') or 'Not run'}"
            ),
            f"- Decision Status: {manifest.get('decision_status') or 'Not run'}",
            (
                "- Statistical Validity: "
                f"{manifest.get('statistical_validity') or 'Not run'}"
            ),
            (
                "- Missing metadata and readiness-only sections remain "
                "visible in the trial and decision artifacts."
            ),
            "",
            "## Safety Notice",
            "",
            SAFETY_NOTICE,
            "",
        ]
    )
    return "\n".join(lines)


def run_historical_readiness_multidate(
    *,
    tickers: str | list[str],
    as_of_dates: str | list[str] | None,
    date_preset: str | None = None,
    examples_root: Path,
    outputs_root: Path,
    fixtures_root: Path,
    portfolio_context: Path | None,
    financials_provider: str,
    financials_root: Path | None,
    export_trial_ledger: bool = False,
    validate_trial_ledger: bool = False,
    run_readiness_backtest: bool = False,
    walk_forward: bool = False,
    walk_forward_frequency: str = "yearly",
    trial_ledger_path: Path = Path(
        "data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv"
    ),
    price_fixtures_path: Path = Path("tests/fixtures/historical_price_history"),
    generated_at: datetime | None = None,
) -> HistoricalReadinessMultidateResult:
    """Run Task 87 batches across multiple historical as-of dates."""
    requested_tickers = _normalize_values(tickers, uppercase=True)
    if as_of_dates:
        requested_dates = _normalize_values(as_of_dates, uppercase=False)
        effective_preset = None
    else:
        effective_preset = date_preset or "annual_3"
        requested_dates = resolve_historical_date_preset(effective_preset)
    if not requested_tickers:
        raise ValueError("Multi-date readiness trial requires at least one ticker.")
    if not requested_dates:
        raise ValueError(
            "Multi-date readiness trial requires at least one as-of date."
        )
    timestamp = generated_at or datetime.now(timezone.utc)
    root = Path(outputs_root) / "historical_readiness_multidate_runs"
    root.mkdir(parents=True, exist_ok=True)
    multidate_run_id = _allocate_multidate_run_id(root, timestamp)
    multidate_folder = root / multidate_run_id
    multidate_folder.mkdir(parents=True, exist_ok=False)
    coverage_report = validate_historical_date_coverage(
        requested_dates=requested_dates,
        tickers=requested_tickers,
        price_root=price_fixtures_path,
        financials_root=financials_root,
        date_preset=effective_preset,
    )
    coverage_json_path = (
        multidate_folder / "historical_date_coverage_report.json"
    )
    coverage_markdown_path = (
        multidate_folder / "historical_date_coverage_report.md"
    )
    build_historical_date_coverage_report(
        report=coverage_report,
        json_path=coverage_json_path,
        markdown_path=coverage_markdown_path,
    )
    if effective_preset and not coverage_report.usable_dates:
        raise ValueError(
            "Historical date coverage is insufficient: zero usable dates."
        )
    execution_dates = (
        coverage_report.usable_dates if effective_preset else requested_dates
    )

    date_records = []
    coverage_by_date = {
        record.as_of_date: record for record in coverage_report.date_records
    }
    for as_of_date in execution_dates:
        coverage_record = coverage_by_date[as_of_date]
        try:
            batch_result = run_historical_readiness_batch(
                tickers=requested_tickers,
                as_of_date=as_of_date,
                examples_root=examples_root,
                outputs_root=outputs_root,
                fixtures_root=fixtures_root,
                portfolio_context=portfolio_context,
                financials_provider=financials_provider,
                financials_root=financials_root,
                batch_label=f"as_of_{as_of_date}",
            )
            date_records.append(
                _date_record(
                    as_of_date,
                    batch_manifest_path=batch_result.manifest_path,
                    batch_folder=batch_result.batch_folder,
                    batch_summary_path=batch_result.summary_path,
                    batch_run_id=batch_result.batch_run_id,
                    coverage_record=coverage_record,
                )
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            date_records.append(
                HistoricalReadinessDateBatchRecord(
                    as_of_date=as_of_date,
                    status="failed",
                    total_failed=len(requested_tickers),
                    failed_tickers=list(requested_tickers),
                    date_coverage_status=coverage_record.status,
                    coverage_quality_label=(
                        coverage_record.coverage_quality_label
                    ),
                    coverage_quality_severity=(
                        coverage_record.coverage_quality_severity
                    ),
                    has_delayed_price_anchor=(
                        coverage_record.has_delayed_price_anchor
                    ),
                    has_limited_financials=(
                        coverage_record.has_limited_financials
                    ),
                    warning_count=coverage_record.warning_count,
                    clean_record_count_estimate=(
                        coverage_record.clean_record_count_estimate
                    ),
                    limited_financials_record_count=(
                        coverage_record.limited_financials_record_count
                    ),
                    delayed_anchor_record_count=(
                        coverage_record.delayed_anchor_record_count
                    ),
                    error=str(exc),
                )
            )

    total_completed_runs = sum(
        record.total_completed for record in date_records
    )
    total_failed_runs = sum(record.total_failed for record in date_records)
    completed_dates = [
        record.as_of_date
        for record in date_records
        if record.status == "completed"
    ]
    failed_dates = [
        record.as_of_date for record in date_records if record.status == "failed"
    ]
    must_export = (
        export_trial_ledger
        or validate_trial_ledger
        or run_readiness_backtest
    )
    export_result = None
    validation_result = None
    backtest_result = None
    pipeline_warnings = list(coverage_report.warnings)

    if must_export and total_completed_runs:
        try:
            export_result = export_readiness_ledger_to_trial_ledger(
                source_ledger=(
                    Path(outputs_root)
                    / "historical_readiness_ledger"
                    / "historical_signal_readiness_ledger.csv"
                ),
                output_ledger=trial_ledger_path,
                unsupported_dates_excluded_count=(
                    coverage_report.unsupported_date_count
                ),
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            pipeline_warnings.append(f"Trial ledger export failed: {exc}")
    elif must_export:
        pipeline_warnings.append(
            "Aggregate trial pipeline skipped because no ticker/date runs "
            "completed."
        )
    if validate_trial_ledger and export_result:
        try:
            validation_result = validate_readiness_trial_ledger(
                export_result.output_ledger
            )
        except (OSError, ValueError) as exc:
            pipeline_warnings.append(f"Trial ledger validation failed: {exc}")
    if run_readiness_backtest and export_result:
        if validation_result and validation_result.status != "valid":
            pipeline_warnings.append(
                "Readiness backtest skipped because trial ledger validation "
                "failed."
            )
        else:
            try:
                backtest_result = run_signal_backtest(
                    ledger_path=export_result.output_ledger,
                    price_fixtures_path=price_fixtures_path,
                    outputs_root=outputs_root,
                    price_provider="csv",
                    lookback_years=5,
                    dedupe_mode="latest_per_ticker_per_day",
                    walk_forward=walk_forward,
                    walk_forward_frequency=walk_forward_frequency,
                )
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                pipeline_warnings.append(f"Readiness backtest failed: {exc}")

    manifest = {
        "multidate_run_id": multidate_run_id,
        "generated_at": timestamp.isoformat(),
        "tickers_requested": requested_tickers,
        "as_of_dates_requested": requested_dates,
        "date_preset": effective_preset,
        "resolved_as_of_dates": requested_dates,
        "date_coverage_status": coverage_report.validation_status,
        "date_coverage_report_path": str(coverage_markdown_path),
        "date_coverage_report_json_path": str(coverage_json_path),
        "usable_dates": coverage_report.usable_dates,
        "skipped_dates": coverage_report.skipped_dates,
        "coverage_quality_counts": coverage_report.coverage_quality_counts,
        "coverage_severity_counts": coverage_report.coverage_severity_counts,
        "clean_date_count": coverage_report.clean_date_count,
        "warning_date_count": coverage_report.warning_date_count,
        "unsupported_date_count": coverage_report.unsupported_date_count,
        "clean_record_count_estimate": (
            coverage_report.clean_record_count_estimate
        ),
        "warning_record_count_estimate": (
            coverage_report.warning_record_count_estimate
        ),
        "total_expected_runs": (
            len(requested_tickers) * len(execution_dates)
        ),
        "total_completed_runs": total_completed_runs,
        "total_failed_runs": total_failed_runs,
        "completed_dates": completed_dates,
        "failed_dates": failed_dates,
        "outputs_root": str(outputs_root),
        "financials_provider": financials_provider,
        "financials_root": (
            str(financials_root) if financials_root is not None else None
        ),
        "point_in_time_enforcement": "readiness_only",
        "safety_notice": SAFETY_NOTICE,
        "date_batch_records": [record.to_dict() for record in date_records],
        "trial_ledger_exported": export_result is not None,
        "trial_ledger_path": (
            str(export_result.output_ledger) if export_result else None
        ),
        "trial_ledger_metadata_path": (
            str(export_result.metadata_file) if export_result else None
        ),
        "trial_ledger_total_exported_records": (
            export_result.total_exported_records if export_result else 0
        ),
        "metadata_enrichment_status": (
            json.dumps(
                export_result.metadata_enrichment_status_counts,
                sort_keys=True,
            )
            if export_result
            else "not_run"
        ),
        "trial_ledger_validation_status": (
            validation_result.status if validation_result else "not_run"
        ),
        "trial_ledger_validation_invalid_rows": (
            validation_result.invalid_rows if validation_result else 0
        ),
        "trial_ledger_validation_rows": (
            validation_result.rows if validation_result else 0
        ),
        "readiness_backtest_run": backtest_result is not None,
        "walk_forward_requested": walk_forward,
        "walk_forward_frequency": walk_forward_frequency,
        "readiness_backtest_run_id": (
            backtest_result.backtest_run_id if backtest_result else None
        ),
        "readiness_backtest_folder": (
            str(backtest_result.backtest_folder) if backtest_result else None
        ),
        "readiness_backtest_manifest": (
            str(backtest_result.manifest_path) if backtest_result else None
        ),
        "readiness_backtest_decision_report": (
            str(backtest_result.decision_report_path)
            if backtest_result
            else None
        ),
        "decision_status": (
            backtest_result.decision_status if backtest_result else None
        ),
        "statistical_validity": (
            backtest_result.statistical_validity if backtest_result else None
        ),
        "sample_size_after_dedupe": (
            backtest_result.metrics["sample_size"] if backtest_result else None
        ),
        "pipeline_warnings": pipeline_warnings,
        "status": "completed",
    }
    manifest_path = (
        multidate_folder / "historical_readiness_multidate_manifest.json"
    )
    summary_path = (
        multidate_folder / "historical_readiness_multidate_summary.md"
    )
    results_path = (
        multidate_folder / "historical_readiness_multidate_results.csv"
    )
    manifest_text = json.dumps(manifest, indent=2)
    manifest_path.write_text(manifest_text, encoding="utf-8")
    summary_path.write_text(_render_summary(manifest), encoding="utf-8")
    with results_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        for record in date_records:
            row = record.to_dict()
            row["completed_tickers"] = ";".join(row["completed_tickers"])
            row["failed_tickers"] = ";".join(row["failed_tickers"])
            row["warnings"] = "; ".join(row["warnings"])
            writer.writerow(row)
    latest_manifest_path = (
        root / "latest_historical_readiness_multidate_manifest.json"
    )
    latest_manifest_path.write_text(manifest_text, encoding="utf-8")
    return HistoricalReadinessMultidateResult(
        multidate_run_id=multidate_run_id,
        multidate_folder=multidate_folder,
        manifest_path=manifest_path,
        summary_path=summary_path,
        results_path=results_path,
        latest_manifest_path=latest_manifest_path,
        total_expected_runs=manifest["total_expected_runs"],
        total_completed_runs=total_completed_runs,
        total_failed_runs=total_failed_runs,
        trial_ledger_exported=export_result is not None,
        trial_ledger_validation_status=(
            validation_result.status if validation_result else "not_run"
        ),
        readiness_backtest_run=backtest_result is not None,
        sample_size_after_dedupe=manifest["sample_size_after_dedupe"],
        decision_status=manifest["decision_status"],
        statistical_validity=manifest["statistical_validity"],
        date_preset=effective_preset,
        resolved_as_of_dates=requested_dates,
        usable_dates=coverage_report.usable_dates,
        skipped_dates=coverage_report.skipped_dates,
        date_coverage_status=coverage_report.validation_status,
        date_coverage_report_path=coverage_markdown_path,
        coverage_quality_counts=coverage_report.coverage_quality_counts,
        coverage_severity_counts=coverage_report.coverage_severity_counts,
    )
