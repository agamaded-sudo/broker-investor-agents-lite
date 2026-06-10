"""Offline-safe broker deal workflow orchestration."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import yaml

from broker_agents.agents.bogle_agent import BogleAgent
from broker_agents.agents.buffett_agent import BuffettAgent
from broker_agents.agents.fisher_agent import FisherAgent
from broker_agents.agents.lynch_agent import LynchAgent
from broker_agents.agents.munger_agent import MungerAgent
from broker_agents.backoffice.enrichment_pipeline import (
    fixture_paths_for_known_ticker,
    run_backoffice_enrichment_pipeline,
)
from broker_agents.backoffice.portfolio_context import (
    load_portfolio_context,
    merge_portfolio_context_into_pack,
)
from broker_agents.backoffice.source_verification import verify_sources
from broker_agents.backoffice.source_verification_matrix import (
    summarize_source_verification_matrix,
)
from broker_agents.calculators.decision_candidates import (
    CURRENT_DECISIONS,
    build_decision_candidate,
)
from broker_agents.deals.investor_interest_response import (
    InvestorInterestResponse,
    derive_investor_interest_response,
)
from broker_agents.deals.deal_executive_summary import (
    build_broker_deal_executive_summary,
)
from broker_agents.reports.agents_summary_report import generate_agents_summary
from broker_agents.reports.backoffice_report import generate_backoffice_report
from broker_agents.reports.broker_deal_package_report import (
    generate_broker_deal_package_report,
)
from broker_agents.reports.investor_report import save_investor_report
from broker_agents.reports.investor_response_letter import (
    save_investor_response_letters,
)
from broker_agents.storage.file_paths import method_path

AGENT_SPECS = {
    "buffett": (BuffettAgent, "buffett_method.yaml", "Buffett"),
    "munger": (MungerAgent, "munger_method.yaml", "Munger"),
    "fisher": (FisherAgent, "fisher_method.yaml", "Fisher"),
    "lynch": (LynchAgent, "lynch_method.yaml", "Lynch"),
    "bogle": (BogleAgent, "bogle_method.yaml", "Bogle"),
}


@dataclass(frozen=True)
class BrokerDealWorkflowResult:
    """Paths and provenance produced by one broker deal workflow."""

    ticker: str
    company_name: str
    input_pack_path: Path
    enriched_pack_path: Path
    deal_output_dir: Path
    backoffice_report_path: Path
    source_verification_status: str
    investor_reports: dict[str, Path]
    investor_summary_path: Path
    investor_response_letter_paths: dict[str, Path]
    broker_deal_package_path: Path
    applied_enrichment_sources: list[str]
    skipped_enrichment_sources: list[str]
    warnings: list[str]
    safety_flags: list[str]

    def to_dict(self) -> dict:
        """Serialize paths and workflow metadata to JSON-compatible values."""
        data = asdict(self)
        for key in (
            "input_pack_path",
            "enriched_pack_path",
            "deal_output_dir",
            "backoffice_report_path",
            "investor_summary_path",
            "broker_deal_package_path",
        ):
            data[key] = str(data[key])
        data["investor_reports"] = {
            name: str(path) for name, path in self.investor_reports.items()
        }
        data["investor_response_letter_paths"] = {
            name: str(path)
            for name, path in self.investor_response_letter_paths.items()
        }
        return data


def _load_yaml(path: Path) -> dict:
    """Load a required YAML pack with clear local errors."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Deal input pack not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid deal input YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Deal input YAML must contain a mapping: {path}")
    return data


def _merge_portfolio_context(pack: dict, path: Path | None) -> dict:
    """Merge optional broker-supplied portfolio context for Bogle analysis."""
    if path is None:
        return pack
    context = load_portfolio_context(path)
    return merge_portfolio_context_into_pack(pack, context)


def _source_status(pack: dict) -> str:
    """Build a compact source-verification status."""
    verification = verify_sources(pack)
    return (
        f"{verification['source_verification_status']} "
        f"({verification['overall_source_quality']})"
    )


def _generate_investor_outputs(
    pack: dict,
    ticker: str,
    company_name: str,
    output_dir: Path,
) -> tuple[dict[str, Path], Path, list[InvestorInterestResponse]]:
    """Run all independent agents and create their summary and interest responses."""
    output_dir.mkdir(parents=True, exist_ok=True)
    lower = ticker.lower()
    report_paths: dict[str, Path] = {}
    responses: list[InvestorInterestResponse] = []
    for agent_key, (agent_class, method_filename, investor_label) in AGENT_SPECS.items():
        agent = agent_class(pack, method_path(method_filename))
        report_text = agent.generate_report()
        report_path = output_dir / f"{lower}_{agent_key}_report.md"
        save_investor_report(report_text, report_path)
        report_paths[agent_key] = report_path
        candidate = build_decision_candidate(pack, agent_key)
        responses.append(
            derive_investor_interest_response(
                ticker=ticker,
                investor=investor_label,
                final_decision=CURRENT_DECISIONS[agent_key],
                candidate_decision=candidate["candidate_decision"],
                report_text=report_text,
                pack=pack,
            )
        )

    summary_path = output_dir / f"{lower}_agents_summary.md"
    summary_path.write_text(
        generate_agents_summary(company_name, ticker, report_paths),
        encoding="utf-8",
    )
    return report_paths, summary_path, responses


