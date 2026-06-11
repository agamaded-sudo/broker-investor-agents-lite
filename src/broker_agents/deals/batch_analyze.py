"""Batch archive support for repeated analyze-stock executions."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from broker_agents.deals.analyze_stock_runner import (
    AnalyzeStockExecutionResult,
)

SAFE_BATCH_LABEL = re.compile(r"[^a-z0-9_-]+")


@dataclass(frozen=True)
class BatchTickerResult:
    """One ticker result recorded in a batch manifest."""

    ticker: str
    status: str
    run_id: str | None = None
    run_folder: str | None = None
    run_manifest_path: str | None = None
    broker_deal_package_path: str | None = None
    readiness_label: str | None = None
    source_verification_status: str | None = None
    total_investor_responses: int = 0
    total_work_orders: int = 0
    promotion_blocking_categories: tuple[str, ...] = ()
    error: str | None = None

    def to_dict(self) -> dict:
        """Serialize the result for a JSON manifest."""
        data = asdict(self)
        data["promotion_blocking_categories"] = list(
            self.promotion_blocking_categories
        )
        return data


@dataclass(frozen=True)
class AnalyzeBatchBundle:
    """Paths and metadata for an archived batch execution."""

    batch_run_id: str
    batch_folder: Path
    batch_summary_path: Path
    batch_manifest_path: Path
    latest_manifest_path: Path
    generated_at: str
    completed_count: int
    failed_count: int
    skipped_count: int


def completed_batch_result(
    execution: AnalyzeStockExecutionResult,
) -> BatchTickerResult:
    """Convert one successful analyze-stock execution to a batch result."""
    manifest = json.loads(
        execution.run_bundle.run_manifest_path.read_text(encoding="utf-8")
    )
    return BatchTickerResult(
        ticker=execution.intake.ticker,
        status="completed",
        run_id=manifest["run_id"],
        run_folder=str(execution.run_bundle.run_folder),
        run_manifest_path=str(execution.run_bundle.run_manifest_path),
        broker_deal_package_path=manifest["broker_deal_package_path"],
        readiness_label=manifest["readiness_label"],
        source_verification_status=manifest["source_verification_status"],
        total_investor_responses=manifest["total_investor_responses"],
        total_work_orders=manifest["total_work_orders"],
        promotion_blocking_categories=tuple(
            manifest["promotion_blocking_categories"]
        ),
    )


def failed_batch_result(ticker: str, error: Exception | str) -> BatchTickerResult:
    """Create a failure result without interrupting the remaining batch."""
    return BatchTickerResult(
        ticker=ticker,
        status="failed",
        error=str(error),
    )


def _safe_batch_label(value: str | None) -> str | None:
    """Normalize a label for use in the batch folder name."""
    if not value:
        return None
    normalized = SAFE_BATCH_LABEL.sub("_", value.strip().lower()).strip("_")
    return normalized or None


def _allocate_batch_run_id(
    batch_runs_root: Path,
    generated_at: datetime,
    batch_label: str | None,
) -> str:
    """Create a readable batch ID and avoid same-second collisions."""
    base = generated_at.strftime("%Y%m%d_%H%M%S")
    safe_label = _safe_batch_label(batch_label)
    if safe_label:
        base = f"{base}_{safe_label}"
    batch_run_id = base
    suffix = 2
    while (batch_runs_root / batch_run_id).exists():
        batch_run_id = f"{base}_{suffix:02d}"
        suffix += 1
    return batch_run_id


def _render_batch_summary(manifest: dict) -> str:
    """Render a readable non-comparative summary of a batch run."""
    lines = [
        "# Analyze-Batch Run Summary",
        "",
        "## Batch Context",
        "",
        f"- Batch Run ID: {manifest['batch_run_id']}",
        f"- Generated At: {manifest['generated_at']}",
        f"- Input Mode: {manifest['input_mode']}",
        f"- Batch Label: {manifest.get('batch_label') or 'Not provided'}",
        f"- Total Tickers Requested: {len(manifest['requested_tickers'])}",
        f"- Completed Count: {manifest['completed_count']}",
        f"- Failed Count: {manifest['failed_count']}",
        f"- Skipped Count: {manifest['skipped_count']}",
        "",
        "## Ticker Results",
        "",
        (
            "| Ticker | Status | Run Folder | Broker Deal Package | "
            "Readiness Label | Source Verification Status | "
            "Promotion-Blocking Categories | Error |"
        ),
        "|---|---|---|---|---|---|---|---|",
    ]
    for result in manifest["results"]:
        blockers = ", ".join(result["promotion_blocking_categories"]) or "None"
        lines.append(
            "| {ticker} | {status} | {run_folder} | {package} | "
            "{readiness} | {source_status} | {blockers} | {error} |".format(
                ticker=result["ticker"],
                status=result["status"],
                run_folder=result["run_folder"] or "Not generated",
                package=(
                    result["broker_deal_package_path"] or "Not generated"
                ),
                readiness=result["readiness_label"] or "Not available",
                source_status=(
                    result["source_verification_status"] or "Not available"
                ),
                blockers=blockers,
                error=result["error"] or "",
            )
        )
    lines.extend(
        [
            "",
            "## Safety Note",
            "",
            (
                "This batch summary is not a recommendation, ranking, vote, "
                "average score, consensus, allocation instruction, rebalancing "
                "instruction, or trade signal. It records independent workflow "
                "statuses without comparing tickers as better or worse. "
                "Auto-promotion disabled."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def create_analyze_batch_bundle(
    *,
    outputs_root: Path,
    input_mode: str,
    batch_label: str | None,
    requested_tickers: list[str],
    results: list[BatchTickerResult],
    generated_at: datetime | None = None,
) -> AnalyzeBatchBundle:
    """Create a batch folder, summary, manifest, and latest pointer."""
    timestamp = generated_at or datetime.now(timezone.utc)
    generated_at_text = timestamp.isoformat()
    batch_runs_root = Path(outputs_root) / "batch_runs"
    batch_runs_root.mkdir(parents=True, exist_ok=True)
    batch_run_id = _allocate_batch_run_id(
        batch_runs_root,
        timestamp,
        batch_label,
    )
    batch_folder = batch_runs_root / batch_run_id
    batch_folder.mkdir(parents=True, exist_ok=False)

    completed_tickers = [
        result.ticker for result in results if result.status == "completed"
    ]
    failed_tickers = [
        result.ticker for result in results if result.status == "failed"
    ]
    skipped_tickers = [
        result.ticker for result in results if result.status == "skipped"
    ]
    manifest = {
        "batch_run_id": batch_run_id,
        "input_mode": input_mode,
        "batch_label": batch_label,
        "generated_at": generated_at_text,
        "requested_tickers": requested_tickers,
        "completed_tickers": completed_tickers,
        "failed_tickers": failed_tickers,
        "skipped_tickers": skipped_tickers,
        "completed_count": len(completed_tickers),
        "failed_count": len(failed_tickers),
        "skipped_count": len(skipped_tickers),
        "results": [result.to_dict() for result in results],
    }
    manifest_text = json.dumps(manifest, indent=2)
    batch_manifest_path = batch_folder / "batch_manifest.json"
    batch_manifest_path.write_text(manifest_text, encoding="utf-8")
    batch_summary_path = batch_folder / "batch_summary.md"
    batch_summary_path.write_text(
        _render_batch_summary(manifest),
        encoding="utf-8",
    )
    latest_manifest_path = batch_runs_root / "latest_batch_manifest.json"
    latest_manifest_path.write_text(manifest_text, encoding="utf-8")
    return AnalyzeBatchBundle(
        batch_run_id=batch_run_id,
        batch_folder=batch_folder,
        batch_summary_path=batch_summary_path,
        batch_manifest_path=batch_manifest_path,
        latest_manifest_path=latest_manifest_path,
        generated_at=generated_at_text,
        completed_count=len(completed_tickers),
        failed_count=len(failed_tickers),
        skipped_count=len(skipped_tickers),
    )
