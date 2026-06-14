"""Reproducible run-folder manifests for analyze-stock executions."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from broker_agents.archive.historical_readiness_ledger import (
    append_historical_readiness_candidate,
)
from broker_agents.deals.analyze_stock_intake import AnalyzeStockIntake
from broker_agents.deals.broker_deal_workflow import BrokerDealWorkflowResult
from broker_agents.deals.historical_date_coverage import (
    validate_historical_date_coverage,
)
from broker_agents.historical.as_of_context import build_as_of_context
from broker_agents.historical.financials_as_of_contract import (
    build_financials_as_of_contract,
)
from broker_agents.historical.historical_financials import (
    filter_financials_as_of,
    historical_financials_path,
    load_historical_financials_csv,
    validate_historical_financials_csv,
    write_historical_financials_csv,
)
from broker_agents.historical.historical_enriched_input import (
    build_historical_enriched_input_assembly,
    write_historical_enriched_input_assembly,
)
from broker_agents.historical.historical_signal_readiness import (
    build_historical_signal_readiness_candidate,
    write_historical_signal_readiness_candidate,
)
from broker_agents.deals.readiness_metadata_enrichment import (
    build_readiness_metadata,
)
from broker_agents.historical.price_windows import (
    build_analysis_price_window,
)
from broker_agents.historical.snapshot_contract import (
    build_historical_snapshot_contract,
)

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


def _create_official_financials_snapshot(
    *,
    intake: AnalyzeStockIntake,
    run_folder: Path,
) -> dict:
    """Create the optional filtered financials snapshot and audit metadata."""
    if intake.financials_provider != "historical_csv":
        return {
            "enabled": False,
            "provider": "sec_fixture",
            "status": "not_enabled",
            "warnings": [],
        }
    if not intake.as_of_date or intake.financials_root is None:
        raise ValueError(
            "Historical financials snapshots require --as-of-date and "
            "--financials-root."
        )
    source_path = historical_financials_path(
        intake.financials_root,
        intake.ticker,
    )
    validation = validate_historical_financials_csv(source_path)
    if not validation.file_found:
        raise ValueError(validation.warnings[0])
    if not validation.required_columns_present:
        raise ValueError("; ".join(validation.warnings))
    rows = load_historical_financials_csv(source_path)
    filtered = filter_financials_as_of(rows, intake.as_of_date)
    snapshot_path = run_folder / "official_financials_as_of_snapshot.csv"
    metadata_path = (
        run_folder / "official_financials_as_of_snapshot_metadata.json"
    )
    write_historical_financials_csv(snapshot_path, filtered.rows)
    warnings = [*validation.warnings, *filtered.warnings]
    metadata = {
        "enabled": True,
        "ticker": intake.ticker,
        "as_of_date": intake.as_of_date,
        "provider": "historical_financials_csv",
        "source_file": str(source_path),
        "snapshot_file": str(snapshot_path),
        "metadata_file": str(metadata_path),
        "file_found": True,
        "rows_before_filter": filtered.rows_before_filter,
        "rows_after_filter": filtered.rows_after_filter,
        "future_rows_excluded_count": filtered.future_rows_excluded_count,
        "rows_missing_availability_date_count": (
            filtered.rows_missing_availability_date_count
        ),
        "max_filing_date_after_filter": (
            filtered.max_filing_date_after_filter
        ),
        "max_accepted_date_after_filter": (
            filtered.max_accepted_date_after_filter
        ),
        "status": filtered.status,
        "warnings": warnings,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def _run_summary(manifest: dict) -> str:
    """Render the human-readable run summary."""
    blockers = manifest["promotion_blocking_categories"]
    snapshot = manifest["historical_snapshot_contract"]
    financials_contract = manifest.get("official_financials_as_of_contract") or {}
    financials_snapshot = manifest.get("official_financials_as_of_snapshot") or {}
    price_window = manifest.get("historical_price_window") or {}
    historical_assembly = (
        manifest.get("historical_enriched_input_assembly") or {}
    )
    historical_candidate = (
        manifest.get("historical_signal_readiness_candidate") or {}
    )
    capability_lines = [
        (
            f"- {item['section']}: {item['provider_name']} / "
            f"{item['enforcement_level']} / leakage {item['leakage_risk']}"
        )
        for item in snapshot["provider_capabilities"]
    ]
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
            f"- As-Of Date: {manifest.get('as_of_date') or 'Not provided'}",
            (
                "- Historical Mode: "
                f"{'enabled' if manifest['historical_mode'] else 'disabled'}"
            ),
            (
                "- Point-in-Time Enforcement: "
                f"{manifest['point_in_time_enforcement']}"
            ),
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
            *(
                [
                    "",
                    "## Historical Data Snapshot Contract",
                    "",
                    f"- As-Of Date: {snapshot['as_of_date']}",
                    f"- Snapshot Status: {snapshot['snapshot_status']}",
                    (
                        "- Point-in-Time Enforcement: "
                        f"{snapshot['point_in_time_enforcement']}"
                    ),
                    (
                        "- Supported Sections: "
                        f"{', '.join(snapshot['supported_sections']) or 'None'}"
                    ),
                    (
                        "- Unsupported Sections: "
                        f"{', '.join(snapshot['unsupported_sections']) or 'None'}"
                    ),
                    (
                        "- Leakage Risk Sections: "
                        f"{', '.join(snapshot['leakage_risk_sections']) or 'None'}"
                    ),
                    "",
                    "### Provider Capability Summary",
                    "",
                    *capability_lines,
                    "",
                    "### Warnings",
                    "",
                    *[f"- {warning}" for warning in snapshot["warnings"]],
                    "",
                    (
                        "This historical snapshot contract is not a "
                        "recommendation, ranking, vote, average score, consensus, "
                        "allocation instruction, rebalancing instruction, or "
                        "trade signal."
                    ),
                    "",
                    "## Official Financials As-Of Contract",
                    "",
                    f"- Provider: {financials_contract['provider_name']}",
                    (
                        "- Supports As-Of Date: "
                        f"{'Yes' if financials_contract['supports_as_of_date'] else 'No'}"
                    ),
                    (
                        "- Enforcement Level: "
                        f"{financials_contract['enforcement_level']}"
                    ),
                    f"- Leakage Risk: {financials_contract['leakage_risk']}",
                    (
                        "- Required Date Fields: "
                        f"{', '.join(financials_contract['required_date_fields'])}"
                    ),
                    (
                        "- Missing Date Fields: "
                        f"{', '.join(financials_contract['missing_date_fields']) or 'None'}"
                    ),
                    f"- Status: {financials_contract['status']}",
                    "",
                    *[
                        f"- Warning: {warning}"
                        for warning in financials_contract["warnings"]
                    ],
                    "",
                    (
                        "Official financials are not yet guaranteed point-in-time safe."
                        if not financials_contract["supports_as_of_date"]
                        else (
                            "Historical financials filtering is partial; source "
                            "provenance remains user-managed."
                        )
                    ),
                    (
                        "This official financials as-of contract is not a "
                        "recommendation, ranking, vote, average score, consensus, "
                        "allocation instruction, rebalancing instruction, or "
                        "trade signal."
                    ),
                    *(
                        [
                            "",
                            "## Official Financials As-Of Snapshot",
                            "",
                            f"- Provider: {financials_snapshot['provider']}",
                            f"- Source File: {financials_snapshot['source_file']}",
                            f"- Snapshot File: {financials_snapshot['snapshot_file']}",
                            (
                                "- Rows Before Filter: "
                                f"{financials_snapshot['rows_before_filter']}"
                            ),
                            (
                                "- Rows After Filter: "
                                f"{financials_snapshot['rows_after_filter']}"
                            ),
                            (
                                "- Future Rows Excluded: "
                                f"{financials_snapshot['future_rows_excluded_count']}"
                            ),
                            (
                                "- Rows Missing Availability Date: "
                                f"{financials_snapshot['rows_missing_availability_date_count']}"
                            ),
                            (
                                "- Max Filing Date After Filter: "
                                f"{financials_snapshot['max_filing_date_after_filter'] or 'None'}"
                            ),
                            (
                                "- Max Accepted Date After Filter: "
                                f"{financials_snapshot['max_accepted_date_after_filter'] or 'None'}"
                            ),
                            f"- Status: {financials_snapshot['status']}",
                            "",
                            (
                                "Historical financials CSV rows are filtered by "
                                "filing_date or accepted_date."
                            ),
                            (
                                "This official financials as-of snapshot is not a "
                                "recommendation, ranking, vote, average score, "
                                "consensus, allocation instruction, rebalancing "
                                "instruction, or trade signal."
                            ),
                        ]
                        if financials_snapshot.get("enabled")
                        else []
                    ),
                    "",
                    "## Historical Price Window",
                    "",
                    f"- As-Of Date: {manifest['as_of_date']}",
                    (
                        "- Analysis Price Window End Date: "
                        f"{price_window['analysis_window']['end_date']}"
                    ),
                    "- Future Prices Allowed in Analysis: No",
                    "- Outcome Prices Used for Backtest Only: Yes",
                    (
                        "- Enforcement Status: "
                        f"{manifest['market_price_window_enforcement']}"
                    ),
                    (
                        "- Leakage Policy Note: "
                        f"{price_window['analysis_window']['leakage_policy_note']}"
                    ),
                    "",
                    "Analysis inputs must not use prices after the as_of_date.",
                    (
                        "This historical price window enforcement is not a "
                        "recommendation, ranking, vote, average score, consensus, "
                        "allocation instruction, rebalancing instruction, or "
                        "trade signal."
                    ),
                    "",
                    "## Historical Enriched Input Assembly",
                    "",
                    (
                        "- Assembly Status: "
                        f"{historical_assembly['assembly_status']}"
                    ),
                    "- Safe for Historical Signal Generation: No",
                    (
                        "- Supported / Partial Sections: "
                        f"{', '.join(historical_assembly['supported_sections'] + historical_assembly['partial_sections']) or 'None'}"
                    ),
                    (
                        "- Readiness-Only Sections: "
                        f"{', '.join(historical_assembly['readiness_only_sections']) or 'None'}"
                    ),
                    (
                        "- Leakage Risk Sections: "
                        f"{', '.join(historical_assembly['leakage_risk_sections']) or 'None'}"
                    ),
                    (
                        "- Assembly File: "
                        f"{historical_assembly['assembly_file']}"
                    ),
                    "",
                    (
                        "Historical signal generation remains disabled until "
                        "sufficient point-in-time inputs are available."
                    ),
                    *[
                        f"- Warning: {warning}"
                        for warning in historical_assembly["warnings"]
                    ],
                    "",
                    "## Historical Signal Readiness Candidate",
                    "",
                    "- Signal Generation Status: readiness_only",
                    "- Safe for Historical Signal Generation: No",
                    (
                        "- Candidate File: "
                        f"{historical_candidate['candidate_file']}"
                    ),
                    (
                        "- Blocking Reasons Count: "
                        f"{historical_candidate['blocking_reasons_count']}"
                    ),
                    (
                        "- Leakage Risk Sections Count: "
                        f"{historical_candidate['leakage_risk_sections_count']}"
                    ),
                    "",
                    (
                        "Historical signal generation remains disabled until "
                        "sufficient point-in-time inputs are available."
                    ),
                    (
                        "Safety Notice: this candidate is a readiness-only "
                        "research artifact and is not an actionable signal."
                    ),
                    "",
                    "## Historical Analysis Warning",
                    "",
                    manifest["data_cutoff_note"],
                    manifest["leakage_warning"],
                    (
                        "Results must not be interpreted as a true historical "
                        "recommendation or trading signal."
                    ),
                ]
                if manifest["historical_mode"]
                else []
            ),
            "",
            "## Safety Note",
            "",
            (
                "This run summary is not a recommendation, ranking, vote, average "
                "score, consensus, allocation instruction, rebalancing instruction, "
                "or trade signal. Final investor decisions remain independent. "
                "Auto-promotion disabled."
            ),
            *(
                [
                    (
                        "This historical analysis readiness mode is not a "
                        "recommendation, ranking, vote, average score, consensus, "
                        "allocation instruction, rebalancing instruction, or "
                        "trade signal."
                    )
                ]
                if manifest["historical_mode"]
                else []
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
    as_of_context = build_as_of_context(intake.as_of_date)
    financials_snapshot = _create_official_financials_snapshot(
        intake=intake,
        run_folder=run_folder,
    )
    snapshot_contract = build_historical_snapshot_contract(
        intake.as_of_date,
        price_provider="fixture",
        input_mode=input_mode,
        fixtures_root=intake.fixtures_root,
        price_data_root=intake.fixtures_root,
        ticker=intake.ticker,
        financials_provider=intake.financials_provider,
        financials_root=intake.financials_root,
    )
    financials_contract = build_financials_as_of_contract(
        intake.as_of_date,
        fixtures_root=intake.fixtures_root,
        ticker=intake.ticker,
        provider_name=intake.financials_provider,
        financials_root=intake.financials_root,
    )
    analysis_window = (
        build_analysis_price_window(intake.as_of_date)
        if intake.as_of_date
        else None
    )
    historical_price_window = (
        {
            "analysis_window": analysis_window.to_dict(),
            "outcome_window_note": (
                "Outcome windows are only used by backtest evaluation, not by "
                "analysis inputs."
            ),
        }
        if analysis_window
        else None
    )
    assembly_json_path = (
        run_folder / "historical_enriched_input_assembly.json"
    )
    assembly_markdown_path = (
        run_folder / "historical_enriched_input_assembly.md"
    )
    candidate_json_path = (
        run_folder / "historical_signal_readiness_candidate.json"
    )
    candidate_markdown_path = (
        run_folder / "historical_signal_readiness_candidate.md"
    )
    if as_of_context.historical_mode:
        historical_assembly = build_historical_enriched_input_assembly(
            ticker=intake.ticker,
            as_of_date=as_of_context.as_of_date.isoformat(),
            run_id=run_id,
            point_in_time_enforcement=(
                as_of_context.point_in_time_enforcement
            ),
            historical_snapshot_contract=snapshot_contract.to_dict(),
            historical_price_window=historical_price_window,
            official_financials_snapshot=financials_snapshot,
            artifacts={
                "historical_snapshot_contract": (
                    f"{run_folder / 'run_manifest.json'}"
                    "#historical_snapshot_contract"
                ),
                "historical_price_window": (
                    f"{run_folder / 'run_manifest.json'}"
                    "#historical_price_window"
                ),
                **(
                    {
                        "official_financials_snapshot": (
                            financials_snapshot["snapshot_file"]
                        ),
                        "official_financials_snapshot_metadata": (
                            financials_snapshot["metadata_file"]
                        ),
                    }
                    if financials_snapshot.get("enabled")
                    else {}
                ),
            },
        )
        write_historical_enriched_input_assembly(
            historical_assembly,
            json_path=assembly_json_path,
            markdown_path=assembly_markdown_path,
        )
        historical_candidate = (
            build_historical_signal_readiness_candidate(
                historical_assembly,
                input_assembly_file=assembly_json_path,
            )
        )
        write_historical_signal_readiness_candidate(
            historical_candidate,
            json_path=candidate_json_path,
            markdown_path=candidate_markdown_path,
        )
        historical_assembly_manifest = {
            "enabled": True,
            "assembly_file": str(assembly_json_path),
            "assembly_markdown": str(assembly_markdown_path),
            "assembly_status": historical_assembly.assembly_status,
            "safe_for_historical_signal_generation": False,
            "supported_sections": historical_assembly.supported_sections,
            "partial_sections": historical_assembly.partial_sections,
            "readiness_only_sections": (
                historical_assembly.readiness_only_sections
            ),
            "leakage_risk_sections": (
                historical_assembly.leakage_risk_sections
            ),
            "warnings": historical_assembly.warnings,
        }
        historical_candidate_manifest = {
            "enabled": True,
            "candidate_file": str(candidate_json_path),
            "candidate_markdown": str(candidate_markdown_path),
            "signal_generation_status": (
                historical_candidate.signal_generation_status
            ),
            "safe_for_historical_signal_generation": False,
            "not_trade_signal": True,
            "not_recommendation": True,
            "blocking_reasons_count": len(
                historical_candidate.blocking_reasons
            ),
            "leakage_risk_sections_count": len(
                historical_candidate.leakage_risk_sections
            ),
            "warnings": historical_candidate.warnings,
        }
        readiness_metadata = build_readiness_metadata(
            manifest={
                "readiness_label": executive_summary.get(
                    "backoffice_readiness_label",
                    "Unknown",
                ),
                "readiness_status": historical_assembly.assembly_status,
                "source_verification_status": (
                    workflow_result.source_verification_status
                ),
                "promotion_blocking_categories": work_order_plan.get(
                    "promotion_blocking_categories",
                    [],
                ),
            },
            package_payload=package_payload,
            source_paths=[
                Path(workflow_result.broker_deal_package_path).with_suffix(
                    ".json"
                )
            ],
        )
        coverage_report = validate_historical_date_coverage(
            requested_dates=[str(intake.as_of_date)],
            tickers=[intake.ticker],
            price_root=intake.fixtures_root / "historical_price_history",
            financials_root=intake.financials_root,
        )
        coverage_quality = coverage_report.date_records[
            0
        ].ticker_coverage_quality[intake.ticker]
        readiness_metadata.update(coverage_quality)
        readiness_archive = append_historical_readiness_candidate(
            outputs_root=intake.outputs_root,
            candidate=historical_candidate,
            run_folder=run_folder,
            candidate_file=candidate_json_path,
            assembly_file=assembly_json_path,
            created_at=generated_at_text,
            metadata=readiness_metadata,
        )
        historical_readiness_ledger_record = {
            "archived": True,
            "ledger_jsonl": str(readiness_archive.jsonl_path),
            "ledger_csv": str(readiness_archive.csv_path),
            "latest_snapshot": str(readiness_archive.snapshot_path),
            "record_type": readiness_archive.record.record_type,
            "signal_generation_status": (
                readiness_archive.record.signal_generation_status
            ),
            "not_trade_signal": readiness_archive.record.not_trade_signal,
            "not_recommendation": readiness_archive.record.not_recommendation,
            "not_allocation_instruction": (
                readiness_archive.record.not_allocation_instruction
            ),
            "coverage_quality_label": (
                readiness_archive.record.coverage_quality_label
            ),
            "coverage_quality_severity": (
                readiness_archive.record.coverage_quality_severity
            ),
            "coverage_guardrail_status": (
                readiness_archive.record.coverage_guardrail_status
            ),
        }
    else:
        historical_assembly_manifest = {
            "enabled": False,
            "assembly_status": "not_enabled",
            "safe_for_historical_signal_generation": False,
            "warnings": [],
        }
        historical_candidate_manifest = {
            "enabled": False,
            "signal_generation_status": "not_enabled",
            "safe_for_historical_signal_generation": False,
            "not_trade_signal": True,
            "not_recommendation": True,
            "warnings": [],
        }
        historical_readiness_ledger_record = {
            "archived": False,
            "record_type": "historical_signal_readiness_candidate",
            "signal_generation_status": "not_enabled",
            "not_trade_signal": True,
            "not_recommendation": True,
            "not_allocation_instruction": True,
        }
    manifest = {
        "run_id": run_id,
        "ticker": intake.ticker,
        "company_name": (
            intake.company_name or workflow_result.company_name or None
        ),
        "input_mode": input_mode,
        "intake_file": str(intake_file) if intake_file else None,
        "run_label": intake.run_label,
        **as_of_context.to_dict(),
        "historical_snapshot_contract": snapshot_contract.to_dict(),
        "official_financials_as_of_contract": (
            financials_contract.to_dict() if intake.as_of_date else None
        ),
        "official_financials_as_of_snapshot": financials_snapshot,
        "historical_price_window": historical_price_window,
        "historical_enriched_input_assembly": (
            historical_assembly_manifest
        ),
        "historical_signal_readiness_candidate": (
            historical_candidate_manifest
        ),
        "historical_readiness_ledger_record": (
            historical_readiness_ledger_record
        ),
        "market_price_window_enforcement": (
            analysis_window.enforcement_status if analysis_window else None
        ),
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
