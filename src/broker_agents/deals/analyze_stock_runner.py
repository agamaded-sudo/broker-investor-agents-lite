"""Reusable execution service for single-stock analysis runs."""

from dataclasses import dataclass
import json
from pathlib import Path

import yaml

from broker_agents.deals.analyze_stock_intake import AnalyzeStockIntake
from broker_agents.deals.broker_deal_workflow import (
    BrokerDealWorkflowResult,
    run_broker_deal_workflow,
)
from broker_agents.deals.deal_intake import (
    DealIntakeStatus,
    build_deal_intake_status,
)
from broker_agents.deals.run_bundle import (
    AnalyzeStockRunBundle,
    create_analyze_stock_run_bundle,
)
from broker_agents.reports.deal_intake_report import generate_deal_intake_report


@dataclass(frozen=True)
class AnalyzeStockExecutionResult:
    """Complete result of one analyze-stock pipeline execution."""

    intake: AnalyzeStockIntake
    input_mode: str
    intake_file: Path | None
    intake_status: DealIntakeStatus
    intake_report_path: Path
    intake_json_path: Path
    intake_snapshot_path: Path
    workflow_result: BrokerDealWorkflowResult
    package_payload: dict
    run_bundle: AnalyzeStockRunBundle
    investor_response_letters_dir: Path
    investor_follow_up_memos_dir: Path


def execute_analyze_stock(
    *,
    intake: AnalyzeStockIntake,
    input_mode: str,
    intake_file: Path | None = None,
) -> AnalyzeStockExecutionResult:
    """Run intake, the existing deal workflow, and run-bundle archiving."""
    status = build_deal_intake_status(
        ticker=intake.ticker,
        examples_root=intake.examples_root,
        outputs_root=intake.outputs_root,
        fixtures_root=intake.fixtures_root,
        portfolio_context_path=intake.portfolio_context,
        market=intake.market,
        company_name=intake.company_name,
    )
    normalized = status.normalized_ticker or "UNKNOWN"
    intake_dir = intake.outputs_root / normalized
    intake_report_path = intake_dir / "deal_intake_report.md"
    intake_json_path = intake_dir / "deal_intake_report.json"
    intake_dir.mkdir(parents=True, exist_ok=True)
    intake_report_path.write_text(
        generate_deal_intake_report(status),
        encoding="utf-8",
    )
    intake_json_path.write_text(
        json.dumps(status.to_dict(), indent=2),
        encoding="utf-8",
    )
    if not status.can_run_deal:
        raise ValueError(
            f"{normalized} cannot run the deal workflow: {status.intake_status}. "
            f"Review {intake_report_path}."
        )

    workflow_result = run_broker_deal_workflow(
        ticker=normalized,
        input_pack_path=status.manual_input_path,
        outputs_root=intake.outputs_root,
        fixtures_root=intake.fixtures_root,
        portfolio_context_path=intake.portfolio_context,
    )
    package_json_path = (
        workflow_result.deal_output_dir
        / f"{normalized.lower()}_broker_deal_package.json"
    )
    package_payload = json.loads(
        package_json_path.read_text(encoding="utf-8")
    )
    snapshot_filename = (
        "analyze_stock_intake_snapshot.yaml"
        if input_mode == "intake_file"
        else "analyze_stock_ticker_snapshot.yaml"
    )
    intake_snapshot_path = (
        workflow_result.deal_output_dir / snapshot_filename
    )
    intake_snapshot_path.write_text(
        yaml.safe_dump(
            intake.to_snapshot(
                input_mode=input_mode,
                intake_file=intake_file,
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    run_bundle = create_analyze_stock_run_bundle(
        intake=intake,
        input_mode=input_mode,
        intake_file=intake_file,
        intake_snapshot_path=intake_snapshot_path,
        workflow_result=workflow_result,
        package_payload=package_payload,
    )
    letter_dir = next(
        iter(workflow_result.investor_response_letter_paths.values())
    ).parent
    memo_dir = next(
        iter(workflow_result.investor_follow_up_memo_paths.values())
    ).parent
    return AnalyzeStockExecutionResult(
        intake=intake,
        input_mode=input_mode,
        intake_file=intake_file,
        intake_status=status,
        intake_report_path=intake_report_path,
        intake_json_path=intake_json_path,
        intake_snapshot_path=intake_snapshot_path,
        workflow_result=workflow_result,
        package_payload=package_payload,
        run_bundle=run_bundle,
        investor_response_letters_dir=letter_dir,
        investor_follow_up_memos_dir=memo_dir,
    )
