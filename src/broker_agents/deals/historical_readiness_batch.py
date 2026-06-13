"""Multi-ticker coordination for historical readiness research runs."""

import csv
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import re

import yaml

from broker_agents.archive.signal_ledger import archive_completed_run
from broker_agents.backtesting.readiness_trial_export import (
    export_readiness_ledger_to_trial_ledger,
    validate_readiness_trial_ledger,
)
from broker_agents.backtesting.signal_backtester import run_signal_backtest
from broker_agents.deals.analyze_stock_intake import (
    build_ticker_analyze_stock_intake,
)
from broker_agents.deals.analyze_stock_runner import execute_analyze_stock

SAFETY_NOTICE = (
    "This historical readiness batch produces readiness-only research "
    "artifacts. It is not a recommendation batch, ranking batch, allocation "
    "batch, rebalancing batch, trade signal batch, or execution instruction "
    "batch."
)
SAFE_LABEL = re.compile(r"[^a-z0-9_-]+")
RESULT_FIELDS = (
    "ticker",
    "status",
    "run_id",
    "run_folder",
    "run_manifest",
    "historical_readiness_candidate_file",
    "historical_enriched_input_assembly_file",
    "historical_readiness_ledger_record_status",
    "warnings",
    "error",
)


@dataclass(frozen=True)
class HistoricalReadinessBatchRecord:
    """One ticker execution recorded by the readiness batch."""

    ticker: str
    status: str
    run_id: str | None = None
    run_folder: str | None = None
    run_manifest: str | None = None
    historical_readiness_candidate_file: str | None = None
    historical_enriched_input_assembly_file: str | None = None
    historical_readiness_ledger_record_status: str = "not_archived"
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict:
        """Serialize one batch record."""
        return asdict(self)


@dataclass(frozen=True)
class HistoricalReadinessBatchResult:
    """Artifacts and totals for a completed historical readiness batch."""

    batch_run_id: str
    batch_folder: Path
    manifest_path: Path
    summary_path: Path
    results_path: Path
    latest_manifest_path: Path
    total_requested: int
    total_completed: int
    total_failed: int
    trial_ledger_exported: bool
    trial_ledger_validation_status: str
    readiness_backtest_run: bool
    readiness_backtest_run_id: str | None = None
    readiness_backtest_folder: Path | None = None
    decision_status: str | None = None
    statistical_validity: str | None = None


def _normalize_tickers(tickers: str | list[str]) -> list[str]:
    """Normalize and deduplicate requested ticker symbols."""
    values = tickers.split(",") if isinstance(tickers, str) else tickers
    normalized = list(
        dict.fromkeys(str(value).strip().upper() for value in values if str(value).strip())
    )
    if not normalized:
        raise ValueError("Historical readiness batch requires at least one ticker.")
    return normalized


def _allocate_batch_run_id(
    root: Path,
    timestamp: datetime,
    batch_label: str | None,
) -> str:
    """Allocate a readable collision-safe batch run identifier."""
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    if batch_label:
        label = SAFE_LABEL.sub("_", batch_label.strip().lower()).strip("_")
        if label:
            base = f"{base}_{label}"
    candidate = base
    suffix = 2
    while (root / candidate).exists():
        candidate = f"{base}_{suffix:02d}"
        suffix += 1
    return candidate