def run_broker_deal_workflow(
    ticker: str,
    input_pack_path: Path,
    outputs_root: Path,
    fixtures_root: Path,
    portfolio_context_path: Path | None = None,
) -> BrokerDealWorkflowResult:
    """Run Backoffice enrichment, independent agents, and broker packaging."""
    ticker_upper = ticker.strip().upper()
    if not ticker_upper:
        raise ValueError("Ticker must not be empty.")
    input_pack_path = Path(input_pack_path)
    outputs_root = Path(outputs_root)
    fixtures_root = Path(fixtures_root)
    input_pack = _load_yaml(input_pack_path)
    input_ticker = str(input_pack.get("company_identity", {}).get("ticker") or "").upper()
    if input_ticker and input_ticker != ticker_upper:
        raise ValueError(
            f"Ticker mismatch: requested {ticker_upper}, input pack contains {input_ticker}."
        )

    lower = ticker_upper.lower()
    deal_dir = outputs_root / ticker_upper / "deal_package"
    enriched_path = deal_dir / f"{lower}_deal_enriched_input.yaml"
    fixture_paths = fixture_paths_for_known_ticker(ticker_upper, fixtures_root)
    enrichment = run_backoffice_enrichment_pipeline(
        input_pack_path,
        enriched_path,
        **fixture_paths,
    )
    enriched_pack = _load_yaml(enriched_path)
    analysis_pack = _merge_portfolio_context(
        enriched_pack,
        Path(portfolio_context_path) if portfolio_context_path else None,
    )
    identity = analysis_pack.get("company_identity", {})
    metadata = analysis_pack.get("metadata", {})
    company_name = str(
        identity.get("company_name")
        or metadata.get("company_name")
        or "Unknown company"
    )

    backoffice_path = deal_dir / f"{lower}_backoffice_data_pack.md"
    backoffice_path.write_text(
        generate_backoffice_report(analysis_pack),
        encoding="utf-8",
    )
    investor_output_dir = deal_dir / "investor_outputs"
    investor_reports, summary_path, responses = _generate_investor_outputs(
        analysis_pack,
        ticker_upper,
        company_name,
        investor_output_dir,
    )
    response_letter_dir = deal_dir / "investor_response_letters"
    response_letter_paths = save_investor_response_letters(
        ticker_upper,
        company_name,
        responses,
        response_letter_dir,
    )
    letters_by_investor = {
        response.investor: path
        for response, path in zip(responses, response_letter_paths, strict=True)
    }
    source_status = _source_status(enriched_pack)
    source_matrix = summarize_source_verification_matrix(analysis_pack)
    warnings = list(enrichment.warnings)
    executive_summary = build_broker_deal_executive_summary(
        ticker=ticker_upper,
        company_name=company_name,
        investor_responses=responses,
        source_verification_status=source_status,
        applied_enrichment_sources=enrichment.applied_sources,
        skipped_enrichment_sources=enrichment.skipped_sources,
        warnings=warnings,
    )
    package_path = deal_dir / f"{lower}_broker_deal_package.md"
    package_path.write_text(
        generate_broker_deal_package_report(
            ticker=ticker_upper,
            company_name=company_name,
            enriched_pack_path=enriched_path,
            investor_responses=responses,
            source_verification_status=source_status,
            applied_enrichment_sources=enrichment.applied_sources,
            skipped_enrichment_sources=enrichment.skipped_sources,
            warnings=warnings,
            executive_summary=executive_summary,
            investor_response_letter_paths=letters_by_investor,
            source_verification_summary=source_matrix.to_dict(),
        ),
        encoding="utf-8",
    )
    safety_flags = [
        "not_a_recommendation",
        "no_ranking",
        "no_consensus",
        "no_portfolio_allocation",
        "no_trade_execution",
        "no_auto_promotion",
        "final_decisions_unchanged",
    ]
    result = BrokerDealWorkflowResult(
        ticker=ticker_upper,
        company_name=company_name,
        input_pack_path=input_pack_path,
        enriched_pack_path=enriched_path,
        deal_output_dir=deal_dir,
        backoffice_report_path=backoffice_path,
        source_verification_status=source_status,
        investor_reports=investor_reports,
        investor_summary_path=summary_path,
        investor_response_letter_paths=letters_by_investor,
        broker_deal_package_path=package_path,
        applied_enrichment_sources=enrichment.applied_sources,
        skipped_enrichment_sources=enrichment.skipped_sources,
        warnings=warnings,
        safety_flags=safety_flags,
    )
    json_path = deal_dir / f"{lower}_broker_deal_package.json"
    json_path.write_text(
        json.dumps(
            {
                "workflow_result": result.to_dict(),
                "investor_responses": [response.to_dict() for response in responses],
                "executive_summary": executive_summary.to_dict(),
                "source_verification_matrix": source_matrix.to_dict(),
                "safety_flags": safety_flags,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return result
