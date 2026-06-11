"""Reproducible run-folder manifests for analyze-stock executions."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from broker_agents.deals.analyze_stock_intake import AnalyzeStockIntake
from broker_agents.deals.broker_deal_workflow import BrokerDealWorkflowResult

SAFE_RUN_LABEL = re.compile(r"[^a-z0-9_-]+")


@dataclass(frozen=True)
class AnalyzeStockRunBundle:
    """Paths and metadata for one archived analyze-stock execution."""

    run_id: str
    run_folder: Path
    run_summary_path: Path
    run_manifest_path: Path
    latest_manifest_path: Path
    generated_at: str

    def to_dict(self) -> dict:
        """Serialize bundle paths for CLI or future orchestration."""
        data = asdict(self)
        for key in (
            "run_folder",
            "run_summary_path",
            "run_manifest_path",
            "latest_manifest_path",
        ):
            data[key] = str(data[key])
        return data


def _safe_run_label(value: str | None) -> str | None:
    """Normalize an optional run label for use in a directory name."""
    if not value:
        return None
    normalized = SAFE_RUN_LABEL.sub("_", value.strip().lower()).strip("_")
    return normalized or None


def _allocate_run_id(
    runs_root: Path,
    generated_at: datetime,
    run_label: str | None,
) -> str:
    """Create a readable run ID and avoid same-second collisions."""
    base = generated_at.strftime("%Y%m%d_%H%M%S")
    safe_label = _safe_run_label(run_label)
    if safe_label:
        base = f"{base}_{safe_label}"
    run_id = base
    suffix = 2
    while (runs_root / run_id).exists():
        run_id = f"{base}_{suffix:02d}"
        suffix += 1
    return run_id


def _run_summary(manifest: dict) -> str:
    """Render the human-readable run summary."""
    blockers = manifest["promotion_blocking_categories"]
    return "\n".join(
        [
            f"# Analyze-Stock Run Summary - {manifest['ticker']}",
            "",
            "## Run Context",
            "",
            f"- Run ID: {manifest['run_id']}",
            f"- Generated At: {manifest['generated_at']}",
            f"- Ticker: {manifest['ticker']}",
            f"- Company Name: {manifest.get('company_name') or 'Not provided'}",
            f"- Input Mode: {manifest['input_mode']}",
            f"- Intake File: {manifest.get('intake_file') or 'Not used'}",
            f"- Run Label: {manifest.get('run_label') or 'Not provided'}",
            "",
            "## Evidence And Readiness",
            "",
            (
                "- Source Verification Status: "
                f"{manifest['source_verification_status']}"
            ),
            f"- Readiness Label: {manifest['readiness_label']}",
            (
                "- Total Investor Responses: "
                f"{manifest['total_investor_responses']}"
            ),
            f"- Total Work Orders: {manifest['total_work_orders']}",
            (
                "- Promotion-Blocking Categories: "
                f"{', '.join(blockers) if blockers else 'None'}"
            ),
            "",
            "## Main Output Paths",
            "",
            f"- Broker Deal Package: {manifest['broker_deal_package_path']}",
            f"- Enriched Input: {manifest['enriched_input_path']}",
            (
                "- Source Verification: "
                f"{manifest['source_verification_path']}"
            ),
            (
                "- Investor Response Letters: "
                f"{manifest['investor_response_letters_dir']}"
            ),
            (
                "- Investor Follow-Up Memos: "
                f"{manifest['investor_follow_up_memos_dir']}"
            ),
            (
                "- Backoffice Work Orders: "
                f"{manifest['backoffice_work_orders_path']}"
            ),
            f"- Intake Snapshot: {manifest['intake_snapshot_path']}",
            "",
            "## Safety Note",
            "",
            (
                "This run summary is not a recommendation, ranking, vote, average "
                "score, consensus, allocation instruction, rebalancing instruction, "
                "or trade signal. Final investor decisions remain independent. "
                "Auto-promotion disabled."
            ),
            "",
        ]
    )


def create_analyze_stock_run_bundle(
    *,
    intake: AnalyzeStockIntake,
    input_mode: str,
    intake_file: Path | None,
    intake_snapshot_path: Path,
    workflow_result: BrokerDealWorkflowResult,
    package_payload: dict,
    generated_at: datetime | None = None,
) -> AnalyzeStockRunBundle:
    """Create a run folder containing a summary and machine-readable manifest."""
    timestamp = generated_at or datetime.now(timezone.utc)
    generated_at_text = timestamp.isoformat()
    runs_root = intake.outputs_root / intake.ticker / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    run_id = _allocate_run_id(runs_root, timestamp, intake.run_label)
    run_folder = runs_root / run_id
    run_folder.mkdir(parents=True, exist_ok=False)

    letter_dir = next(
        iter(workflow_result.investor_response_letter_paths.values())
    ).parent
    memo_dir = next(
        iter(workflow_result.investor_follow_up_memo_paths.values())
    ).parent
    executive_summary = package_payload.get("executive_summary", {})
    work_order_plan = package_payload.get("backoffice_work_order_plan", {})
    manifest = {
        "run_id": run_id,
        "ticker": intake.ticker,
        "company_name": (
            intake.company_name or workflow_result.company_name or None
        ),
        "input_mode": input_mode,
        "intake_file": str(intake_file) if intake_file else None,
        "run_label": intake.run_label,
        "generated_at": generated_at_text,
        "broker_deal_package_path": str(
            workflow_result.broker_deal_package_path
        ),
        "enriched_input_path": str(workflow_result.enriched_pack_path),
        "source_verification_path": str(
            workflow_result.broker_deal_package_path
        ),
        "investor_response_letters_dir": str(letter_dir),
        "investor_follow_up_memos_dir": str(memo_dir),
        "backoffice_work_orders_path": str(
            workflow_result.backoffice_work_orders_path
        ),
        "intake_snapshot_path": str(intake_snapshot_path),
        "source_verification_status": (
            workflow_result.source_verification_status
        ),
        "readiness_label": executive_summary.get(
            "backoffice_readiness_label",
            "Unknown",
        ),
        "total_investor_responses": len(
            package_payload.get("investor_responses", [])
        ),
        "total_work_orders": work_order_plan.get(
            "total_work_orders",
            0,
        ),
        "promotion_blocking_categories": work_order_plan.get(
            "promotion_blocking_categories",
            [],
        ),
        "status": "completed",
    }
    manifest_path = run_folder / "run_manifest.json"
    manifest_text = json.dumps(manifest, indent=2)
    manifest_path.write_text(manifest_text, encoding="utf-8")
    summary_path = run_folder / "run_summary.md"
    summary_path.write_text(_run_summary(manifest), encoding="utf-8")
    latest_manifest_path = runs_root / "latest_run_manifest.json"
    latest_manifest_path.write_text(manifest_text, encoding="utf-8")
    return AnalyzeStockRunBundle(
        run_id=run_id,
        run_folder=run_folder,
        run_summary_path=summary_path,
        run_manifest_path=manifest_path,
        latest_manifest_path=latest_manifest_path,
        generated_at=generated_at_text,
    )