def _completed_record(ticker: str, manifest_path: Path) -> HistoricalReadinessBatchRecord:
    """Build one successful ticker record from its run manifest."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidate = manifest.get("historical_signal_readiness_candidate", {})
    assembly = manifest.get("historical_enriched_input_assembly", {})
    readiness_record = manifest.get("historical_readiness_ledger_record", {})
    warnings = [
        str(warning)
        for warning in (
            list(candidate.get("warnings") or [])
            + list(assembly.get("warnings") or [])
        )
    ]
    candidate_file = candidate.get("candidate_file")
    assembly_file = assembly.get("assembly_file")
    if not candidate.get("enabled") or not candidate_file:
        raise ValueError(f"{ticker} did not produce a readiness candidate.")
    if not assembly.get("enabled") or not assembly_file:
        raise ValueError(f"{ticker} did not produce a historical input assembly.")
    if not readiness_record.get("archived"):
        raise ValueError(f"{ticker} readiness candidate was not archived.")
    return HistoricalReadinessBatchRecord(
        ticker=ticker,
        status="completed",
        run_id=str(manifest["run_id"]),
        run_folder=str(manifest_path.parent),
        run_manifest=str(manifest_path),
        historical_readiness_candidate_file=str(candidate_file),
        historical_enriched_input_assembly_file=str(assembly_file),
        historical_readiness_ledger_record_status="archived",
        warnings=warnings,
    )


def _render_summary(manifest: dict) -> str:
    """Render a readable, non-comparative readiness batch summary."""
    lines = [
        "# Historical Readiness Batch Summary",
        "",
        "## Batch Context",
        "",
        f"- Batch Run ID: {manifest['batch_run_id']}",
        f"- As-Of Date: {manifest['as_of_date']}",
        f"- Tickers Requested: {', '.join(manifest['tickers_requested'])}",
        f"- Total Requested: {manifest['total_requested']}",
        f"- Total Completed: {manifest['total_completed']}",
        f"- Total Failed: {manifest['total_failed']}",
        f"- Point-in-Time Enforcement: {manifest['point_in_time_enforcement']}",
        "",
        "## Ticker Results",
        "",
        (
            "| Ticker | Status | Run ID | Run Manifest | Readiness Candidate | "
            "Historical Input Assembly | Readiness Ledger | Error |"
        ),
        "|---|---|---|---|---|---|---|---|",
    ]
    for record in manifest["run_records"]:
        lines.append(
            "| {ticker} | {status} | {run_id} | {run_manifest} | "
            "{candidate} | {assembly} | {ledger} | {error} |".format(
                ticker=record["ticker"],
                status=record["status"],
                run_id=record["run_id"] or "Not generated",
                run_manifest=record["run_manifest"] or "Not generated",
                candidate=(
                    record["historical_readiness_candidate_file"]
                    or "Not generated"
                ),
                assembly=(
                    record["historical_enriched_input_assembly_file"]
                    or "Not generated"
                ),
                ledger=record["historical_readiness_ledger_record_status"],
                error=record["error"] or "",
            )
        )
    lines.extend(
        [
            "",
            "## Trial Pipeline",
            "",
            (
                f"- Trial Ledger Exported: "
                f"{'Yes' if manifest['trial_ledger_exported'] else 'No'}"
            ),
            (
                "- Trial Ledger Validation: "
                f"{manifest['trial_ledger_validation_status']}"
            ),
            (
                f"- Readiness Backtest Run: "
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
            "",
            "## Safety Notice",
            "",
            SAFETY_NOTICE,
            "",
        ]
    )
    return "\n".join(lines)


def run_historical_readiness_batch(
    *,
    tickers: str | list[str],
    as_of_date: str,
    examples_root: Path,
    outputs_root: Path,
    fixtures_root: Path,
    portfolio_context: Path | None,
    financials_provider: str,
    financials_root: Path | None,
    export_trial_ledger: bool = False,
    validate_trial_ledger: bool = False,
    run_readiness_backtest: bool = False,
    trial_ledger_path: Path = Path(
        "data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv"
    ),
    price_fixtures_path: Path = Path("tests/fixtures/historical_price_history"),
    batch_label: str | None = None,
    generated_at: datetime | None = None,
) -> HistoricalReadinessBatchResult:
    """Run historical readiness analysis and optional trial evaluation."""
    requested = _normalize_tickers(tickers)
    if not as_of_date:
        raise ValueError("--as-of-date is required for a readiness batch.")
    financials_provider = str(financials_provider).strip().lower()
    if financials_provider != "historical_csv":
        raise ValueError(
            "Historical readiness batch requires --financials-provider "
            "historical_csv."
        )
    if financials_root is None:
        raise ValueError(
            "--financials-root is required for historical_csv financials."
        )
    timestamp = generated_at or datetime.now(timezone.utc)
    batch_root = Path(outputs_root) / "historical_readiness_batch_runs"
    batch_root.mkdir(parents=True, exist_ok=True)
    batch_run_id = _allocate_batch_run_id(batch_root, timestamp, batch_label)
    batch_folder = batch_root / batch_run_id
    batch_folder.mkdir(parents=True, exist_ok=False)

    records = []
    for ticker in requested:
        try:
            intake = build_ticker_analyze_stock_intake(
                ticker=ticker,
                examples_root=examples_root,
                outputs_root=outputs_root,
                fixtures_root=fixtures_root,
                portfolio_context=portfolio_context,
                as_of_date=as_of_date,
                financials_provider=financials_provider,
                financials_root=financials_root,
            )
            execution = execute_analyze_stock(
                intake=intake,
                input_mode="ticker",
            )
            archive_completed_run(
                outputs_root=outputs_root,
                run_manifest_path=execution.run_bundle.run_manifest_path,
                broker_deal_package_path=(
                    execution.workflow_result.broker_deal_package_path
                ),
                batch_run_id=batch_run_id,
                batch_folder=batch_folder,
            )
            records.append(
                _completed_record(
                    ticker,
                    execution.run_bundle.run_manifest_path,
                )
            )
        except (
            OSError,
            ValueError,
            yaml.YAMLError,
            json.JSONDecodeError,
        ) as exc:
            records.append(
                HistoricalReadinessBatchRecord(
                    ticker=ticker,
                    status="failed",
                    error=str(exc),
                )
            )

    completed = [record.ticker for record in records if record.status == "completed"]
    failed = [record.ticker for record in records if record.status == "failed"]
    skipped = [record.ticker for record in records if record.status == "skipped"]
    must_export = export_trial_ledger or validate_trial_ledger or run_readiness_backtest
    export_result = None
    validation_result = None
    backtest_result = None
    pipeline_warnings = []

    if must_export and completed:
        try:
            export_result = export_readiness_ledger_to_trial_ledger(
                source_ledger=(
                    Path(outputs_root)
                    / "historical_readiness_ledger"
                    / "historical_signal_readiness_ledger.csv"
                ),
                output_ledger=trial_ledger_path,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            pipeline_warnings.append(f"Trial ledger export failed: {exc}")
    elif must_export:
        pipeline_warnings.append(
            "Trial pipeline skipped because no ticker runs completed."
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
                "Readiness backtest skipped because trial ledger validation failed."
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
                )
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                pipeline_warnings.append(f"Readiness backtest failed: {exc}")

    manifest = {
        "batch_run_id": batch_run_id,
        "generated_at": timestamp.isoformat(),
        "as_of_date": as_of_date,
        "tickers_requested": requested,
        "completed_tickers": completed,
        "failed_tickers": failed,
        "skipped_tickers": skipped,
        "total_requested": len(requested),
        "total_completed": len(completed),
        "total_failed": len(failed),
        "outputs_root": str(outputs_root),
        "financials_provider": financials_provider,
        "financials_root": str(financials_root),
        "point_in_time_enforcement": "readiness_only",
        "safety_notice": SAFETY_NOTICE,
        "run_records": [record.to_dict() for record in records],
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
    manifest_path = batch_folder / "historical_readiness_batch_manifest.json"
    summary_path = batch_folder / "historical_readiness_batch_summary.md"
    results_path = batch_folder / "historical_readiness_batch_results.csv"
    manifest_text = json.dumps(manifest, indent=2)
    manifest_path.write_text(manifest_text, encoding="utf-8")
    summary_path.write_text(_render_summary(manifest), encoding="utf-8")
    with results_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        for record in records:
            row = record.to_dict()
            row["warnings"] = "; ".join(row["warnings"])
            writer.writerow(row)
    latest_manifest_path = (
        batch_root / "latest_historical_readiness_batch_manifest.json"
    )
    latest_manifest_path.write_text(manifest_text, encoding="utf-8")
    return HistoricalReadinessBatchResult(
        batch_run_id=batch_run_id,
        batch_folder=batch_folder,
        manifest_path=manifest_path,
        summary_path=summary_path,
        results_path=results_path,
        latest_manifest_path=latest_manifest_path,
        total_requested=len(requested),
        total_completed=len(completed),
        total_failed=len(failed),
        trial_ledger_exported=export_result is not None,
        trial_ledger_validation_status=(
            validation_result.status if validation_result else "not_run"
        ),
        readiness_backtest_run=backtest_result is not None,
        readiness_backtest_run_id=(
            backtest_result.backtest_run_id if backtest_result else None
        ),
        readiness_backtest_folder=(
            backtest_result.backtest_folder if backtest_result else None
        ),
        decision_status=(
            backtest_result.decision_status if backtest_result else None
        ),
        statistical_validity=(
            backtest_result.statistical_validity if backtest_result else None
        ),
    )
