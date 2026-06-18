"""Command-line entry points for broker investor agents."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.table import Table

from broker_agents.backoffice.data_validator import validate_backoffice_pack
from broker_agents.backoffice.enrichment_pipeline import (
    fixture_paths_for_known_ticker,
    run_backoffice_enrichment_pipeline,
)
from broker_agents.backoffice.gap_detector import detect_basic_gaps
from broker_agents.backoffice.growth_peg_mapper import merge_growth_peg_into_pack
from broker_agents.backoffice.historical_valuation_mapper import (
    merge_historical_valuation_into_pack,
)
from broker_agents.backoffice.market_data_mapper import merge_market_data_into_pack
from broker_agents.backoffice.official_financials_mapper import (
    merge_official_financials_into_pack,
)
from broker_agents.backoffice.portfolio_context import (
    load_portfolio_context,
    merge_portfolio_context_into_pack,
)
from broker_agents.backoffice.research_audit_trail_bundle import (
    write_research_audit_trail_bundle_report,
)
from broker_agents.regate.re_run_re_gate_plan import (
    write_re_run_re_gate_plan_report,
)
from broker_agents.regate.re_run_input_package import (
    write_re_run_input_package_report,
)
from broker_agents.regate.controlled_re_run_trial import (
    write_controlled_re_run_trial_report,
)
from broker_agents.regate.pre_post_repair_comparison import (
    write_pre_post_repair_comparison_report,
)
from broker_agents.regate.gatekeeper_re_evaluation import (
    write_gatekeeper_re_evaluation_report,
)
from broker_agents.regate.phase_16_closure import (
    write_phase_16_closure_report,
)
from broker_agents.stabilization.targeted_evidence_stabilization_plan import (
    write_targeted_evidence_stabilization_plan_report,
)
from broker_agents.stabilization.residual_blocker_work_orders import (
    write_residual_blocker_work_order_report,
)
from broker_agents.stabilization.targeted_evidence_repairs import (
    write_targeted_evidence_repairs_report,
)
from broker_agents.stabilization.stabilization_validation_trial import (
    write_stabilization_validation_trial_report,
)
from broker_agents.agents.bogle_agent import BogleAgent
from broker_agents.agents.buffett_agent import BuffettAgent
from broker_agents.agents.fisher_agent import FisherAgent
from broker_agents.agents.lynch_agent import LynchAgent
from broker_agents.agents.munger_agent import MungerAgent
from broker_agents.archive.signal_ledger import archive_completed_run
from broker_agents.backtesting.clean_coverage_before_after_report import (
    find_latest_clean_coverage_runs,
    write_clean_coverage_comparison_report,
)
from broker_agents.backtesting.backoffice_evidence_quality_attribution import (
    write_backoffice_evidence_quality_report,
)
from broker_agents.backtesting.backtest_driver_decomposition import (
    write_backtest_driver_decomposition_report,
)
from broker_agents.backtesting.outlier_repair_path import (
    write_outlier_repair_path_report,
)
from broker_agents.backtesting.walk_forward_repair_plan import (
    write_walk_forward_repair_plan_report,
)
from broker_agents.backtesting.delayed_anchor_repair import (
    write_delayed_anchor_repair_report,
)
from broker_agents.backtesting.metadata_diversity_recheck import (
    write_metadata_diversity_recheck_report,
)
from broker_agents.backtesting.evidence_decision_gate import (
    find_latest_evidence_gate_backtest,
    write_evidence_decision_gate_report,
)
from broker_agents.backtesting.expanded_ticker_coverage_output_validator import (
    load_latest_expanded_ticker_coverage_manifest,
    write_expanded_ticker_coverage_output_validation_report,
)
from broker_agents.backtesting.expanded_trial_results_analyzer import (
    write_expanded_trial_analysis_report,
)
from broker_agents.backtesting.investor_persona_attribution import (
    write_investor_persona_attribution_report,
)
from broker_agents.backtesting.signal_backtester import run_signal_backtest
from broker_agents.backtesting.readiness_trial_decision_report import (
    regenerate_readiness_trial_decision_report,
)
from broker_agents.backtesting.readiness_trial_diagnostic_report import (
    regenerate_readiness_trial_diagnostic_report,
)
from broker_agents.backtesting.readiness_trial_export import (
    export_readiness_ledger_to_trial_ledger,
    validate_readiness_trial_ledger,
)
from broker_agents.backtesting.research_evidence_scorecard import (
    write_research_evidence_scorecard_report,
)
from broker_agents.backtesting.research_gatekeeper import (
    write_research_gatekeeper_report,
)
from broker_agents.data_providers.price_csv_validation import (
    validate_price_csvs,
)
from broker_agents.data_providers.price_provider import create_price_provider
from broker_agents.deals.analyze_stock_intake import (
    build_ticker_analyze_stock_intake,
    load_analyze_stock_intake,
    with_as_of_date,
    with_financials_provider,
)
from broker_agents.deals.expanded_ticker_coverage import (
    write_expanded_ticker_coverage_report,
)
from broker_agents.deals.expanded_ticker_readiness_trial import (
    run_expanded_ticker_readiness_trial,
)
from broker_agents.deals.historical_date_coverage import (
    resolve_historical_date_preset,
)
from broker_agents.deals.readiness_metadata_enrichment import (
    ENRICHMENT_FIELDS,
)
from broker_agents.historical.as_of_context import build_as_of_context
from broker_agents.personas.persona_evidence_pack_requirements import (
    write_persona_evidence_pack_requirements_report,
)
from broker_agents.personas.bogle_benchmark_index_pack import (
    write_bogle_benchmark_index_pack_report,
)
from broker_agents.personas.fisher_qualitative_growth_pack import (
    write_fisher_qualitative_growth_pack_report,
)
from broker_agents.personas.buffett_munger_quality_risk_pack import (
    write_buffett_munger_quality_risk_pack_report,
)
from broker_agents.historical.financials_as_of_contract import (
    build_financials_as_of_contract,
)
from broker_agents.historical.historical_financials import (
    filter_financials_as_of,
    historical_financials_path,
    load_historical_financials_csv,
    validate_historical_financials_csv,
)
from broker_agents.historical.historical_signal_readiness import (
    HistoricalSignalReadinessCandidate,
)
from broker_agents.historical.price_windows import (
    build_analysis_price_window,
)
from broker_agents.historical.snapshot_contract import (
    build_historical_snapshot_contract,
)
from broker_agents.deals.analyze_stock_runner import execute_analyze_stock
from broker_agents.deals.batch_analyze import (
    BatchTickerResult,
    completed_batch_result,
    create_analyze_batch_bundle,
    failed_batch_result,
)
from broker_agents.deals.historical_readiness_batch import (
    run_historical_readiness_batch,
)
from broker_agents.deals.historical_readiness_multidate import (
    run_historical_readiness_multidate,
)
from broker_agents.deals.deal_intake import build_deal_intake_status
from broker_agents.fetchers.sec_financials_fetcher import (
    load_sec_fixture,
    map_fixture_to_financials,
)
from broker_agents.fetchers.market_data_fetcher import (
    MarketDataFetcher,
    load_market_data_fixture,
)
from broker_agents.fetchers.historical_valuation_fetcher import (
    HistoricalValuationFetcher,
    load_historical_valuation_fixture,
)
from broker_agents.fetchers.growth_peg_fetcher import (
    GrowthPegFetcher,
    load_growth_peg_fixture,
)
from broker_agents.deals.broker_deal_workflow import run_broker_deal_workflow
from broker_agents.reports.backoffice_report import generate_backoffice_report
from broker_agents.reports.backoffice_missing_evidence_report import (
    generate_backoffice_missing_evidence_report,
)
from broker_agents.reports.agents_summary_report import generate_agents_summary
from broker_agents.reports.agents_comparison_report import generate_agents_comparison
from broker_agents.reports.decision_candidate_audit_report import (
    generate_decision_candidate_audit,
)
from broker_agents.reports.deal_intake_report import generate_deal_intake_report
from broker_agents.reports.enrichment_pipeline_summary import (
    generate_enrichment_pipeline_summary,
)
from broker_agents.reports.investor_report import save_investor_report
from broker_agents.reports.human_review_queue_report import (
    generate_human_review_queue_report,
)
from broker_agents.reports.manual_vs_enriched_comparison import (
    generate_manual_vs_enriched_comparison,
)
from broker_agents.reports.post_enrichment_gap_report import (
    generate_post_enrichment_gap_report,
)
from broker_agents.reports.portfolio_manager_readiness_report import (
    generate_portfolio_manager_readiness_report,
)
from broker_agents.reports.investor_agent_readiness_dashboard import (
    generate_investor_agent_readiness_dashboard,
)
from broker_agents.reports.multi_company_comparison_report import (
    generate_multi_company_comparison,
)
from broker_agents.reports.report_quality_review import review_generated_reports
from broker_agents.reports.source_verification_report import (
    generate_source_verification_report,
)
from broker_agents.review.human_review_queue import generate_human_review_queue
from broker_agents.portfolio.portfolio_manager_readiness import (
    generate_portfolio_readiness_items,
)
from broker_agents.storage.file_paths import method_path, output_dir_for_ticker

app = typer.Typer(help="Broker investor agents utilities.")
console = Console()

AGENT_SPECS = {
    "buffett": (BuffettAgent, "buffett_method.yaml"),
    "munger": (MungerAgent, "munger_method.yaml"),
    "fisher": (FisherAgent, "fisher_method.yaml"),
    "lynch": (LynchAgent, "lynch_method.yaml"),
    "bogle": (BogleAgent, "bogle_method.yaml"),
}


@app.callback()
def broker_agents() -> None:
    """Broker investor agents command group."""


def _load_yaml(path: Path) -> dict:
    """Load a YAML file as a dictionary."""
    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
    except FileNotFoundError as exc:
        raise typer.BadParameter(f"YAML file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise typer.BadParameter(f"Invalid YAML in {path}: {exc}") from exc
    except OSError as exc:
        raise typer.BadParameter(f"Could not read YAML file {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise typer.BadParameter(f"YAML file must contain a mapping at the top level: {path}")

    return data


def _build_agent(agent_name: str, pack: dict):
    """Build a supported deterministic investor agent."""
    try:
        agent_class, method_filename = AGENT_SPECS[agent_name]
    except KeyError as exc:
        supported = ", ".join(AGENT_SPECS)
        raise typer.BadParameter(
            f"Unsupported agent. Currently supported agents are: {supported}."
        ) from exc

    return agent_class(pack=pack, method_path=method_path(method_filename))


def _merge_optional_portfolio_context(pack: dict, context_path: Path | None) -> dict:
    """Merge optional portfolio context into a pack with CLI-friendly errors."""
    if context_path is None:
        return pack
    try:
        context = load_portfolio_context(context_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise typer.BadParameter(
            f"Could not load portfolio context {context_path}: {exc}"
        ) from exc
    return merge_portfolio_context_into_pack(pack, context)


def run_all_agent_reports(pack: dict, output_dir: Path) -> list[dict[str, str]]:
    """Generate and save reports for all supported investor agents."""
    company_identity = pack.get("company_identity", {})
    metadata = pack.get("metadata", {})
    ticker = str(company_identity.get("ticker") or metadata.get("ticker") or "company").lower()
    results: list[dict[str, str]] = []

    for agent_name in AGENT_SPECS:
        output_path = Path(output_dir) / f"{ticker}_{agent_name}_report.md"
        investor_agent = _build_agent(agent_name, pack)
        save_investor_report(investor_agent.generate_report(), output_path)
        results.append(
            {
                "agent": agent_name,
                "output_file": str(output_path),
                "status": "written",
            }
        )

    return results


def run_full_pipeline(pack: dict, output_dir: Path) -> list[dict[str, str]]:
    """Run the full deterministic reporting pipeline."""
    output_dir = Path(output_dir)
    company_identity = pack.get("company_identity", {})
    metadata = pack.get("metadata", {})
    ticker = str(company_identity.get("ticker") or metadata.get("ticker") or "company")
    ticker_lower = ticker.lower()
    company_name = str(
        company_identity.get("company_name") or metadata.get("company_name") or "Unknown company"
    )

    results: list[dict[str, str]] = []
    validation_messages = validate_backoffice_pack(pack)
    validation_status = "valid" if not validation_messages else "warnings"

    backoffice_path = output_dir / f"{ticker_lower}_backoffice_data_pack.md"
    backoffice_report = generate_backoffice_report(pack)
    backoffice_path.parent.mkdir(parents=True, exist_ok=True)
    backoffice_path.write_text(backoffice_report, encoding="utf-8")
    results.append(
        {
            "artifact": "backoffice",
            "output_file": str(backoffice_path),
            "status": validation_status,
        }
    )

    agent_results = run_all_agent_reports(pack, output_dir)
    results.extend(
        {
            "artifact": result["agent"],
            "output_file": result["output_file"],
            "status": result["status"],
        }
        for result in agent_results
    )

    report_paths = {
        agent_name: output_dir / f"{ticker_lower}_{agent_name}_report.md"
        for agent_name in AGENT_SPECS
    }
    summary_path = output_dir / f"{ticker_lower}_agents_summary.md"
    summary = generate_agents_summary(company_name, ticker, report_paths)
    summary_path.write_text(summary, encoding="utf-8")
    results.append(
        {
            "artifact": "agents_summary",
            "output_file": str(summary_path),
            "status": "written",
        }
    )

    return results


def run_enriched_pipeline_reports(
    pack: dict,
    output_dir: Path,
) -> list[dict[str, str]]:
    """Run the full pipeline plus its deterministic quality review."""
    results = run_full_pipeline(pack, output_dir)
    identity = pack.get("company_identity", {})
    metadata = pack.get("metadata", {})
    ticker = str(identity.get("ticker") or metadata.get("ticker") or "company")
    ticker_lower = ticker.lower()
    report_paths = {
        "backoffice": output_dir / f"{ticker_lower}_backoffice_data_pack.md",
        **{
            agent_name: output_dir / f"{ticker_lower}_{agent_name}_report.md"
            for agent_name in AGENT_SPECS
        },
        "agents_summary": output_dir / f"{ticker_lower}_agents_summary.md",
    }
    review_path = output_dir / f"{ticker_lower}_reports_quality_review.md"
    review_path.write_text(review_generated_reports(report_paths), encoding="utf-8")
    results.append(
        {
            "artifact": "reports_quality_review",
            "output_file": str(review_path),
            "status": "written",
        }
    )
    return results


@app.command("validate-pack")
def validate_pack(
    input_path: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to a YAML backoffice data pack.",
        ),
    ] = Path("examples/msft_input.yaml"),
) -> None:
    """Validate a local backoffice data pack and report basic gaps."""
    pack = _load_yaml(input_path)
    validation_messages = validate_backoffice_pack(pack)
    gaps = detect_basic_gaps(pack)

    console.print(f"[bold]Validation results for:[/bold] {input_path}")
    if validation_messages:
        for message in validation_messages:
            console.print(f"[red]- {message}[/red]")
    else:
        console.print("[green]No validation issues found.[/green]")

    gap_table = Table(title="Basic Gaps")
    gap_table.add_column("Gap")
    gap_table.add_column("Priority")
    gap_table.add_column("Investor Relevance")

    for gap in gaps:
        gap_table.add_row(
            str(gap["gap_name"]),
            str(gap["priority"]),
            str(gap["investor_relevance"]),
        )

    if gaps:
        console.print(gap_table)
    else:
        console.print("[green]No basic gaps detected.[/green]")


def _write_enrichment_summary(result, summary_output: Path | None) -> None:
    """Write and print an optional enrichment summary."""
    if summary_output is None:
        return
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.write_text(
        generate_enrichment_pipeline_summary(result),
        encoding="utf-8",
    )
    console.print(f"[bold]Enrichment summary written to:[/bold] {summary_output}")


@app.command("enrich-pack")
def enrich_pack(
    input_path: Annotated[
        Path,
        typer.Option("--input", "-i", exists=True, readable=True),
    ],
    output_path: Annotated[
        Path,
        typer.Option("--output", "-o", file_okay=True, dir_okay=False),
    ],
    sec_fixture_path: Annotated[
        Path | None,
        typer.Option("--sec-fixture", file_okay=True, dir_okay=False),
    ] = None,
    market_fixture_path: Annotated[
        Path | None,
        typer.Option("--market-fixture", file_okay=True, dir_okay=False),
    ] = None,
    historical_fixture_path: Annotated[
        Path | None,
        typer.Option("--historical-valuation-fixture", file_okay=True, dir_okay=False),
    ] = None,
    growth_fixture_path: Annotated[
        Path | None,
        typer.Option("--growth-peg-fixture", file_okay=True, dir_okay=False),
    ] = None,
    summary_output: Annotated[
        Path | None,
        typer.Option("--summary-output", file_okay=True, dir_okay=False),
    ] = None,
) -> None:
    """Apply explicitly selected offline fixtures to a Backoffice pack."""
    try:
        result = run_backoffice_enrichment_pipeline(
            input_path=input_path,
            output_path=output_path,
            sec_fixture_path=sec_fixture_path,
            market_fixture_path=market_fixture_path,
            historical_valuation_fixture_path=historical_fixture_path,
            growth_peg_fixture_path=growth_fixture_path,
        )
        _write_enrichment_summary(result, summary_output)
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(f"Could not enrich Backoffice pack: {exc}") from exc
    console.print(f"[bold]Enriched pack written to:[/bold] {result.output_path}")


@app.command("enrich-known-ticker")
def enrich_known_ticker(
    ticker: Annotated[str, typer.Option("--ticker")] = "MSFT",
    input_path: Annotated[
        Path,
        typer.Option("--input", "-i", exists=True, readable=True),
    ] = Path("examples/msft_input.yaml"),
    output_path: Annotated[
        Path,
        typer.Option("--output", "-o", file_okay=True, dir_okay=False),
    ] = Path("data/outputs/MSFT/msft_enriched_input.yaml"),
    fixtures_root: Annotated[
        Path,
        typer.Option("--fixtures-root", exists=True, file_okay=False, readable=True),
    ] = Path("tests/fixtures"),
    summary_output: Annotated[
        Path | None,
        typer.Option("--summary-output", file_okay=True, dir_okay=False),
    ] = Path("data/outputs/MSFT/msft_enrichment_summary.md"),
) -> None:
    """Enrich one known ticker using convention-based fixture names."""
    fixture_paths = fixture_paths_for_known_ticker(ticker, fixtures_root)
    try:
        result = run_backoffice_enrichment_pipeline(
            input_path=input_path,
            output_path=output_path,
            **fixture_paths,
        )
        _write_enrichment_summary(result, summary_output)
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(f"Could not enrich known ticker {ticker}: {exc}") from exc
    console.print(f"[bold]Enriched pack written to:[/bold] {result.output_path}")


@app.command("enrich-known-tickers")
def enrich_known_tickers(
    tickers: Annotated[
        str,
        typer.Option("--tickers", help="Comma-separated ticker symbols."),
    ] = "MSFT,AAPL,NVDA",
    examples_root: Annotated[
        Path,
        typer.Option("--examples-root", exists=True, file_okay=False, readable=True),
    ] = Path("examples"),
    outputs_root: Annotated[
        Path,
        typer.Option("--outputs-root", file_okay=False),
    ] = Path("data/outputs"),
    fixtures_root: Annotated[
        Path,
        typer.Option("--fixtures-root", exists=True, file_okay=False, readable=True),
    ] = Path("tests/fixtures"),
) -> None:
    """Enrich multiple known tickers using the standard project layout."""
    parsed = [ticker.strip().upper() for ticker in tickers.split(",") if ticker.strip()]
    if not parsed:
        raise typer.BadParameter("At least one ticker must be provided.")

    table = Table(title="Backoffice Enrichment Results")
    table.add_column("Ticker")
    table.add_column("Applied")
    table.add_column("Skipped")
    table.add_column("Output")
    for ticker in parsed:
        ticker_lower = ticker.lower()
        input_path = examples_root / f"{ticker_lower}_input.yaml"
        output_dir = outputs_root / ticker
        output_path = output_dir / f"{ticker_lower}_enriched_input.yaml"
        summary_path = output_dir / f"{ticker_lower}_enrichment_summary.md"
        try:
            result = run_backoffice_enrichment_pipeline(
                input_path=input_path,
                output_path=output_path,
                **fixture_paths_for_known_ticker(ticker, fixtures_root),
            )
            _write_enrichment_summary(result, summary_path)
        except (OSError, ValueError) as exc:
            raise typer.BadParameter(
                f"Could not enrich known ticker {ticker}: {exc}"
            ) from exc
        table.add_row(
            ticker,
            ", ".join(result.applied_sources) or "None",
            ", ".join(result.skipped_sources) or "None",
            str(result.output_path),
        )
    console.print(table)


@app.command("merge-sec-fixture")
def merge_sec_fixture(
    input_path: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Existing manual Backoffice YAML pack.",
        ),
    ],
    fixture_path: Annotated[
        Path,
        typer.Option(
            "--fixture",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Compact SEC company-facts JSON fixture.",
        ),
    ],
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Path where the merged YAML pack should be written.",
        ),
    ],
) -> None:
    """Merge offline SEC fixture financials into a copy of a manual pack."""
    pack = _load_yaml(input_path)
    try:
        fixture = load_sec_fixture(fixture_path)
        financials = map_fixture_to_financials(fixture)
        merged = merge_official_financials_into_pack(pack, financials)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            yaml.safe_dump(merged, sort_keys=False, allow_unicode=False),
            encoding="utf-8",
        )
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(
            f"Could not merge SEC fixture {fixture_path}: {exc}"
        ) from exc

    console.print(f"[bold]SEC fixture merge written to:[/bold] {output_path}")


@app.command("merge-market-fixture")
def merge_market_fixture(
    input_path: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Existing manual Backoffice YAML pack.",
        ),
    ],
    fixture_path: Annotated[
        Path,
        typer.Option(
            "--fixture",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Compact market-data JSON fixture.",
        ),
    ],
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Path where the merged YAML pack should be written.",
        ),
    ],
) -> None:
    """Merge offline market fixture data into a copy of a manual pack."""
    pack = _load_yaml(input_path)
    try:
        fixture = load_market_data_fixture(fixture_path)
        market_data = MarketDataFetcher().map_fixture_to_market_data(fixture)
        merged = merge_market_data_into_pack(pack, market_data)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            yaml.safe_dump(merged, sort_keys=False, allow_unicode=False),
            encoding="utf-8",
        )
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(
            f"Could not merge market fixture {fixture_path}: {exc}"
        ) from exc

    console.print(f"[bold]Market fixture merge written to:[/bold] {output_path}")


@app.command("merge-historical-valuation-fixture")
def merge_historical_valuation_fixture(
    input_path: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Existing manual Backoffice YAML pack.",
        ),
    ],
    fixture_path: Annotated[
        Path,
        typer.Option(
            "--fixture",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Compact historical valuation JSON fixture.",
        ),
    ],
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Path where the merged YAML pack should be written.",
        ),
    ],
) -> None:
    """Merge offline historical valuation fixture data into a pack copy."""
    pack = _load_yaml(input_path)
    try:
        fixture = load_historical_valuation_fixture(fixture_path)
        snapshot = (
            HistoricalValuationFetcher().map_fixture_to_historical_valuation(
                fixture
            )
        )
        merged = merge_historical_valuation_into_pack(pack, snapshot)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            yaml.safe_dump(merged, sort_keys=False, allow_unicode=False),
            encoding="utf-8",
        )
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(
            f"Could not merge historical valuation fixture {fixture_path}: {exc}"
        ) from exc

    console.print(
        f"[bold]Historical valuation fixture merge written to:[/bold] {output_path}"
    )


@app.command("merge-growth-peg-fixture")
def merge_growth_peg_fixture(
    input_path: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Existing manual Backoffice YAML pack.",
        ),
    ],
    fixture_path: Annotated[
        Path,
        typer.Option(
            "--fixture",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Compact growth and PEG JSON fixture.",
        ),
    ],
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Path where the merged YAML pack should be written.",
        ),
    ],
) -> None:
    """Merge offline growth and PEG fixture data into a pack copy."""
    pack = _load_yaml(input_path)
    try:
        fixture = load_growth_peg_fixture(fixture_path)
        snapshot = GrowthPegFetcher().map_fixture_to_growth_peg(fixture)
        merged = merge_growth_peg_into_pack(pack, snapshot)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            yaml.safe_dump(merged, sort_keys=False, allow_unicode=False),
            encoding="utf-8",
        )
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(
            f"Could not merge growth and PEG fixture {fixture_path}: {exc}"
        ) from exc

    console.print(
        f"[bold]Growth and PEG fixture merge written to:[/bold] {output_path}"
    )


@app.command("build-backoffice-report")
def build_backoffice_report(
    input_path: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to a YAML backoffice data pack.",
        ),
    ] = Path("examples/msft_input.yaml"),
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Path where the Markdown report should be written.",
        ),
    ] = Path("examples/msft_backoffice_data_pack.md"),
) -> None:
    """Build a neutral Markdown backoffice report from a local YAML pack."""
    pack = _load_yaml(input_path)
    validation_messages = validate_backoffice_pack(pack)

    if validation_messages:
        console.print("[yellow]Validation warnings:[/yellow]")
        for message in validation_messages:
            console.print(f"[yellow]- {message}[/yellow]")
    else:
        console.print("[green]No validation issues found.[/green]")

    report = generate_backoffice_report(pack)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
    except OSError as exc:
        raise typer.BadParameter(f"Could not write Markdown report {output_path}: {exc}") from exc

    console.print(f"[bold]Backoffice report written to:[/bold] {output_path}")


@app.command("run-agent")
def run_agent(
    agent: Annotated[
        str,
        typer.Option(
            "--agent",
            "-a",
            help="Investor agent to run. Currently supports 'buffett', 'munger', 'fisher', 'lynch', and 'bogle'.",
        ),
    ],
    input_path: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to a YAML backoffice data pack.",
        ),
    ] = Path("examples/msft_input.yaml"),
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Path where the investor report should be written.",
        ),
    ] = Path("examples/msft_buffett_report.md"),
    portfolio_context_path: Annotated[
        Path | None,
        typer.Option(
            "--portfolio-context",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Optional portfolio context YAML for Bogle analysis.",
        ),
    ] = None,
) -> None:
    """Run a deterministic investor agent against a local backoffice pack."""
    pack = _merge_optional_portfolio_context(
        _load_yaml(input_path),
        portfolio_context_path,
    )
    agent_name = agent.lower()
    investor_agent = _build_agent(agent_name, pack)
    report = investor_agent.generate_report()
    save_investor_report(report, output_path)

    console.print(f"[bold]Investor report written to:[/bold] {output_path}")


@app.command("run-all-agents")
def run_all_agents(
    input_path: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to a YAML backoffice data pack.",
        ),
    ] = Path("examples/msft_input.yaml"),
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Directory where investor reports should be written.",
        ),
    ] = Path("examples"),
    portfolio_context_path: Annotated[
        Path | None,
        typer.Option(
            "--portfolio-context",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Optional portfolio context YAML for Bogle analysis.",
        ),
    ] = None,
) -> None:
    """Run all deterministic investor agents against one local backoffice pack."""
    pack = _merge_optional_portfolio_context(
        _load_yaml(input_path),
        portfolio_context_path,
    )
    results = run_all_agent_reports(pack, output_dir)

    table = Table(title="Investor Agent Reports")
    table.add_column("Agent")
    table.add_column("Output File")
    table.add_column("Status")

    for result in results:
        table.add_row(result["agent"], result["output_file"], result["status"])

    console.print(table)


@app.command("summarize-agents")
def summarize_agents(
    ticker: Annotated[
        str,
        typer.Option("--ticker", "-t", help="Ticker symbol used for report filenames."),
    ],
    company_name: Annotated[
        str,
        typer.Option("--company", "-c", help="Company name for the summary report."),
    ],
    reports_dir: Annotated[
        Path,
        typer.Option(
            "--reports-dir",
            "-r",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing generated investor reports.",
        ),
    ] = Path("examples"),
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Path where the summary report should be written.",
        ),
    ] = Path("examples/msft_agents_summary.md"),
) -> None:
    """Summarize independent investor-agent reports without creating consensus."""
    ticker_lower = ticker.lower()
    report_paths = {
        agent_name: reports_dir / f"{ticker_lower}_{agent_name}_report.md"
        for agent_name in AGENT_SPECS
    }
    summary = generate_agents_summary(company_name, ticker, report_paths)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(summary, encoding="utf-8")
    except OSError as exc:
        raise typer.BadParameter(f"Could not write agents summary report {output_path}: {exc}") from exc

    console.print(f"[bold]Agents summary written to:[/bold] {output_path}")


@app.command("run-pipeline")
def run_pipeline(
    input_path: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to a YAML backoffice data pack.",
        ),
    ] = Path("examples/msft_input.yaml"),
    output_dir: Annotated[
        Path | None,
        typer.Option(
            "--output-dir",
            "-o",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Directory where all pipeline reports should be written. Defaults to data/outputs/{TICKER}.",
        ),
    ] = None,
    portfolio_context_path: Annotated[
        Path | None,
        typer.Option(
            "--portfolio-context",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Optional portfolio context YAML for Bogle analysis.",
        ),
    ] = None,
) -> None:
    """Run the full deterministic reporting pipeline."""
    pack = _merge_optional_portfolio_context(
        _load_yaml(input_path),
        portfolio_context_path,
    )
    if output_dir is None:
        company_identity = pack.get("company_identity", {})
        metadata = pack.get("metadata", {})
        ticker = str(company_identity.get("ticker") or metadata.get("ticker") or "company")
        output_dir = output_dir_for_ticker(ticker)

    results = run_full_pipeline(pack, output_dir)

    table = Table(title="Deterministic Pipeline Outputs")
    table.add_column("Artifact")
    table.add_column("Output File")
    table.add_column("Status")

    for result in results:
        table.add_row(result["artifact"], result["output_file"], result["status"])

    console.print(table)


@app.command("run-enriched-pipeline")
def run_enriched_pipeline(
    ticker: Annotated[
        str,
        typer.Option("--ticker", "-t", help="Ticker symbol for the enriched pack."),
    ],
    input_path: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to an enriched Backoffice YAML pack.",
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Directory where enriched pipeline reports should be written.",
        ),
    ],
    portfolio_context_path: Annotated[
        Path | None,
        typer.Option(
            "--portfolio-context",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Optional portfolio context YAML for Bogle analysis.",
        ),
    ] = None,
) -> None:
    """Run the deterministic investor pipeline on one enriched pack."""
    pack = _merge_optional_portfolio_context(
        _load_yaml(input_path),
        portfolio_context_path,
    )
    identity = pack.get("company_identity", {})
    pack_ticker = str(identity.get("ticker") or "").upper()
    requested_ticker = ticker.upper()
    if pack_ticker and pack_ticker != requested_ticker:
        raise typer.BadParameter(
            f"Ticker mismatch: --ticker is {requested_ticker}, but the pack contains {pack_ticker}."
        )

    validation_messages = validate_backoffice_pack(pack)
    if validation_messages:
        console.print(
            f"[yellow]Validation completed with {len(validation_messages)} warning(s).[/yellow]"
        )
    results = run_enriched_pipeline_reports(pack, output_dir)

    table = Table(title=f"{requested_ticker} Enriched Pipeline Outputs")
    table.add_column("Artifact")
    table.add_column("Output File")
    table.add_column("Status")
    for result in results:
        table.add_row(result["artifact"], result["output_file"], result["status"])
    console.print(table)


@app.command("run-enriched-pipelines")
def run_enriched_pipelines(
    tickers: Annotated[
        str,
        typer.Option("--tickers", help="Comma-separated ticker symbols to process."),
    ] = "MSFT,AAPL,NVDA",
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Root directory containing per-ticker enriched inputs.",
        ),
    ] = Path("data/outputs"),
    portfolio_context_path: Annotated[
        Path | None,
        typer.Option(
            "--portfolio-context",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Optional shared portfolio context YAML for Bogle analysis.",
        ),
    ] = None,
) -> None:
    """Run enriched pipelines for known ticker folders, skipping missing inputs."""
    parsed_tickers = [ticker.strip().upper() for ticker in tickers.split(",") if ticker.strip()]
    if not parsed_tickers:
        raise typer.BadParameter("At least one ticker must be provided.")
    portfolio_context = (
        load_portfolio_context(portfolio_context_path)
        if portfolio_context_path
        else None
    )

    table = Table(title="Enriched Pipeline Batch")
    table.add_column("Ticker")
    table.add_column("Input")
    table.add_column("Output Directory")
    table.add_column("Status")

    for ticker in parsed_tickers:
        ticker_lower = ticker.lower()
        input_path = outputs_root / ticker / f"{ticker_lower}_enriched_input.yaml"
        output_dir = outputs_root / ticker / "enriched"
        if not input_path.is_file():
            console.print(
                f"[yellow]Skipping {ticker}: enriched input not found at {input_path}.[/yellow]"
            )
            table.add_row(ticker, str(input_path), str(output_dir), "skipped")
            continue
        try:
            pack = _load_yaml(input_path)
            if portfolio_context:
                pack = merge_portfolio_context_into_pack(pack, portfolio_context)
            run_enriched_pipeline_reports(pack, output_dir)
        except (OSError, ValueError, typer.BadParameter) as exc:
            console.print(f"[red]{ticker} enriched pipeline failed: {exc}[/red]")
            table.add_row(ticker, str(input_path), str(output_dir), "failed")
            continue
        table.add_row(ticker, str(input_path), str(output_dir), "written")

    console.print(table)


@app.command("compare-manual-enriched")
def compare_manual_enriched(
    tickers: Annotated[
        str,
        typer.Option("--tickers", help="Comma-separated ticker symbols to compare."),
    ] = "MSFT,AAPL,NVDA",
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Root directory containing manual and enriched outputs.",
        ),
    ] = Path("data/outputs"),
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Path where the comparison report should be written.",
        ),
    ] = Path("data/outputs/manual_vs_enriched_comparison.md"),
) -> None:
    """Compare source evidence and stable decisions across manual and enriched runs."""
    parsed_tickers = [ticker.strip() for ticker in tickers.split(",") if ticker.strip()]
    if not parsed_tickers:
        raise typer.BadParameter("At least one ticker must be provided.")
    report = generate_manual_vs_enriched_comparison(parsed_tickers, outputs_root)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
    except OSError as exc:
        raise typer.BadParameter(
            f"Could not write manual versus enriched comparison {output_path}: {exc}"
        ) from exc
    console.print(f"[bold]Manual versus enriched comparison written to:[/bold] {output_path}")


@app.command("post-enrichment-gaps")
def post_enrichment_gaps(
    tickers: Annotated[
        str,
        typer.Option("--tickers", help="Comma-separated ticker symbols to review."),
    ] = "MSFT,AAPL,NVDA",
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Root directory containing enriched inputs and outputs.",
        ),
    ] = Path("data/outputs"),
    examples_root: Annotated[
        Path,
        typer.Option(
            "--examples-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing the original manual company inputs.",
        ),
    ] = Path("examples"),
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Path where the post-enrichment gap report should be written.",
        ),
    ] = Path("data/outputs/post_enrichment_evidence_gap_report.md"),
) -> None:
    """Report remaining evidence gaps after deterministic enrichment."""
    parsed_tickers = [ticker.strip() for ticker in tickers.split(",") if ticker.strip()]
    if not parsed_tickers:
        raise typer.BadParameter("At least one ticker must be provided.")
    report = generate_post_enrichment_gap_report(
        parsed_tickers,
        outputs_root,
        examples_root,
    )
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
    except OSError as exc:
        raise typer.BadParameter(
            f"Could not write post-enrichment gap report {output_path}: {exc}"
        ) from exc
    console.print(f"[bold]Post-enrichment gap report written to:[/bold] {output_path}")


@app.command("human-review-queue")
def human_review_queue(
    tickers: Annotated[
        str,
        typer.Option("--tickers", help="Comma-separated ticker symbols to review."),
    ] = "MSFT,AAPL,NVDA",
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Root directory containing enriched packs and reports.",
        ),
    ] = Path("data/outputs"),
    examples_root: Annotated[
        Path,
        typer.Option(
            "--examples-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing manual inputs and portfolio context.",
        ),
    ] = Path("examples"),
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Path where the Human Review Queue Markdown should be written.",
        ),
    ] = Path("data/outputs/human_review_queue.md"),
    json_output_path: Annotated[
        Path | None,
        typer.Option(
            "--json-output",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Optional path where structured queue JSON should be written.",
        ),
    ] = None,
) -> None:
    """Generate a governed queue of questions requiring human judgment."""
    parsed_tickers = [ticker.strip() for ticker in tickers.split(",") if ticker.strip()]
    if not parsed_tickers:
        raise typer.BadParameter("At least one ticker must be provided.")
    items = generate_human_review_queue(
        parsed_tickers,
        outputs_root,
        examples_root,
    )
    report = generate_human_review_queue_report(items)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        if json_output_path is not None:
            json_output_path.parent.mkdir(parents=True, exist_ok=True)
            json_output_path.write_text(
                json.dumps([asdict(item) for item in items], indent=2),
                encoding="utf-8",
            )
    except OSError as exc:
        raise typer.BadParameter(
            f"Could not write Human Review Queue output: {exc}"
        ) from exc

    console.print(f"[bold]Human Review Queue written to:[/bold] {output_path}")
    if json_output_path is not None:
        console.print(f"[bold]Human Review Queue JSON written to:[/bold] {json_output_path}")


@app.command("portfolio-readiness")
def portfolio_readiness(
    tickers: Annotated[
        str,
        typer.Option("--tickers", help="Comma-separated ticker symbols to assess."),
    ] = "MSFT,AAPL,NVDA",
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Root directory containing enriched packs and governance artifacts.",
        ),
    ] = Path("data/outputs"),
    examples_root: Annotated[
        Path,
        typer.Option(
            "--examples-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing manual inputs and portfolio context.",
        ),
    ] = Path("examples"),
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Path where the portfolio readiness Markdown should be written.",
        ),
    ] = Path("data/outputs/portfolio_manager_readiness_report.md"),
    json_output_path: Annotated[
        Path | None,
        typer.Option(
            "--json-output",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Optional path where structured portfolio readiness JSON should be written.",
        ),
    ] = None,
) -> None:
    """Generate governance-only portfolio manager readiness assessments."""
    parsed_tickers = [ticker.strip() for ticker in tickers.split(",") if ticker.strip()]
    if not parsed_tickers:
        raise typer.BadParameter("At least one ticker must be provided.")
    items = generate_portfolio_readiness_items(
        parsed_tickers,
        outputs_root,
        examples_root,
    )
    report = generate_portfolio_manager_readiness_report(items)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        if json_output_path is not None:
            json_output_path.parent.mkdir(parents=True, exist_ok=True)
            json_output_path.write_text(
                json.dumps([asdict(item) for item in items], indent=2),
                encoding="utf-8",
            )
    except OSError as exc:
        raise typer.BadParameter(
            f"Could not write portfolio readiness output: {exc}"
        ) from exc

    console.print(f"[bold]Portfolio readiness report written to:[/bold] {output_path}")
    if json_output_path is not None:
        console.print(
            f"[bold]Portfolio readiness JSON written to:[/bold] {json_output_path}"
        )


@app.command("deal-intake")
def deal_intake(
    ticker: Annotated[
        str,
        typer.Option("--ticker", "-t", help="Ticker symbol to check for deal readiness."),
    ],
    examples_root: Annotated[
        Path,
        typer.Option(
            "--examples-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing manual input packs.",
        ),
    ] = Path("examples"),
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Root directory expected for broker deal outputs.",
        ),
    ] = Path("data/outputs"),
    fixtures_root: Annotated[
        Path,
        typer.Option(
            "--fixtures-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing optional offline enrichment fixtures.",
        ),
    ] = Path("tests/fixtures"),
    portfolio_context_path: Annotated[
        Path | None,
        typer.Option(
            "--portfolio-context",
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Optional portfolio context path to include in the readiness check.",
        ),
    ] = None,
    market: Annotated[
        str | None,
        typer.Option("--market", help="Optional broker-supplied market label."),
    ] = None,
    company_name: Annotated[
        str | None,
        typer.Option("--company-name", help="Optional broker-supplied company name."),
    ] = None,
    output_path: Annotated[
        Path | None,
        typer.Option(
            "--output",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Markdown output path; defaults to the ticker output directory.",
        ),
    ] = None,
    json_output_path: Annotated[
        Path | None,
        typer.Option(
            "--json-output",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Optional structured intake status JSON output.",
        ),
    ] = None,
) -> None:
    """Check a ticker's files without running enrichment or investor agents."""
    status = build_deal_intake_status(
        ticker=ticker,
        examples_root=examples_root,
        outputs_root=outputs_root,
        fixtures_root=fixtures_root,
        portfolio_context_path=portfolio_context_path,
        market=market,
        company_name=company_name,
    )
    normalized = status.normalized_ticker or "UNKNOWN"
    output_path = output_path or (
        outputs_root / normalized / "deal_intake_report.md"
    )
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            generate_deal_intake_report(status),
            encoding="utf-8",
        )
        if json_output_path is not None:
            json_output_path.parent.mkdir(parents=True, exist_ok=True)
            json_output_path.write_text(
                json.dumps(status.to_dict(), indent=2),
                encoding="utf-8",
            )
    except OSError as exc:
        raise typer.BadParameter(f"Could not write deal intake output: {exc}") from exc

    console.print(f"[bold]Intake status:[/bold] {status.intake_status}")
    console.print(f"[bold]Deal intake report written to:[/bold] {output_path}")
    if json_output_path is not None:
        console.print(
            f"[bold]Deal intake JSON written to:[/bold] {json_output_path}"
        )


@app.command("deal-intakes")
def deal_intakes(
    tickers: Annotated[
        str,
        typer.Option("--tickers", help="Comma-separated ticker symbols to check."),
    ] = "MSFT,AAPL,NVDA",
    examples_root: Annotated[
        Path,
        typer.Option(
            "--examples-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing manual input packs.",
        ),
    ] = Path("examples"),
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Root directory for deal intake reports.",
        ),
    ] = Path("data/outputs"),
    fixtures_root: Annotated[
        Path,
        typer.Option(
            "--fixtures-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing optional offline enrichment fixtures.",
        ),
    ] = Path("tests/fixtures"),
    portfolio_context_path: Annotated[
        Path | None,
        typer.Option(
            "--portfolio-context",
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Optional portfolio context path included in each readiness check.",
        ),
    ] = None,
) -> None:
    """Generate deal intake Markdown and JSON for multiple tickers."""
    parsed_tickers = [
        ticker.strip().upper() for ticker in tickers.split(",") if ticker.strip()
    ]
    if not parsed_tickers:
        raise typer.BadParameter("At least one ticker must be provided.")

    table = Table(title="Deal Intake Status")
    table.add_column("Ticker")
    table.add_column("Status")
    table.add_column("Can Run Deal")
    table.add_column("Report")
    for ticker in parsed_tickers:
        status = build_deal_intake_status(
            ticker=ticker,
            examples_root=examples_root,
            outputs_root=outputs_root,
            fixtures_root=fixtures_root,
            portfolio_context_path=portfolio_context_path,
        )
        output_dir = outputs_root / ticker
        report_path = output_dir / "deal_intake_report.md"
        json_path = output_dir / "deal_intake_report.json"
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                generate_deal_intake_report(status),
                encoding="utf-8",
            )
            json_path.write_text(
                json.dumps(status.to_dict(), indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            console.print(f"[yellow]Could not write {ticker} intake: {exc}[/yellow]")
            table.add_row(ticker, "write failed", "No", str(report_path))
            continue
        table.add_row(
            ticker,
            status.intake_status,
            "Yes" if status.can_run_deal else "No",
            str(report_path),
        )
    console.print(table)


@app.command("run-deal")
def run_deal(
    ticker: Annotated[
        str,
        typer.Option("--ticker", "-t", help="Ticker symbol for the broker deal."),
    ],
    input_path: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Manual Backoffice input pack.",
        ),
    ],
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Root directory for broker deal outputs.",
        ),
    ] = Path("data/outputs"),
    fixtures_root: Annotated[
        Path,
        typer.Option(
            "--fixtures-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing offline enrichment fixtures.",
        ),
    ] = Path("tests/fixtures"),
    portfolio_context_path: Annotated[
        Path | None,
        typer.Option(
            "--portfolio-context",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Optional portfolio context used only by the independent Bogle report.",
        ),
    ] = None,
) -> None:
    """Run one Backoffice-to-investor broker deal workflow."""
    try:
        result = run_broker_deal_workflow(
            ticker=ticker,
            input_pack_path=input_path,
            outputs_root=outputs_root,
            fixtures_root=fixtures_root,
            portfolio_context_path=portfolio_context_path,
        )
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise typer.BadParameter(f"Broker deal workflow failed: {exc}") from exc

    console.print(
        f"[bold]Broker deal package written to:[/bold] "
        f"{result.broker_deal_package_path}"
    )
    console.print(f"[bold]Enriched deal input:[/bold] {result.enriched_pack_path}")
    console.print(
        f"[bold]Investor output directory:[/bold] "
        f"{result.investor_summary_path.parent}"
    )
    if result.investor_response_letter_paths:
        response_letter_dir = next(
            iter(result.investor_response_letter_paths.values())
        ).parent
        console.print(
            f"[bold]Investor response letters directory:[/bold] "
            f"{response_letter_dir}"
        )
    if result.investor_follow_up_memo_paths:
        follow_up_memo_dir = next(
            iter(result.investor_follow_up_memo_paths.values())
        ).parent
        console.print(
            f"[bold]Investor follow-up memos directory:[/bold] "
            f"{follow_up_memo_dir}"
        )
    console.print(
        f"[bold]Backoffice work orders:[/bold] "
        f"{result.backoffice_work_orders_path}"
    )


@app.command("analyze-stock")
def analyze_stock(
    ticker: Annotated[
        str | None,
        typer.Option(
            "--ticker",
            "-t",
            help="Ticker symbol for the unified broker deal analysis.",
        ),
    ] = None,
    intake_file: Annotated[
        Path | None,
        typer.Option(
            "--intake-file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Structured YAML or JSON analyze-stock intake configuration.",
        ),
    ] = None,
    examples_root: Annotated[
        Path,
        typer.Option(
            "--examples-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing manual input packs.",
        ),
    ] = Path("examples"),
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Root directory for intake and broker deal outputs.",
        ),
    ] = Path("data/outputs"),
    fixtures_root: Annotated[
        Path,
        typer.Option(
            "--fixtures-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing offline enrichment fixtures.",
        ),
    ] = Path("tests/fixtures"),
    portfolio_context_path: Annotated[
        Path | None,
        typer.Option(
            "--portfolio-context",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Optional portfolio context for the independent Bogle analysis.",
        ),
    ] = None,
    as_of_date: Annotated[
        str | None,
        typer.Option(
            "--as-of-date",
            help="Historical-readiness date in YYYY-MM-DD format.",
        ),
    ] = None,
    financials_provider: Annotated[
        str | None,
        typer.Option(
            "--financials-provider",
            help=(
                "Official financials provider: fixture, sec_fixture, default, "
                "or historical_csv."
            ),
        ),
    ] = None,
    financials_root: Annotated[
        Path | None,
        typer.Option(
            "--financials-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing historical financials CSV files.",
        ),
    ] = None,
) -> None:
    """Run intake and the complete existing broker deal workflow for one ticker."""
    if ticker is not None and intake_file is not None:
        raise typer.BadParameter(
            "Provide either --ticker or --intake-file, not both."
        )
    if ticker is None and intake_file is None:
        raise typer.BadParameter(
            "Provide one input mode: --ticker or --intake-file."
        )
    try:
        if intake_file is not None:
            intake = load_analyze_stock_intake(intake_file)
            if as_of_date is not None:
                intake = with_as_of_date(intake, as_of_date)
            input_mode = "intake_file"
        else:
            intake = build_ticker_analyze_stock_intake(
                ticker=ticker or "",
                examples_root=examples_root,
                outputs_root=outputs_root,
                fixtures_root=fixtures_root,
                portfolio_context=portfolio_context_path,
                as_of_date=as_of_date,
                financials_provider=(financials_provider or "sec_fixture"),
                financials_root=financials_root,
            )
            input_mode = "ticker"
        intake = with_financials_provider(
            intake,
            financials_provider or intake.financials_provider,
            financials_root or intake.financials_root,
        )
    except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    try:
        execution = execute_analyze_stock(
            intake=intake,
            input_mode=input_mode,
            intake_file=intake_file,
        )
    except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Unified stock analysis failed: {exc}"
        ) from exc

    normalized = execution.intake_status.normalized_ticker or "UNKNOWN"
    result = execution.workflow_result
    package_payload = execution.package_payload
    run_bundle = execution.run_bundle
    executive_summary = package_payload.get("executive_summary", {})
    work_order_plan = package_payload.get("backoffice_work_order_plan", {})
    archive_result = archive_completed_run(
        outputs_root=intake.outputs_root,
        run_manifest_path=run_bundle.run_manifest_path,
        broker_deal_package_path=result.broker_deal_package_path,
    )
    historical_context = build_as_of_context(intake.as_of_date)
    run_manifest = json.loads(
        run_bundle.run_manifest_path.read_text(encoding="utf-8")
    )
    readiness_ledger = run_manifest.get(
        "historical_readiness_ledger_record",
        {},
    )

    console.print(f"Input Mode: {input_mode}", soft_wrap=True)
    console.print(
        f"Intake File: {intake_file if intake_file is not None else 'Not used'}",
        soft_wrap=True,
    )
    console.print(
        f"Run Label: {intake.run_label or 'Not provided'}",
        soft_wrap=True,
    )
    table = Table(title="Unified Stock Analysis")
    table.add_column("Field")
    table.add_column("Value")
    rows = [
        ("Input Mode", input_mode),
        (
            "Intake File",
            str(intake_file) if intake_file is not None else "Not used",
        ),
        ("Run Label", intake.run_label or "Not provided"),
        ("Financials Provider", intake.financials_provider),
        (
            "Financials Root",
            str(intake.financials_root) if intake.financials_root else "Not used",
        ),
        (
            "As-Of Date",
            (
                historical_context.as_of_date.isoformat()
                if historical_context.as_of_date
                else "Not provided"
            ),
        ),
        (
            "Historical Mode",
            "enabled" if historical_context.historical_mode else "disabled",
        ),
        (
            "Point-in-Time Enforcement",
            historical_context.point_in_time_enforcement,
        ),
        ("Run ID", run_bundle.run_id),
        ("Run Folder", str(run_bundle.run_folder)),
        ("Run Manifest", str(run_bundle.run_manifest_path)),
        ("Run Summary", str(run_bundle.run_summary_path)),
        (
            "Official Financials Snapshot",
            str(
                run_bundle.run_folder
                / "official_financials_as_of_snapshot.csv"
            )
            if intake.financials_provider == "historical_csv"
            else "Not enabled",
        ),
        ("Ticker", normalized),
        ("Broker Deal Package", str(result.broker_deal_package_path)),
        ("Enriched Input", str(result.enriched_pack_path)),
        (
            "Investor Response Letters",
            str(execution.investor_response_letters_dir),
        ),
        (
            "Investor Follow-Up Memos",
            str(execution.investor_follow_up_memos_dir),
        ),
        ("Backoffice Work Orders", str(result.backoffice_work_orders_path)),
        ("Intake Snapshot", str(execution.intake_snapshot_path)),
        ("Source Verification Status", result.source_verification_status),
        (
            "Readiness Label",
            str(executive_summary.get("backoffice_readiness_label", "Unknown")),
        ),
        (
            "Total Investor Responses",
            str(len(package_payload.get("investor_responses", []))),
        ),
        (
            "Total Work Orders",
            str(work_order_plan.get("total_work_orders", "Unknown")),
        ),
        (
            "Promotion-Blocking Categories",
            ", ".join(
                work_order_plan.get("promotion_blocking_categories", [])
            )
            or "None",
        ),
        ("Signal Archive Record", "archived"),
        ("Signal Ledger", str(archive_result.jsonl_path)),
        *(
            [
                ("Historical Readiness Ledger Record", "archived"),
                (
                    "Historical Readiness Ledger",
                    str(readiness_ledger["ledger_jsonl"]),
                ),
            ]
            if readiness_ledger.get("archived")
            else []
        ),
        ("Status", "completed"),
    ]
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)


@app.command("validate-historical-snapshot")
def validate_historical_snapshot(
    as_of_date: Annotated[
        str,
        typer.Option(
            "--as-of-date",
            help="Historical snapshot date in YYYY-MM-DD format.",
        ),
    ],
    price_provider: Annotated[
        str,
        typer.Option(
            "--price-provider",
            help="Price provider capability to evaluate.",
        ),
    ] = "fixture",
    price_fixtures_path: Annotated[
        Path | None,
        typer.Option(
            "--price-fixtures",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Optional local price-data root used by the contract.",
        ),
    ] = None,
    financials_provider: Annotated[
        str,
        typer.Option(
            "--financials-provider",
            help="Financials capability: sec_fixture or historical_csv.",
        ),
    ] = "sec_fixture",
    financials_root: Annotated[
        Path | None,
        typer.Option(
            "--financials-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Optional root containing historical financials CSV files.",
        ),
    ] = None,
) -> None:
    """Validate point-in-time readiness without running investor agents."""
    try:
        contract = build_historical_snapshot_contract(
            as_of_date,
            price_provider=price_provider,
            input_mode="validation",
            fixtures_root=price_fixtures_path,
            price_data_root=price_fixtures_path,
            financials_provider=financials_provider,
            financials_root=financials_root,
        )
    except ValueError as exc:
        raise typer.BadParameter(
            f"Historical snapshot validation failed: {exc}"
        ) from exc

    table = Table(title="Historical Data Snapshot Contract")
    for column in (
        "Section",
        "Provider",
        "Supports As-Of Date",
        "Enforcement Level",
        "Leakage Risk",
        "Status",
    ):
        table.add_column(column)
    for capability in contract.provider_capabilities:
        status = (
            "supported"
            if capability.supports_as_of_date
            else capability.enforcement_level
        )
        table.add_row(
            capability.section,
            capability.provider_name,
            str(capability.supports_as_of_date).lower(),
            capability.enforcement_level,
            capability.leakage_risk,
            status,
        )
    console.print(table)
    for capability in contract.provider_capabilities:
        console.print(
            " | ".join(
                (
                    f"section={capability.section}",
                    f"provider={capability.provider_name}",
                    (
                        "supports_as_of_date="
                        f"{str(capability.supports_as_of_date).lower()}"
                    ),
                    f"enforcement_level={capability.enforcement_level}",
                    f"leakage_risk={capability.leakage_risk}",
                )
            )
        )
    console.print(f"As-Of Date: {contract.as_of_date}")
    console.print(f"Snapshot Status: {contract.snapshot_status}")
    console.print(
        f"Point-in-Time Enforcement: {contract.point_in_time_enforcement}"
    )
    analysis_window = build_analysis_price_window(as_of_date)
    console.print(
        f"Analysis Price Window End Date: {analysis_window.end_date}"
    )
    console.print("Market Price Window Enforcement: analysis_window_enforced")
    console.print(
        "Price Window Note: prices after as_of_date are excluded from "
        "analysis windows."
    )
    financials_contract = build_financials_as_of_contract(
        as_of_date,
        fixtures_root=price_fixtures_path,
        provider_name=financials_provider,
        financials_root=financials_root,
    )
    console.print("Official Financials As-Of Readiness:")
    console.print(
        f"Official Financials Note: {financials_contract.notes[0]}"
    )
    console.print(
        "Official Financials Status: "
        f"{financials_contract.status}"
    )
    if not financials_contract.supports_as_of_date:
        console.print(
            "Official financials are not yet guaranteed point-in-time safe."
        )
    console.print(
        "Official Financials Missing Date Fields: "
        f"{', '.join(financials_contract.missing_date_fields) or 'None'}"
    )
    for warning in financials_contract.warnings:
        console.print(f"Official Financials Warning: {warning}")
    console.print(
        "Leakage Risk Sections: "
        f"{', '.join(contract.leakage_risk_sections) or 'None'}"
    )
    for warning in contract.warnings:
        console.print(f"Warning: {warning}")


@app.command("validate-financials-csv")
def validate_financials_csv(
    financials_root: Annotated[
        Path,
        typer.Option(
            "--financials-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing local historical financials CSV files.",
        ),
    ],
    tickers: Annotated[
        str,
        typer.Option("--tickers", help="Comma-separated tickers to validate."),
    ],
    as_of_date: Annotated[
        str,
        typer.Option("--as-of-date", help="Historical cutoff in YYYY-MM-DD."),
    ],
) -> None:
    """Validate and cutoff-filter local historical financials CSV files."""
    table = Table(title="Historical Financials CSV Validation")
    for column in (
        "Ticker",
        "File Found",
        "Rows",
        "Required Columns",
        "Before",
        "After",
        "Future Excluded",
        "Missing Availability",
        "Max Filing Date",
        "Max Accepted Date",
        "Status",
    ):
        table.add_column(column)
    automation_lines = []
    parsed_tickers = [
        item.strip().upper() for item in tickers.split(",") if item.strip()
    ]
    for ticker in parsed_tickers:
        path = historical_financials_path(financials_root, ticker)
        validation = validate_historical_financials_csv(path)
        filtered = None
        if validation.required_columns_present and validation.rows_count:
            try:
                filtered = filter_financials_as_of(
                    load_historical_financials_csv(path),
                    as_of_date,
                )
            except ValueError as exc:
                raise typer.BadParameter(
                    f"Historical financials validation failed: {exc}"
                ) from exc
        before = filtered.rows_before_filter if filtered else validation.rows_count
        after = filtered.rows_after_filter if filtered else 0
        future = filtered.future_rows_excluded_count if filtered else 0
        missing_availability = (
            filtered.rows_missing_availability_date_count
            if filtered
            else validation.rows_missing_availability_date_count
        )
        status = filtered.status if filtered else validation.status
        max_filing = filtered.max_filing_date_after_filter if filtered else None
        max_accepted = (
            filtered.max_accepted_date_after_filter if filtered else None
        )
        table.add_row(
            ticker,
            str(validation.file_found).lower(),
            str(validation.rows_count),
            str(validation.required_columns_present).lower(),
            str(before),
            str(after),
            str(future),
            str(missing_availability),
            max_filing or "None",
            max_accepted or "None",
            status,
        )
        automation_lines.append(
            " | ".join(
                (
                    f"ticker={ticker}",
                    f"file_found={str(validation.file_found).lower()}",
                    f"rows={validation.rows_count}",
                    (
                        "required_columns_present="
                        f"{str(validation.required_columns_present).lower()}"
                    ),
                    f"rows_before_filter={before}",
                    f"rows_after_filter={after}",
                    f"future_rows_excluded_count={future}",
                    (
                        "rows_missing_availability_date_count="
                        f"{missing_availability}"
                    ),
                    f"max_filing_date_after_filter={max_filing or 'None'}",
                    (
                        "max_accepted_date_after_filter="
                        f"{max_accepted or 'None'}"
                    ),
                    f"status={status}",
                )
            )
        )
    console.print(table)
    for line in automation_lines:
        console.print(line)


@app.command("validate-financials-as-of")
def validate_financials_as_of(
    as_of_date: Annotated[
        str,
        typer.Option(
            "--as-of-date",
            help="Historical financials cutoff in YYYY-MM-DD format.",
        ),
    ],
    fixtures_root: Annotated[
        Path,
        typer.Option(
            "--fixtures-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing offline official-financial fixtures.",
        ),
    ] = Path("tests/fixtures"),
    ticker: Annotated[
        str | None,
        typer.Option(
            "--ticker",
            help="Optional ticker whose SEC fixture metadata is inspected.",
        ),
    ] = None,
) -> None:
    """Validate official-financials point-in-time readiness offline."""
    try:
        contract = build_financials_as_of_contract(
            as_of_date,
            fixtures_root=fixtures_root,
            ticker=ticker,
        )
    except ValueError as exc:
        raise typer.BadParameter(
            f"Financials as-of validation failed: {exc}"
        ) from exc

    table = Table(title="Official Financials As-Of Contract")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Provider", contract.provider_name),
        ("As-Of Date", str(contract.as_of_date)),
        (
            "Supports As-Of Date",
            str(contract.supports_as_of_date).lower(),
        ),
        ("Enforcement Level", contract.enforcement_level),
        ("Leakage Risk", contract.leakage_risk),
        ("Required Date Fields", ", ".join(contract.required_date_fields)),
        (
            "Available Date Fields",
            ", ".join(contract.available_date_fields) or "None",
        ),
        (
            "Missing Date Fields",
            ", ".join(contract.missing_date_fields) or "None",
        ),
        ("Status", contract.status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"provider={contract.provider_name}")
    console.print(f"as_of_date={contract.as_of_date}")
    console.print(
        f"supports_as_of_date={str(contract.supports_as_of_date).lower()}"
    )
    console.print(f"enforcement_level={contract.enforcement_level}")
    console.print(f"leakage_risk={contract.leakage_risk}")
    console.print(f"status={contract.status}")
    for warning in contract.warnings:
        console.print(f"warning={warning}")


@app.command("validate-price-window")
def validate_price_window(
    ticker: Annotated[
        str,
        typer.Option("--ticker", help="Ticker whose local price window is checked."),
    ],
    as_of_date: Annotated[
        str,
        typer.Option("--as-of-date", help="Analysis cutoff in YYYY-MM-DD format."),
    ],
    price_provider: Annotated[
        str,
        typer.Option("--price-provider", help="Offline price provider to validate."),
    ] = "csv",
    price_fixtures_path: Annotated[
        Path,
        typer.Option(
            "--price-fixtures",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing local ticker price CSV files.",
        ),
    ] = Path("tests/fixtures/historical_price_history"),
) -> None:
    """Validate that an analysis window excludes post-cutoff prices."""
    try:
        window = build_analysis_price_window(as_of_date)
        provider = create_price_provider(price_provider, price_fixtures_path)
        result = provider.get_price_history(
            ticker,
            end_date=window.end_date,
            window_type=window.window_type,
        )
    except ValueError as exc:
        raise typer.BadParameter(f"Price window validation failed: {exc}") from exc

    max_date = max((point.date for point in result.rows), default=None)
    table = Table(title="Historical Analysis Price Window")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Ticker", result.ticker),
        ("Provider", result.provider_name),
        ("As-Of Date", as_of_date),
        ("Rows Before Filter", str(result.rows_before_filter)),
        ("Rows After Filter", str(result.rows_after_filter)),
        (
            "Future Rows Excluded Count",
            str(result.future_rows_excluded_count),
        ),
        ("Max Date After Filter", str(max_date) if max_date else "None"),
        ("Status", result.status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"ticker={result.ticker}")
    console.print(f"provider={result.provider_name}")
    console.print(f"as_of_date={as_of_date}")
    console.print(f"rows_before_filter={result.rows_before_filter}")
    console.print(f"rows_after_filter={result.rows_after_filter}")
    console.print(
        f"future_rows_excluded_count={result.future_rows_excluded_count}"
    )
    console.print(f"max_date_after_filter={max_date or 'None'}")
    console.print(f"status={result.status}")


@app.command("validate-historical-signal-candidate")
def validate_historical_signal_candidate(
    candidate_file: Annotated[
        Path,
        typer.Option(
            "--candidate-file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Run-local historical signal readiness candidate JSON.",
        ),
    ],
) -> None:
    """Validate a readiness-only candidate without running analysis."""
    try:
        payload = json.loads(candidate_file.read_text(encoding="utf-8"))
        candidate = HistoricalSignalReadinessCandidate(**payload)
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        raise typer.BadParameter(
            f"Historical signal candidate validation failed: {exc}"
        ) from exc
    valid = (
        candidate.historical_signal_candidate
        and candidate.signal_generation_status == "readiness_only"
        and not candidate.safe_for_historical_signal_generation
        and candidate.not_trade_signal
        and candidate.not_recommendation
        and candidate.not_allocation_instruction
    )
    if not valid:
        raise typer.BadParameter(
            "Candidate does not satisfy readiness-only safety invariants."
        )

    table = Table(title="Historical Signal Readiness Candidate")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Ticker", candidate.ticker),
        ("As-Of Date", candidate.as_of_date),
        ("Signal Generation Status", candidate.signal_generation_status),
        (
            "Safe for Historical Signal Generation",
            str(candidate.safe_for_historical_signal_generation).lower(),
        ),
        ("Not Trade Signal", str(candidate.not_trade_signal).lower()),
        ("Not Recommendation", str(candidate.not_recommendation).lower()),
        ("Blocking Reasons Count", str(len(candidate.blocking_reasons))),
        ("Status", "valid_readiness_candidate"),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"ticker={candidate.ticker}")
    console.print(f"as_of_date={candidate.as_of_date}")
    console.print(
        f"signal_generation_status={candidate.signal_generation_status}"
    )
    console.print(
        "safe_for_historical_signal_generation="
        f"{str(candidate.safe_for_historical_signal_generation).lower()}"
    )
    console.print(
        f"not_trade_signal={str(candidate.not_trade_signal).lower()}"
    )
    console.print(
        f"not_recommendation={str(candidate.not_recommendation).lower()}"
    )
    console.print(f"blocking_reasons_count={len(candidate.blocking_reasons)}")
    console.print("status=valid_readiness_candidate")


@app.command("show-historical-readiness-ledger")
def show_historical_readiness_ledger(
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Output root containing the historical readiness ledger.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Show the latest separate historical-readiness ledger snapshot."""
    ledger_dir = outputs_root / "historical_readiness_ledger"
    snapshot_path = (
        ledger_dir / "latest_historical_signal_readiness_ledger_snapshot.json"
    )
    if not snapshot_path.is_file():
        raise typer.BadParameter(
            f"Historical readiness ledger snapshot not found: {snapshot_path}"
        )
    try:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Historical readiness ledger could not be read: {exc}"
        ) from exc
    latest = snapshot.get("latest_record", {})
    table = Table(title="Historical Readiness Candidate Ledger")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Total Records", str(snapshot.get("total_records", 0))),
        ("Latest Ticker", str(latest.get("ticker", "None"))),
        ("Latest As-Of Date", str(latest.get("as_of_date", "None"))),
        (
            "Latest Signal Generation Status",
            str(latest.get("signal_generation_status", "None")),
        ),
        (
            "Latest Not Trade Signal",
            str(latest.get("not_trade_signal", False)).lower(),
        ),
        (
            "Latest Not Recommendation",
            str(latest.get("not_recommendation", False)).lower(),
        ),
        ("Ledger JSONL", str(snapshot.get("ledger_jsonl", "None"))),
        ("Ledger CSV", str(snapshot.get("ledger_csv", "None"))),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"total_records={snapshot.get('total_records', 0)}")
    console.print(f"latest_ticker={latest.get('ticker', 'None')}")
    console.print(f"latest_as_of_date={latest.get('as_of_date', 'None')}")
    console.print(
        "latest_signal_generation_status="
        f"{latest.get('signal_generation_status', 'None')}"
    )
    console.print(
        "latest_not_trade_signal="
        f"{str(latest.get('not_trade_signal', False)).lower()}"
    )
    console.print(
        "latest_not_recommendation="
        f"{str(latest.get('not_recommendation', False)).lower()}"
    )
    console.print(f"ledger_jsonl={snapshot.get('ledger_jsonl', 'None')}")
    console.print(f"ledger_csv={snapshot.get('ledger_csv', 'None')}")


@app.command("export-readiness-trial-ledger")
def export_readiness_trial_ledger(
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Output root containing the historical readiness ledger.",
        ),
    ] = Path("data/outputs"),
    output_ledger: Annotated[
        Path,
        typer.Option(
            "--output-ledger",
            file_okay=True,
            dir_okay=False,
            help="Destination trial ledger CSV.",
        ),
    ] = Path(
        "data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv"
    ),
    source_ledger: Annotated[
        Path | None,
        typer.Option(
            "--source-ledger",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Optional readiness ledger CSV or JSONL override.",
        ),
    ] = None,
    metadata_file: Annotated[
        Path | None,
        typer.Option(
            "--metadata-file",
            file_okay=True,
            dir_okay=False,
            help="Optional export metadata JSON path.",
        ),
    ] = None,
) -> None:
    """Export readiness-only records to a research trial ledger."""
    resolved_source = source_ledger or (
        outputs_root
        / "historical_readiness_ledger"
        / "historical_signal_readiness_ledger.csv"
    )
    try:
        result = export_readiness_ledger_to_trial_ledger(
            source_ledger=resolved_source,
            output_ledger=output_ledger,
            metadata_file=metadata_file,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Readiness trial ledger export failed: {exc}"
        ) from exc

    table = Table(title="Readiness Ledger Trial Export")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Source Ledger", str(result.source_ledger)),
        ("Output Ledger", str(result.output_ledger)),
        ("Metadata File", str(result.metadata_file)),
        ("Total Input Records", str(result.total_input_records)),
        ("Total Exported Records", str(result.total_exported_records)),
        ("Skipped Records", str(result.skipped_records)),
        ("Metadata Enrichment", "enabled"),
        (
            "Metadata Status Counts",
            json.dumps(result.metadata_enrichment_status_counts, sort_keys=True),
        ),
        ("Metadata Fields Added", str(len(ENRICHMENT_FIELDS))),
        ("Status", "completed"),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"source_ledger={result.source_ledger}", soft_wrap=True)
    console.print(f"output_ledger={result.output_ledger}", soft_wrap=True)
    console.print(
        f"total_exported_records={result.total_exported_records}"
    )
    console.print("status=completed")


@app.command("validate-readiness-trial-ledger")
def validate_readiness_trial_ledger_command(
    ledger: Annotated[
        Path,
        typer.Option(
            "--ledger",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Readiness-only trial ledger CSV to validate.",
        ),
    ],
) -> None:
    """Validate research-only trial ledger safety invariants."""
    try:
        result = validate_readiness_trial_ledger(ledger)
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(
            f"Readiness trial ledger validation failed: {exc}"
        ) from exc

    table = Table(title="Readiness Trial Ledger Validation")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Rows", str(result.rows)),
        ("Readiness-Only Rows", str(result.readiness_only_rows)),
        ("Not Trade Signal Rows", str(result.not_trade_signal_rows)),
        ("Not Recommendation Rows", str(result.not_recommendation_rows)),
        ("Invalid Rows", str(result.invalid_rows)),
        ("Status", result.status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"rows={result.rows}")
    console.print(f"readiness_only_rows={result.readiness_only_rows}")
    console.print(f"not_trade_signal_rows={result.not_trade_signal_rows}")
    console.print(
        f"not_recommendation_rows={result.not_recommendation_rows}"
    )
    console.print(f"invalid_rows={result.invalid_rows}")
    console.print(f"status={result.status}")
    for warning in result.warnings:
        console.print(f"warning={warning}")
    if result.invalid_rows:
        raise typer.Exit(code=1)


@app.command("validate-expanded-ticker-coverage")
def validate_expanded_ticker_coverage_command(
    ticker_universe: Annotated[
        Path,
        typer.Option(
            "--ticker-universe",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Research-only candidate ticker universe YAML.",
        ),
    ] = Path("examples/expanded_ticker_universe.yaml"),
    as_of_dates: Annotated[
        str | None,
        typer.Option(
            "--as-of-dates",
            help=(
                "Comma-separated coverage dates. Explicit dates take "
                "precedence over --date-preset."
            ),
        ),
    ] = None,
    date_preset: Annotated[
        str | None,
        typer.Option(
            "--date-preset",
            help="Date preset: annual_3, semiannual_6, or quarterly_9.",
        ),
    ] = None,
    fixtures_root: Annotated[
        Path,
        typer.Option(
            "--fixtures-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Offline fixture root retained for command consistency.",
        ),
    ] = Path("tests/fixtures"),
    financials_root: Annotated[
        Path,
        typer.Option(
            "--financials-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Point-in-time historical financial fixture directory.",
        ),
    ] = Path("tests/fixtures/historical_financials"),
    price_fixtures: Annotated[
        Path,
        typer.Option(
            "--price-fixtures",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Historical price fixture directory.",
        ),
    ] = Path("tests/fixtures/historical_price_history"),
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Root for expanded coverage validation artifacts.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Validate expanded ticker admission using local fixture coverage."""
    del fixtures_root
    try:
        if as_of_dates:
            requested_dates = [
                value.strip()
                for value in as_of_dates.split(",")
                if value.strip()
            ]
        elif date_preset:
            requested_dates = resolve_historical_date_preset(date_preset)
        else:
            requested_dates = resolve_historical_date_preset("annual_3")
        if not requested_dates:
            raise ValueError("At least one as-of date is required.")
        files = write_expanded_ticker_coverage_report(
            ticker_universe_path=ticker_universe,
            requested_dates=requested_dates,
            financials_root=financials_root,
            price_root=price_fixtures,
            outputs_root=outputs_root,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Expanded ticker coverage validation failed: {exc}"
        ) from exc

    report = files.report
    table = Table(title="Expanded Ticker Coverage Validation")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Validation Run ID", report.validation_run_id),
        ("Validation Status", report.validation_status),
        ("Requested Tickers", str(len(report.requested_tickers))),
        ("Requested Dates", ", ".join(report.requested_dates)),
        ("Eligible Tickers", ", ".join(report.eligible_tickers) or "None"),
        ("Caution Tickers", ", ".join(report.caution_tickers) or "None"),
        ("Excluded Tickers", ", ".join(report.excluded_tickers) or "None"),
        (
            "Coverage Quality Counts",
            json.dumps(report.coverage_quality_counts, sort_keys=True),
        ),
        (
            "Eligibility Counts",
            json.dumps(report.eligibility_counts, sort_keys=True),
        ),
        ("Eligible Universe", str(files.eligible_universe_path)),
        ("Report Path", str(files.markdown_path)),
        ("Status", "completed"),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"validation_run_id={report.validation_run_id}")
    console.print(f"validation_status={report.validation_status}")
    console.print(f"eligible_tickers={','.join(report.eligible_tickers)}")
    console.print(f"caution_tickers={','.join(report.caution_tickers)}")
    console.print(f"excluded_tickers={','.join(report.excluded_tickers)}")
    console.print(f"eligible_universe={files.eligible_universe_path}")
    console.print("status=completed")


@app.command("validate-expanded-ticker-coverage-output")
def validate_expanded_ticker_coverage_output_command(
    validation_run_id: Annotated[
        str | None,
        typer.Option(
            "--validation-run-id",
            help="Expanded ticker coverage validation run ID.",
        ),
    ] = None,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Root containing expanded coverage and validation outputs.",
        ),
    ] = Path("data/outputs"),
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Validate the latest expanded ticker coverage output.",
        ),
    ] = False,
) -> None:
    """Validate Task 101 outputs before expanded trial execution."""
    try:
        if auto_latest:
            latest_manifest = load_latest_expanded_ticker_coverage_manifest(
                outputs_root
            )
            validation_run_id = str(latest_manifest["validation_run_id"])
        else:
            if not validation_run_id:
                raise ValueError(
                    "Provide --validation-run-id or use --auto-latest."
                )
            try:
                latest_manifest = (
                    load_latest_expanded_ticker_coverage_manifest(
                        outputs_root
                    )
                )
            except FileNotFoundError:
                latest_manifest = {}
        files = (
            write_expanded_ticker_coverage_output_validation_report(
                outputs_root=outputs_root,
                validation_run_id=validation_run_id,
                latest_manifest=latest_manifest,
            )
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Expanded ticker coverage output validation failed: {exc}"
        ) from exc

    report = files.report
    table = Table(title="Expanded Ticker Coverage Output Validation")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Validation Check Run ID", report.validation_check_run_id),
        ("Source Validation Run ID", report.source_validation_run_id),
        ("Output Validation Status", report.output_validation_status),
        (
            "Ready for Expanded Trial",
            str(report.readiness_for_expanded_trial).lower(),
        ),
        ("Eligible Ticker Count", str(len(report.eligible_tickers))),
        ("Clean Record Total", str(report.clean_record_total)),
        ("Usable Record Total", str(report.usable_record_total)),
        ("Unsupported Record Total", str(report.unsupported_record_total)),
        ("Pass Count", str(report.pass_count)),
        ("Warning Count", str(report.warn_count)),
        ("Fail Count", str(report.fail_count)),
        ("Next Research Action", str(report.next_research_action)),
        ("Report Path", str(files.markdown_path)),
        ("Status", "completed"),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(
        f"validation_check_run_id={report.validation_check_run_id}"
    )
    console.print(
        f"source_validation_run_id={report.source_validation_run_id}"
    )
    console.print(
        f"output_validation_status={report.output_validation_status}"
    )
    console.print(
        "readiness_for_expanded_trial="
        f"{str(report.readiness_for_expanded_trial).lower()}"
    )
    console.print(f"fail_count={report.fail_count}")
    console.print(f"next_research_action={report.next_research_action}")
    console.print("status=completed")


@app.command("run-historical-readiness-multidate")
def run_historical_readiness_multidate_command(
    tickers: Annotated[
        str,
        typer.Option(
            "--tickers",
            help="Comma-separated ticker symbols for each historical date.",
        ),
    ] = "MSFT,AAPL,NVDA,COST",
    as_of_dates: Annotated[
        str | None,
        typer.Option(
            "--as-of-dates",
            help=(
                "Comma-separated historical readiness dates. Explicit dates "
                "take precedence over --date-preset."
            ),
        ),
    ] = None,
    date_preset: Annotated[
        str | None,
        typer.Option(
            "--date-preset",
            help="Date preset: annual_3, semiannual_6, or quarterly_9.",
        ),
    ] = None,
    examples_root: Annotated[
        Path,
        typer.Option(
            "--examples-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing manual input packs.",
        ),
    ] = Path("examples"),
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Root directory for ticker, multidate, and backtest outputs.",
        ),
    ] = Path("data/outputs"),
    fixtures_root: Annotated[
        Path,
        typer.Option(
            "--fixtures-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing offline enrichment fixtures.",
        ),
    ] = Path("tests/fixtures"),
    portfolio_context_path: Annotated[
        Path | None,
        typer.Option(
            "--portfolio-context",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Optional portfolio context for independent Bogle analysis.",
        ),
    ] = None,
    financials_provider: Annotated[
        str,
        typer.Option(
            "--financials-provider",
            help="Historical financials provider; currently historical_csv.",
        ),
    ] = "historical_csv",
    financials_root: Annotated[
        Path,
        typer.Option(
            "--financials-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing point-in-time financials CSV files.",
        ),
    ] = Path("tests/fixtures/historical_financials"),
    export_trial_ledger: Annotated[
        bool,
        typer.Option(
            "--export-trial-ledger",
            help="Export the aggregate readiness-only trial ledger.",
        ),
    ] = False,
    validate_trial_ledger: Annotated[
        bool,
        typer.Option(
            "--validate-trial-ledger",
            help="Validate the aggregate readiness-only trial ledger.",
        ),
    ] = False,
    run_readiness_backtest: Annotated[
        bool,
        typer.Option(
            "--run-readiness-backtest",
            help="Run one readiness-only backtest after all dates finish.",
        ),
    ] = False,
    trial_ledger_path: Annotated[
        Path,
        typer.Option(
            "--trial-ledger",
            help="Output path for the aggregate readiness trial ledger.",
        ),
    ] = Path(
        "data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv"
    ),
    price_fixtures_path: Annotated[
        Path,
        typer.Option(
            "--price-fixtures",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Historical local CSV prices for the optional backtest.",
        ),
    ] = Path("tests/fixtures/historical_price_history"),
) -> None:
    """Expand readiness research across multiple tickers and dates."""
    try:
        result = run_historical_readiness_multidate(
            tickers=tickers,
            as_of_dates=as_of_dates,
            date_preset=date_preset,
            examples_root=examples_root,
            outputs_root=outputs_root,
            fixtures_root=fixtures_root,
            portfolio_context=portfolio_context_path,
            financials_provider=financials_provider,
            financials_root=financials_root,
            export_trial_ledger=export_trial_ledger,
            validate_trial_ledger=validate_trial_ledger,
            run_readiness_backtest=run_readiness_backtest,
            trial_ledger_path=trial_ledger_path,
            price_fixtures_path=price_fixtures_path,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Historical readiness multi-date trial failed: {exc}"
        ) from exc

    table = Table(title="Historical Readiness Multi-Date Trial")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Multi-Date Run ID", result.multidate_run_id),
        ("Date Preset", result.date_preset or "explicit"),
        ("As-Of Dates", ",".join(result.resolved_as_of_dates)),
        ("Usable Dates", ",".join(result.usable_dates) or "None"),
        ("Skipped Dates", ",".join(result.skipped_dates) or "None"),
        ("Date Coverage", result.date_coverage_status),
        ("Date Coverage Report", str(result.date_coverage_report_path)),
        (
            "Coverage Quality Counts",
            json.dumps(result.coverage_quality_counts, sort_keys=True),
        ),
        (
            "Coverage Severity Counts",
            json.dumps(result.coverage_severity_counts, sort_keys=True),
        ),
        ("Tickers Requested", tickers),
        ("Expected Runs", str(result.total_expected_runs)),
        ("Completed Runs", str(result.total_completed_runs)),
        ("Failed Runs", str(result.total_failed_runs)),
        (
            "Export Trial Ledger",
            str(result.trial_ledger_exported).lower(),
        ),
        ("Validate Trial Ledger", result.trial_ledger_validation_status),
        (
            "Run Readiness Backtest",
            str(result.readiness_backtest_run).lower(),
        ),
        (
            "Sample Size After Dedupe",
            (
                str(result.sample_size_after_dedupe)
                if result.sample_size_after_dedupe is not None
                else "Not run"
            ),
        ),
        ("Decision Status", result.decision_status or "Not run"),
        (
            "Statistical Validity",
            result.statistical_validity or "Not run",
        ),
        ("Multidate Manifest", str(result.manifest_path)),
        ("Multidate Summary", str(result.summary_path)),
        ("Multidate Results", str(result.results_path)),
        ("Status", "completed"),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"multidate_run_id={result.multidate_run_id}")
    console.print(f"date_preset={result.date_preset or 'explicit'}")
    console.print(
        f"as_of_dates={','.join(result.resolved_as_of_dates)}"
    )
    console.print(f"usable_dates={','.join(result.usable_dates)}")
    console.print(f"skipped_dates={','.join(result.skipped_dates)}")
    console.print(f"date_coverage_status={result.date_coverage_status}")
    console.print(
        "coverage_quality_counts="
        f"{json.dumps(result.coverage_quality_counts, sort_keys=True)}"
    )
    console.print(
        "coverage_severity_counts="
        f"{json.dumps(result.coverage_severity_counts, sort_keys=True)}"
    )
    console.print(f"tickers={tickers}")
    console.print(f"total_expected_runs={result.total_expected_runs}")
    console.print(f"total_completed_runs={result.total_completed_runs}")
    console.print(f"total_failed_runs={result.total_failed_runs}")
    console.print(
        "trial_ledger_exported="
        f"{str(result.trial_ledger_exported).lower()}"
    )
    console.print(
        "readiness_backtest_run="
        f"{str(result.readiness_backtest_run).lower()}"
    )
    console.print(
        "sample_size_after_dedupe="
        f"{result.sample_size_after_dedupe or 0}"
    )
    console.print(f"decision_status={result.decision_status or 'not_run'}")
    console.print(
        "statistical_validity="
        f"{result.statistical_validity or 'not_run'}"
    )
    console.print("status=completed")


@app.command("run-expanded-ticker-readiness-trial")
def run_expanded_ticker_readiness_trial_command(
    eligible_universe: Annotated[
        Path,
        typer.Option(
            "--eligible-universe",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Coverage-validated eligible ticker universe YAML.",
        ),
    ],
    as_of_dates: Annotated[
        str | None,
        typer.Option(
            "--as-of-dates",
            help="Optional explicit dates; takes precedence over the preset.",
        ),
    ] = None,
    date_preset: Annotated[
        str | None,
        typer.Option(
            "--date-preset",
            help="Date preset: annual_3, semiannual_6, or quarterly_9.",
        ),
    ] = "semiannual_6",
    examples_root: Annotated[
        Path,
        typer.Option(
            "--examples-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
        ),
    ] = Path("examples"),
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            file_okay=False,
            dir_okay=True,
            writable=True,
        ),
    ] = Path("data/outputs"),
    fixtures_root: Annotated[
        Path,
        typer.Option(
            "--fixtures-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
        ),
    ] = Path("tests/fixtures"),
    portfolio_context_path: Annotated[
        Path | None,
        typer.Option(
            "--portfolio-context",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    financials_provider: Annotated[
        str,
        typer.Option("--financials-provider"),
    ] = "historical_csv",
    financials_root: Annotated[
        Path,
        typer.Option(
            "--financials-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
        ),
    ] = Path("tests/fixtures/historical_financials"),
    price_provider: Annotated[
        str,
        typer.Option("--price-provider"),
    ] = "csv",
    price_fixtures_path: Annotated[
        Path,
        typer.Option(
            "--price-fixtures",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
        ),
    ] = Path("tests/fixtures/historical_price_history"),
    export_trial_ledger: Annotated[
        bool,
        typer.Option("--export-trial-ledger"),
    ] = False,
    validate_trial_ledger: Annotated[
        bool,
        typer.Option("--validate-trial-ledger"),
    ] = False,
    run_readiness_backtest: Annotated[
        bool,
        typer.Option("--run-readiness-backtest"),
    ] = False,
    walk_forward: Annotated[
        bool,
        typer.Option("--walk-forward"),
    ] = False,
    trial_ledger_path: Annotated[
        Path,
        typer.Option("--trial-ledger"),
    ] = Path(
        "data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv"
    ),
) -> None:
    """Run a readiness-only trial from a coverage-validated universe."""
    if price_provider.strip().lower() != "csv":
        raise typer.BadParameter(
            "Expanded ticker readiness trial requires --price-provider csv."
        )
    try:
        result = run_expanded_ticker_readiness_trial(
            eligible_universe=eligible_universe,
            date_preset=date_preset,
            as_of_dates=as_of_dates,
            examples_root=examples_root,
            outputs_root=outputs_root,
            fixtures_root=fixtures_root,
            portfolio_context=portfolio_context_path,
            financials_provider=financials_provider,
            financials_root=financials_root,
            price_fixtures_path=price_fixtures_path,
            export_trial_ledger=export_trial_ledger,
            validate_trial_ledger=validate_trial_ledger,
            run_readiness_backtest=run_readiness_backtest,
            walk_forward=walk_forward,
            trial_ledger_path=trial_ledger_path,
        )
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise typer.BadParameter(
            f"Expanded ticker readiness trial failed: {exc}"
        ) from exc

    table = Table(title="Expanded Ticker Readiness Trial")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Expanded Trial Run ID", result.expanded_trial_run_id),
        (
            "Source Validation Run ID",
            result.source_validation_run_id or "Unknown",
        ),
        ("Eligible Ticker Count", str(len(result.eligible_tickers))),
        ("Eligible Tickers", ",".join(result.eligible_tickers)),
        ("Requested Dates", ",".join(result.requested_dates)),
        ("Usable Dates", ",".join(result.usable_dates) or "None"),
        ("Skipped Dates", ",".join(result.skipped_dates) or "None"),
        ("Completed Runs", str(result.completed_runs)),
        ("Failed Runs", str(result.failed_runs)),
        (
            "Trial Ledger Validation",
            result.trial_ledger_validation_status,
        ),
        ("Backtest Run ID", result.backtest_run_id or "Not run"),
        (
            "Sample Size After Dedupe",
            str(result.sample_size_after_dedupe or 0),
        ),
        ("Clean Records", str(result.clean_record_count)),
        ("Warning Records", str(result.warning_record_count)),
        ("Warning-Heavy Records", str(result.warning_heavy_record_count)),
        ("Diagnostic Status", result.diagnostic_status or "Not run"),
        ("Decision Status", result.decision_status or "Not run"),
        (
            "Walk-Forward Stability",
            result.walk_forward_stability_judgment or "Not run",
        ),
        ("Summary Report Path", str(result.summary_path)),
        ("Status", result.status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"expanded_trial_run_id={result.expanded_trial_run_id}")
    console.print(
        f"source_validation_run_id={result.source_validation_run_id or ''}"
    )
    console.print(f"eligible_ticker_count={len(result.eligible_tickers)}")
    console.print(f"completed_runs={result.completed_runs}")
    console.print(f"failed_runs={result.failed_runs}")
    console.print(f"backtest_run_id={result.backtest_run_id or ''}")
    console.print(
        f"sample_size_after_dedupe={result.sample_size_after_dedupe or 0}"
    )
    console.print(f"status={result.status}")


@app.command("analyze-expanded-trial-results")
def analyze_expanded_trial_results_command(
    expanded_trial_run_id: Annotated[
        str | None,
        typer.Option(
            "--expanded-trial-run-id",
            help="Expanded ticker trial run identifier to analyze.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Analyze the latest expanded ticker trial manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing expanded trial and backtest outputs.",
        ),
    ] = Path("data/outputs"),
    prior_backtest_run_id: Annotated[
        str,
        typer.Option(
            "--prior-backtest-run-id",
            help="Prior readiness trial backtest used for comparison.",
        ),
    ] = "20260614_205804",
    backtest_run_id: Annotated[
        str | None,
        typer.Option(
            "--backtest-run-id",
            help="Optional backtest override for the selected expanded trial.",
        ),
    ] = None,
) -> None:
    """Explain expanded readiness trial instability from existing outputs."""
    if bool(expanded_trial_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --expanded-trial-run-id or --auto-latest."
        )
    try:
        files = write_expanded_trial_analysis_report(
            outputs_root=outputs_root,
            expanded_trial_run_id=(
                None if auto_latest else expanded_trial_run_id
            ),
            backtest_run_id=backtest_run_id,
            prior_backtest_run_id=prior_backtest_run_id,
        )
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise typer.BadParameter(
            f"Expanded trial results analysis failed: {exc}"
        ) from exc

    report = files.report
    explanation = report.expanded_trial_instability_explanation
    diversity = report.metadata_diversity_recheck
    table = Table(title="Expanded Trial Results Analysis")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Analysis Run ID", report.analysis_run_id),
        ("Expanded Trial Run ID", report.expanded_trial_run_id),
        ("Backtest Run ID", report.backtest_run_id),
        ("Prior Backtest Run ID", report.prior_backtest_run_id),
        ("Analysis Status", report.analysis_status),
        (
            "Metadata Diversity Status",
            diversity["metadata_diversity_status"],
        ),
        (
            "Primary Instability Drivers",
            ",".join(explanation["primary_instability_drivers"]) or "None",
        ),
        ("Next Research Action", report.next_research_action),
        ("Report Path", str(files.markdown_path)),
        ("Status", "completed"),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"analysis_run_id={report.analysis_run_id}")
    console.print(f"expanded_trial_run_id={report.expanded_trial_run_id}")
    console.print(f"backtest_run_id={report.backtest_run_id}")
    console.print(f"analysis_status={report.analysis_status}")
    console.print(
        "metadata_diversity_status="
        f"{diversity['metadata_diversity_status']}"
    )
    console.print(f"next_research_action={report.next_research_action}")
    console.print("status=completed")


@app.command("build-research-evidence-scorecard")
def build_research_evidence_scorecard_command(
    analysis_run_id: Annotated[
        str | None,
        typer.Option(
            "--analysis-run-id",
            help="Expanded trial analysis run used by the scorecard.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest expanded trial analysis manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing analysis, trial, and backtest outputs.",
        ),
    ] = Path("data/outputs"),
    expanded_trial_run_id: Annotated[
        str | None,
        typer.Option(
            "--expanded-trial-run-id",
            help="Optional expanded trial run override.",
        ),
    ] = None,
    backtest_run_id: Annotated[
        str | None,
        typer.Option(
            "--backtest-run-id",
            help="Optional expanded trial backtest override.",
        ),
    ] = None,
    prior_backtest_run_id: Annotated[
        str | None,
        typer.Option(
            "--prior-backtest-run-id",
            help="Optional prior readiness trial comparison override.",
        ),
    ] = None,
) -> None:
    """Consolidate expanded trial diagnostics into a research scorecard."""
    if bool(analysis_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --analysis-run-id or --auto-latest."
        )
    try:
        files = write_research_evidence_scorecard_report(
            outputs_root=outputs_root,
            analysis_run_id=None if auto_latest else analysis_run_id,
            expanded_trial_run_id=expanded_trial_run_id,
            backtest_run_id=backtest_run_id,
            prior_backtest_run_id=prior_backtest_run_id,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Research evidence scorecard failed: {exc}"
        ) from exc

    scorecard = files.scorecard
    table = Table(title="Research Evidence Scorecard")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Scorecard Run ID", scorecard.scorecard_run_id),
        ("Analysis Run ID", scorecard.analysis_run_id),
        ("Expanded Trial Run ID", scorecard.expanded_trial_run_id),
        ("Backtest Run ID", scorecard.backtest_run_id),
        ("Classification", scorecard.research_evidence_classification),
        ("Research Decision", scorecard.research_decision),
        ("Raw Score", str(scorecard.raw_score)),
        (
            "Normalized Score",
            f"{scorecard.normalized_score_percent}%",
        ),
        ("Positive Factors", str(len(scorecard.positive_factors))),
        ("Warning Factors", str(scorecard.warning_factor_count)),
        ("Negative Factors", str(scorecard.negative_factor_count)),
        ("Blocker Factors", str(scorecard.blocker_count)),
        (
            "Next Research Action",
            scorecard.recommended_next_research_action,
        ),
        ("Report Path", str(files.markdown_path)),
        ("Status", scorecard.scorecard_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"scorecard_run_id={scorecard.scorecard_run_id}")
    console.print(f"analysis_run_id={scorecard.analysis_run_id}")
    console.print(
        "research_evidence_classification="
        f"{scorecard.research_evidence_classification}"
    )
    console.print(f"research_decision={scorecard.research_decision}")
    console.print(
        "next_research_action="
        f"{scorecard.recommended_next_research_action}"
    )
    console.print(f"status={scorecard.scorecard_status}")


@app.command("run-research-gatekeeper")
def run_research_gatekeeper_command(
    scorecard_run_id: Annotated[
        str | None,
        typer.Option(
            "--scorecard-run-id",
            help="Research evidence scorecard run used by the gatekeeper.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest research evidence scorecard manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing research evidence scorecard outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Convert a research evidence scorecard into a governance verdict."""
    if bool(scorecard_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --scorecard-run-id or --auto-latest."
        )
    try:
        files = write_research_gatekeeper_report(
            outputs_root=outputs_root,
            scorecard_run_id=None if auto_latest else scorecard_run_id,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Research gatekeeper failed: {exc}"
        ) from exc

    report = files.report
    table = Table(title="Research Gatekeeper")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Gatekeeper Run ID", report.gatekeeper_run_id),
        ("Scorecard Run ID", report.scorecard_run_id),
        (
            "Classification",
            report.research_evidence_classification,
        ),
        ("Research Decision", report.research_decision),
        ("Gatekeeper Decision", report.gatekeeper_decision),
        ("Progression Allowed", str(report.progression_allowed).lower()),
        ("Hold Bias", str(report.hold_bias).lower()),
        ("Hold Rules", str(len(report.hold_rules))),
        ("Block Rules", str(len(report.block_rules))),
        (
            "Next Research Action",
            report.recommended_next_research_action,
        ),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.gatekeeper_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"gatekeeper_run_id={report.gatekeeper_run_id}")
    console.print(f"scorecard_run_id={report.scorecard_run_id}")
    console.print(f"gatekeeper_decision={report.gatekeeper_decision}")
    console.print(
        f"progression_allowed={str(report.progression_allowed).lower()}"
    )
    console.print(f"hold_bias={str(report.hold_bias).lower()}")
    console.print(
        "next_research_action="
        f"{report.recommended_next_research_action}"
    )
    console.print(f"status={report.gatekeeper_status}")


@app.command("build-investor-persona-attribution")
def build_investor_persona_attribution_command(
    gatekeeper_run_id: Annotated[
        str | None,
        typer.Option(
            "--gatekeeper-run-id",
            help="Research gatekeeper run used by the attribution report.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest research gatekeeper manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing gatekeeper and linked research outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Map held research evidence to independent persona evidence needs."""
    if bool(gatekeeper_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --gatekeeper-run-id or --auto-latest."
        )
    try:
        files = write_investor_persona_attribution_report(
            outputs_root=outputs_root,
            gatekeeper_run_id=(
                None if auto_latest else gatekeeper_run_id
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Investor persona attribution failed: {exc}"
        ) from exc

    report = files.report
    summary = report.cross_persona_summary
    table = Table(title="Investor-Agent Attribution by Persona")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Attribution Run ID", report.attribution_run_id),
        ("Gatekeeper Run ID", report.gatekeeper_run_id),
        ("Gatekeeper Decision", report.gatekeeper_decision),
        ("Progression Allowed", str(report.progression_allowed).lower()),
        ("Hold Bias", str(report.hold_bias).lower()),
        ("Attribution Status", report.attribution_status),
        (
            "Personas Not Ready",
            str(summary["personas_not_ready_count"]),
        ),
        (
            "Personas Repair Possible",
            str(summary["personas_repair_possible_count"]),
        ),
        (
            "Personas Watchlist Only",
            str(summary["personas_watchlist_only_count"]),
        ),
        ("Personas Ready", str(summary["personas_ready_count"])),
        (
            "Next Research Action",
            report.recommended_next_research_action,
        ),
        ("Report Path", str(files.markdown_path)),
        ("Status", "completed"),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"attribution_run_id={report.attribution_run_id}")
    console.print(f"gatekeeper_run_id={report.gatekeeper_run_id}")
    console.print(f"attribution_status={report.attribution_status}")
    console.print(
        f"progression_allowed={str(report.progression_allowed).lower()}"
    )
    console.print(
        "next_research_action="
        f"{report.recommended_next_research_action}"
    )
    console.print("status=completed")


@app.command("build-backoffice-evidence-quality-attribution")
def build_backoffice_evidence_quality_attribution_command(
    persona_attribution_run_id: Annotated[
        str | None,
        typer.Option(
            "--persona-attribution-run-id",
            help="Investor persona attribution run used for repair planning.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest investor persona attribution manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing persona and linked research outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Translate a held persona state into Backoffice repair work."""
    if bool(persona_attribution_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --persona-attribution-run-id or "
            "--auto-latest."
        )
    try:
        files = write_backoffice_evidence_quality_report(
            outputs_root=outputs_root,
            attribution_run_id=(
                None if auto_latest else persona_attribution_run_id
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Backoffice evidence quality attribution failed: {exc}"
        ) from exc

    report = files.report
    summary = report.backoffice_attribution_summary
    table = Table(title="Backoffice Evidence Quality Attribution")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        (
            "Backoffice Attribution Run ID",
            report.backoffice_attribution_run_id,
        ),
        (
            "Persona Attribution Run ID",
            report.investor_persona_attribution_run_id,
        ),
        ("Gatekeeper Run ID", report.gatekeeper_run_id),
        ("Gatekeeper Decision", report.gatekeeper_decision),
        ("Progression Allowed", str(report.progression_allowed).lower()),
        ("Attribution Status", report.attribution_status),
        ("Total Issues", str(summary["total_issues"])),
        ("P0 Issues", str(summary["p0_issues"])),
        ("P1 Issues", str(summary["p1_issues"])),
        ("Total Work Orders", str(summary["total_work_orders"])),
        (
            "Next Research Action",
            report.recommended_next_research_action,
        ),
        ("Report Path", str(files.markdown_path)),
        ("Status", "completed"),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(
        "backoffice_attribution_run_id="
        f"{report.backoffice_attribution_run_id}"
    )
    console.print(
        "persona_attribution_run_id="
        f"{report.investor_persona_attribution_run_id}"
    )
    console.print(f"attribution_status={report.attribution_status}")
    console.print(
        f"progression_allowed={str(report.progression_allowed).lower()}"
    )
    console.print(
        "next_research_action="
        f"{report.recommended_next_research_action}"
    )
    console.print("status=completed")


@app.command("build-backtest-driver-decomposition")
def build_backtest_driver_decomposition_command(
    backoffice_attribution_run_id: Annotated[
        str | None,
        typer.Option(
            "--backoffice-attribution-run-id",
            help="Backoffice attribution run used to execute BO-001.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest Backoffice attribution manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing Backoffice and expanded backtest outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Execute BO-001 backtest driver decomposition."""
    if bool(backoffice_attribution_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --backoffice-attribution-run-id or "
            "--auto-latest."
        )
    try:
        files = write_backtest_driver_decomposition_report(
            outputs_root=outputs_root,
            backoffice_attribution_run_id=(
                None if auto_latest else backoffice_attribution_run_id
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Backtest driver decomposition failed: {exc}"
        ) from exc

    report = files.report
    summary = report.driver_summary
    table = Table(title="Backtest Driver Decomposition")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Decomposition Run ID", report.decomposition_run_id),
        (
            "Backoffice Attribution Run ID",
            report.backoffice_attribution_run_id,
        ),
        ("Work Order ID", report.work_order_id),
        ("Backtest Run ID", report.backtest_run_id),
        ("Rows Reconciled", str(report.reconciliation["rows_reconciled"])),
        (
            "Reconciliation Status",
            report.reconciliation["reconciliation_status"],
        ),
        (
            "Primary Negative Drivers",
            ",".join(summary["primary_negative_drivers"]) or "None",
        ),
        ("Recommended Next Work Order", report.recommended_next_work_order),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.decomposition_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"decomposition_run_id={report.decomposition_run_id}")
    console.print(
        "backoffice_attribution_run_id="
        f"{report.backoffice_attribution_run_id}"
    )
    console.print(
        f"reconciliation_status={report.reconciliation['reconciliation_status']}"
    )
    console.print(f"rows_reconciled={report.reconciliation['rows_reconciled']}")
    console.print(f"recommended_next_work_order={report.recommended_next_work_order}")
    console.print(f"status={report.decomposition_status}")


@app.command("build-outlier-repair-path")
def build_outlier_repair_path_command(
    decomposition_run_id: Annotated[
        str | None,
        typer.Option(
            "--decomposition-run-id",
            help="Backtest driver decomposition run used to execute BO-002.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest backtest driver decomposition manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing decomposition and expanded backtest outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Execute BO-002 outlier and Ex-NVDA repair path."""
    if bool(decomposition_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --decomposition-run-id or --auto-latest."
        )
    try:
        files = write_outlier_repair_path_report(
            outputs_root=outputs_root,
            decomposition_run_id=None if auto_latest else decomposition_run_id,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(f"Outlier repair path failed: {exc}") from exc

    report = files.report
    dependence = report.dependence_classification
    table = Table(title="Outlier and Ex-NVDA Repair Path")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Outlier Repair Run ID", report.outlier_repair_run_id),
        ("Decomposition Run ID", report.decomposition_run_id),
        ("Work Order ID", report.work_order_id),
        ("Backtest Run ID", report.backtest_run_id),
        ("Scenario Count", str(len(report.scenario_analysis))),
        (
            "Overall Outlier Repair Status",
            dependence["overall_outlier_repair_status"],
        ),
        ("Main Outlier Finding", dependence["main_outlier_finding"]),
        ("Recommended Next Work Order", report.recommended_next_work_order),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.outlier_repair_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"outlier_repair_run_id={report.outlier_repair_run_id}")
    console.print(f"decomposition_run_id={report.decomposition_run_id}")
    console.print(
        "overall_outlier_repair_status="
        f"{dependence['overall_outlier_repair_status']}"
    )
    console.print(f"scenario_count={len(report.scenario_analysis)}")
    console.print(f"recommended_next_work_order={report.recommended_next_work_order}")
    console.print(f"status={report.outlier_repair_status}")


@app.command("build-walk-forward-repair-plan")
def build_walk_forward_repair_plan_command(
    outlier_repair_run_id: Annotated[
        str | None,
        typer.Option(
            "--outlier-repair-run-id",
            help="Outlier repair run used to execute BO-003.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest outlier repair path manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing outlier repair and expanded backtest outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Execute BO-003 walk-forward stability repair plan."""
    if bool(outlier_repair_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --outlier-repair-run-id or --auto-latest."
        )
    try:
        files = write_walk_forward_repair_plan_report(
            outputs_root=outputs_root,
            outlier_repair_run_id=None if auto_latest else outlier_repair_run_id,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Walk-forward repair plan failed: {exc}"
        ) from exc

    report = files.report
    main_finding = (
        "Post-2021 periods break benchmark-relative stability while "
        "2021-06-30 remains supportive."
    )
    table = Table(title="Walk-Forward Stability Repair Plan")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Walk-Forward Repair Run ID", report.walk_forward_repair_run_id),
        ("Outlier Repair Run ID", report.outlier_repair_run_id),
        ("Work Order ID", report.work_order_id),
        ("Backtest Run ID", report.backtest_run_id),
        ("Period Count", str(len(report.period_stability_analysis))),
        ("Failure Mode Count", str(len(report.stability_failure_modes))),
        ("Main Stability Finding", main_finding),
        ("Recommended Next Work Order", report.recommended_next_work_order),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.walk_forward_repair_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(
        f"walk_forward_repair_run_id={report.walk_forward_repair_run_id}"
    )
    console.print(f"outlier_repair_run_id={report.outlier_repair_run_id}")
    console.print(f"period_count={len(report.period_stability_analysis)}")
    console.print(f"failure_mode_count={len(report.stability_failure_modes)}")
    console.print(f"recommended_next_work_order={report.recommended_next_work_order}")
    console.print(f"status={report.walk_forward_repair_status}")


@app.command("build-delayed-anchor-repair")
def build_delayed_anchor_repair_command(
    walk_forward_repair_run_id: Annotated[
        str | None,
        typer.Option(
            "--walk-forward-repair-run-id",
            help="Walk-forward repair run used to execute BO-004.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest walk-forward repair manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing walk-forward repair and backtest outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Execute BO-004 delayed anchor exposure repair."""
    if bool(walk_forward_repair_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --walk-forward-repair-run-id or --auto-latest."
        )
    try:
        files = write_delayed_anchor_repair_report(
            outputs_root=outputs_root,
            walk_forward_repair_run_id=(
                None if auto_latest else walk_forward_repair_run_id
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Delayed anchor repair failed: {exc}"
        ) from exc

    report = files.report
    classification = report.anchor_impact_classification
    table = Table(title="Delayed Anchor Exposure Repair")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Delayed Anchor Repair Run ID", report.delayed_anchor_repair_run_id),
        ("Walk-Forward Repair Run ID", report.walk_forward_repair_run_id),
        ("Work Order ID", report.work_order_id),
        ("Backtest Run ID", report.backtest_run_id),
        ("Anchor Bucket Count", str(len(report.anchor_exposure_analysis))),
        (
            "Anchor Data Sufficiency",
            classification["anchor_data_sufficiency_status"],
        ),
        ("Main Anchor Finding", classification["main_anchor_finding"]),
        ("Recommended Next Work Order", report.recommended_next_work_order),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.delayed_anchor_repair_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(
        f"delayed_anchor_repair_run_id={report.delayed_anchor_repair_run_id}"
    )
    console.print(f"walk_forward_repair_run_id={report.walk_forward_repair_run_id}")
    console.print(f"anchor_bucket_count={len(report.anchor_exposure_analysis)}")
    console.print(
        "anchor_data_sufficiency_status="
        f"{classification['anchor_data_sufficiency_status']}"
    )
    console.print(f"recommended_next_work_order={report.recommended_next_work_order}")
    console.print(f"status={report.delayed_anchor_repair_status}")


@app.command("build-metadata-diversity-recheck")
def build_metadata_diversity_recheck_command(
    delayed_anchor_repair_run_id: Annotated[
        str | None,
        typer.Option(
            "--delayed-anchor-repair-run-id",
            help="Delayed anchor repair run used to execute BO-005.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest delayed anchor repair manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing delayed anchor repair and backtest outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Execute BO-005 metadata diversity recheck."""
    if bool(delayed_anchor_repair_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --delayed-anchor-repair-run-id or "
            "--auto-latest."
        )
    try:
        files = write_metadata_diversity_recheck_report(
            outputs_root=outputs_root,
            delayed_anchor_repair_run_id=(
                None if auto_latest else delayed_anchor_repair_run_id
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Metadata diversity recheck failed: {exc}"
        ) from exc

    report = files.report
    summary = report.metadata_matrix_summary
    classification = report.concentration_classification
    table = Table(title="Metadata Diversity Recheck")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        (
            "Metadata Diversity Recheck Run ID",
            report.metadata_diversity_recheck_run_id,
        ),
        ("Delayed Anchor Repair Run ID", report.delayed_anchor_repair_run_id),
        ("Work Order ID", report.work_order_id),
        ("Backtest Run ID", report.backtest_run_id),
        ("Ticker Count", str(summary["ticker_count"])),
        ("Sector Count", str(summary["sector_count"])),
        ("Category Count", str(summary["category_count"])),
        ("Universe Group Count", str(summary["universe_group_count"])),
        ("Metadata Diversity Status", classification["metadata_diversity_status"]),
        ("Main Metadata Finding", classification["main_metadata_finding"]),
        ("Recommended Next Work Order", report.recommended_next_work_order),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.metadata_diversity_recheck_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(
        "metadata_diversity_recheck_run_id="
        f"{report.metadata_diversity_recheck_run_id}"
    )
    console.print(
        f"delayed_anchor_repair_run_id={report.delayed_anchor_repair_run_id}"
    )
    console.print(f"ticker_count={summary['ticker_count']}")
    console.print(f"sector_count={summary['sector_count']}")
    console.print(f"category_count={summary['category_count']}")
    console.print(
        f"metadata_diversity_status={classification['metadata_diversity_status']}"
    )
    console.print(f"recommended_next_work_order={report.recommended_next_work_order}")
    console.print(f"status={report.metadata_diversity_recheck_status}")


@app.command("build-persona-evidence-pack-requirements")
def build_persona_evidence_pack_requirements_command(
    metadata_diversity_recheck_run_id: Annotated[
        str | None,
        typer.Option(
            "--metadata-diversity-recheck-run-id",
            help="Metadata diversity recheck run used to execute BO-006.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest metadata diversity recheck manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing metadata recheck and persona attribution outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Execute BO-006 persona evidence pack requirements."""
    if bool(metadata_diversity_recheck_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --metadata-diversity-recheck-run-id or "
            "--auto-latest."
        )
    try:
        files = write_persona_evidence_pack_requirements_report(
            outputs_root=outputs_root,
            metadata_diversity_recheck_run_id=(
                None if auto_latest else metadata_diversity_recheck_run_id
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Persona evidence pack requirements failed: {exc}"
        ) from exc

    report = files.report
    table = Table(title="Persona-Specific Evidence Pack Requirements")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Persona Evidence Pack Run ID", report.persona_evidence_pack_run_id),
        (
            "Metadata Diversity Recheck Run ID",
            report.metadata_diversity_recheck_run_id,
        ),
        ("Work Order ID", report.work_order_id),
        ("Gatekeeper Decision", "hold"),
        ("Progression Allowed", "false"),
        ("Persona Count", str(len(report.persona_checklists))),
        ("Requirement Rows", str(len(report.persona_requirement_matrix))),
        ("Recommended Next Work Order", report.recommended_next_work_order),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.persona_evidence_pack_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(
        f"persona_evidence_pack_run_id={report.persona_evidence_pack_run_id}"
    )
    console.print(
        "metadata_diversity_recheck_run_id="
        f"{report.metadata_diversity_recheck_run_id}"
    )
    console.print("gatekeeper_decision=hold")
    console.print("progression_allowed=false")
    console.print(f"persona_count={len(report.persona_checklists)}")
    console.print(f"requirement_rows={len(report.persona_requirement_matrix)}")
    console.print(f"recommended_next_work_order={report.recommended_next_work_order}")
    console.print(f"status={report.persona_evidence_pack_status}")


@app.command("build-bogle-benchmark-index-pack")
def build_bogle_benchmark_index_pack_command(
    persona_evidence_pack_run_id: Annotated[
        str | None,
        typer.Option(
            "--persona-evidence-pack-run-id",
            help="Persona evidence pack run used to execute BO-007.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest persona evidence pack manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing persona evidence pack and repair outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Execute BO-007 Bogle benchmark/index comparison pack."""
    if bool(persona_evidence_pack_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --persona-evidence-pack-run-id or "
            "--auto-latest."
        )
    try:
        files = write_bogle_benchmark_index_pack_report(
            outputs_root=outputs_root,
            persona_evidence_pack_run_id=(
                None if auto_latest else persona_evidence_pack_run_id
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Bogle benchmark/index pack failed: {exc}"
        ) from exc

    report = files.report
    summary = report.bogle_benchmark_summary
    table = Table(title="Bogle Benchmark / Index Comparison Pack")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Bogle Benchmark Pack Run ID", report.bogle_benchmark_pack_run_id),
        ("Persona Evidence Pack Run ID", report.persona_evidence_pack_run_id),
        ("Work Order ID", report.work_order_id),
        ("Gatekeeper Decision", summary["gatekeeper_decision"]),
        ("Progression Allowed", str(summary["progression_allowed"]).lower()),
        ("Bogle Review Allowed", str(summary["bogle_review_allowed"]).lower()),
        ("Index Comparison Rows", str(len(report.index_comparison_matrix))),
        ("Concentration Risk Rows", str(len(report.concentration_risk_matrix))),
        ("Recommended Next Work Order", report.recommended_next_work_order),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.bogle_benchmark_pack_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(
        f"bogle_benchmark_pack_run_id={report.bogle_benchmark_pack_run_id}"
    )
    console.print(
        f"persona_evidence_pack_run_id={report.persona_evidence_pack_run_id}"
    )
    console.print(f"gatekeeper_decision={summary['gatekeeper_decision']}")
    console.print(f"progression_allowed={str(summary['progression_allowed']).lower()}")
    console.print(f"bogle_review_allowed={str(summary['bogle_review_allowed']).lower()}")
    console.print(f"index_comparison_rows={len(report.index_comparison_matrix)}")
    console.print(f"concentration_risk_rows={len(report.concentration_risk_matrix)}")
    console.print(f"recommended_next_work_order={report.recommended_next_work_order}")
    console.print(f"status={report.bogle_benchmark_pack_status}")


@app.command("build-fisher-qualitative-growth-pack")
def build_fisher_qualitative_growth_pack_command(
    bogle_benchmark_pack_run_id: Annotated[
        str | None,
        typer.Option(
            "--bogle-benchmark-pack-run-id",
            help="Bogle benchmark pack run used to execute BO-008.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest Bogle benchmark pack manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing Bogle benchmark pack and repair outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Execute BO-008 Fisher qualitative growth evidence pack."""
    if bool(bogle_benchmark_pack_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --bogle-benchmark-pack-run-id or "
            "--auto-latest."
        )
    try:
        files = write_fisher_qualitative_growth_pack_report(
            outputs_root=outputs_root,
            bogle_benchmark_pack_run_id=(
                None if auto_latest else bogle_benchmark_pack_run_id
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Fisher qualitative growth pack failed: {exc}"
        ) from exc

    report = files.report
    summary = report.fisher_growth_summary
    table = Table(title="Fisher Qualitative Growth Evidence Pack")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Fisher Growth Pack Run ID", report.fisher_growth_pack_run_id),
        ("Bogle Benchmark Pack Run ID", report.bogle_benchmark_pack_run_id),
        ("Work Order ID", report.work_order_id),
        ("Gatekeeper Decision", summary["gatekeeper_decision"]),
        ("Progression Allowed", str(summary["progression_allowed"]).lower()),
        ("Fisher Review Allowed", str(summary["fisher_review_allowed"]).lower()),
        (
            "Qualitative Evidence Rows",
            str(len(report.fisher_qualitative_evidence_matrix)),
        ),
        (
            "Scuttlebutt Proxy Rows",
            str(len(report.fisher_scuttlebutt_proxy_matrix)),
        ),
        ("Growth Risk Rows", str(len(report.fisher_growth_risk_matrix))),
        ("Recommended Next Work Order", report.recommended_next_work_order),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.fisher_growth_pack_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"fisher_growth_pack_run_id={report.fisher_growth_pack_run_id}")
    console.print(f"bogle_benchmark_pack_run_id={report.bogle_benchmark_pack_run_id}")
    console.print(f"gatekeeper_decision={summary['gatekeeper_decision']}")
    console.print(f"progression_allowed={str(summary['progression_allowed']).lower()}")
    console.print(f"fisher_review_allowed={str(summary['fisher_review_allowed']).lower()}")
    console.print(
        f"qualitative_evidence_rows={len(report.fisher_qualitative_evidence_matrix)}"
    )
    console.print(
        f"scuttlebutt_proxy_rows={len(report.fisher_scuttlebutt_proxy_matrix)}"
    )
    console.print(f"growth_risk_rows={len(report.fisher_growth_risk_matrix)}")
    console.print(f"recommended_next_work_order={report.recommended_next_work_order}")
    console.print(f"status={report.fisher_growth_pack_status}")


@app.command("build-buffett-munger-quality-risk-pack")
def build_buffett_munger_quality_risk_pack_command(
    fisher_growth_pack_run_id: Annotated[
        str | None,
        typer.Option(
            "--fisher-growth-pack-run-id",
            help="Fisher growth pack run used to execute BO-009.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest Fisher growth pack manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing Fisher growth pack and repair outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Execute BO-009 Buffett/Munger quality and risk pack."""
    if bool(fisher_growth_pack_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --fisher-growth-pack-run-id or "
            "--auto-latest."
        )
    try:
        files = write_buffett_munger_quality_risk_pack_report(
            outputs_root=outputs_root,
            fisher_growth_pack_run_id=(
                None if auto_latest else fisher_growth_pack_run_id
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Buffett/Munger quality and risk pack failed: {exc}"
        ) from exc

    report = files.report
    buffett = report.buffett_quality_summary
    munger = report.munger_quality_summary
    table = Table(title="Buffett/Munger Quality and Risk Pack")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Buffett/Munger Pack Run ID", report.buffett_munger_pack_run_id),
        ("Fisher Growth Pack Run ID", report.fisher_growth_pack_run_id),
        ("Work Order ID", report.work_order_id),
        ("Gatekeeper Decision", buffett["gatekeeper_decision"]),
        ("Progression Allowed", str(buffett["progression_allowed"]).lower()),
        ("Buffett Review Allowed", str(buffett["buffett_review_allowed"]).lower()),
        ("Munger Review Allowed", str(munger["munger_review_allowed"]).lower()),
        ("Quality Evidence Rows", str(len(report.quality_evidence_matrix))),
        ("Munger Risk Rows", str(len(report.munger_inversion_risk_matrix))),
        ("Recommended Next Work Order", report.recommended_next_work_order),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.buffett_munger_pack_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(
        f"buffett_munger_pack_run_id={report.buffett_munger_pack_run_id}"
    )
    console.print(f"fisher_growth_pack_run_id={report.fisher_growth_pack_run_id}")
    console.print(f"gatekeeper_decision={buffett['gatekeeper_decision']}")
    console.print(f"progression_allowed={str(buffett['progression_allowed']).lower()}")
    console.print(
        f"buffett_review_allowed={str(buffett['buffett_review_allowed']).lower()}"
    )
    console.print(
        f"munger_review_allowed={str(munger['munger_review_allowed']).lower()}"
    )
    console.print(f"quality_evidence_rows={len(report.quality_evidence_matrix)}")
    console.print(f"munger_risk_rows={len(report.munger_inversion_risk_matrix)}")
    console.print(f"recommended_next_work_order={report.recommended_next_work_order}")
    console.print(f"status={report.buffett_munger_pack_status}")


@app.command("build-research-audit-trail-bundle")
def build_research_audit_trail_bundle_command(
    buffett_munger_pack_run_id: Annotated[
        str | None,
        typer.Option(
            "--buffett-munger-pack-run-id",
            help="Buffett/Munger pack run used to execute BO-010.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest Buffett/Munger pack manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing Buffett/Munger pack and repair outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Execute BO-010 research audit trail bundle."""
    if bool(buffett_munger_pack_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --buffett-munger-pack-run-id or "
            "--auto-latest."
        )
    try:
        files = write_research_audit_trail_bundle_report(
            outputs_root=outputs_root,
            buffett_munger_pack_run_id=(
                None if auto_latest else buffett_munger_pack_run_id
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Research audit trail bundle failed: {exc}"
        ) from exc

    report = files.report
    phase = report.phase_closure_summary
    table = Table(title="Research Audit Trail Bundle")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Research Audit Trail Run ID", report.research_audit_trail_run_id),
        ("Buffett/Munger Pack Run ID", report.buffett_munger_pack_run_id),
        ("Work Order ID", report.work_order_id),
        ("Gatekeeper Decision", phase["final_gatekeeper_decision"]),
        ("Progression Allowed", str(phase["progression_allowed"]).lower()),
        ("Current Phase", phase["current_phase_name"]),
        ("Phase Status", phase["phase_status"]),
        ("Completed Work Orders", str(phase["completed_work_orders"])),
        ("Recommended Next Phase", report.recommended_next_phase),
        ("Recommended Next Task", report.recommended_next_task),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.research_audit_trail_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(
        f"research_audit_trail_run_id={report.research_audit_trail_run_id}"
    )
    console.print(f"buffett_munger_pack_run_id={report.buffett_munger_pack_run_id}")
    console.print(f"gatekeeper_decision={phase['final_gatekeeper_decision']}")
    console.print(f"progression_allowed={str(phase['progression_allowed']).lower()}")
    console.print(f"current_phase={phase['current_phase_name']}")
    console.print(f"phase_status={phase['phase_status']}")
    console.print(f"completed_work_orders={phase['completed_work_orders']}")
    console.print(f"recommended_next_phase={report.recommended_next_phase}")
    console.print(f"recommended_next_task={report.recommended_next_task}")
    console.print(f"status={report.research_audit_trail_status}")


@app.command("build-re-run-re-gate-plan")
def build_re_run_re_gate_plan_command(
    research_audit_trail_run_id: Annotated[
        str | None,
        typer.Option(
            "--research-audit-trail-run-id",
            help="Research audit trail run used to define the Phase 16 plan.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest research audit trail manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing research audit trail and re-gate outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Define the Phase 16 re-run and re-gate plan without executing it."""
    if bool(research_audit_trail_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --research-audit-trail-run-id or "
            "--auto-latest."
        )
    try:
        files = write_re_run_re_gate_plan_report(
            outputs_root=outputs_root,
            research_audit_trail_run_id=(
                None if auto_latest else research_audit_trail_run_id
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(f"Re-run and re-gate plan failed: {exc}") from exc

    report = files.report
    context = report.phase_16_context
    table = Table(title="Re-Run & Re-Gate Plan")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Re-Run & Re-Gate Plan Run ID", report.re_run_re_gate_plan_run_id),
        ("Research Audit Trail Run ID", report.research_audit_trail_run_id),
        ("Current Phase", context["phase_name"]),
        ("Current Task", context["current_task_name"]),
        ("Gatekeeper Decision", context["gatekeeper_decision"]),
        ("Progression Allowed", str(context["progression_allowed"]).lower()),
        (
            "Persona Reviews Allowed",
            str(context["persona_reviews_allowed"]).lower(),
        ),
        ("Roadmap Tasks", str(len(report.phase_16_task_roadmap))),
        ("Recommended Next Task", report.recommended_next_task),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.plan_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(
        f"re_run_re_gate_plan_run_id={report.re_run_re_gate_plan_run_id}"
    )
    console.print(
        f"research_audit_trail_run_id={report.research_audit_trail_run_id}"
    )
    console.print(f"current_phase={context['phase_name']}")
    console.print(f"current_task={context['current_task_name']}")
    console.print(f"gatekeeper_decision={context['gatekeeper_decision']}")
    console.print(
        f"progression_allowed={str(context['progression_allowed']).lower()}"
    )
    console.print(
        "persona_reviews_allowed="
        f"{str(context['persona_reviews_allowed']).lower()}"
    )
    console.print(f"roadmap_tasks={len(report.phase_16_task_roadmap)}")
    console.print(f"recommended_next_task={report.recommended_next_task}")
    console.print(f"status={report.plan_status}")


@app.command("build-re-run-input-package")
def build_re_run_input_package_command(
    re_run_re_gate_plan_run_id: Annotated[
        str | None,
        typer.Option(
            "--re-run-re-gate-plan-run-id",
            help="Task 119 re-run/re-gate plan run used to build Task 120.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest re-run/re-gate plan manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing re-run/re-gate plan and input package outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Build Task 120 re-run input package without executing the re-run."""
    if bool(re_run_re_gate_plan_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --re-run-re-gate-plan-run-id or "
            "--auto-latest."
        )
    try:
        files = write_re_run_input_package_report(
            outputs_root=outputs_root,
            re_run_re_gate_plan_run_id=(
                None if auto_latest else re_run_re_gate_plan_run_id
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(f"Re-run input package failed: {exc}") from exc

    report = files.report
    summary = report.input_package_summary
    table = Table(title="Re-Run Input Package")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Re-Run Input Package Run ID", report.re_run_input_package_run_id),
        ("Re-Run & Re-Gate Plan Run ID", report.re_run_re_gate_plan_run_id),
        ("Current Phase", "16 - Re-Run & Re-Gate Layer"),
        ("Current Task", summary["current_task_name"]),
        ("Gatekeeper Decision", summary["gatekeeper_decision"]),
        ("Progression Allowed", str(summary["progression_allowed"]).lower()),
        (
            "Persona Reviews Allowed",
            str(summary["persona_reviews_allowed"]).lower(),
        ),
        ("Universe Rows", str(len(report.re_run_universe_matrix))),
        ("Date Rows", str(len(report.re_run_date_matrix))),
        ("Control Rows", str(len(report.re_run_control_matrix))),
        ("Recommended Next Task", report.recommended_next_task),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.package_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(
        f"re_run_input_package_run_id={report.re_run_input_package_run_id}"
    )
    console.print(
        f"re_run_re_gate_plan_run_id={report.re_run_re_gate_plan_run_id}"
    )
    console.print("current_phase=16 - Re-Run & Re-Gate Layer")
    console.print(f"current_task={summary['current_task_name']}")
    console.print(f"gatekeeper_decision={summary['gatekeeper_decision']}")
    console.print(
        f"progression_allowed={str(summary['progression_allowed']).lower()}"
    )
    console.print(
        "persona_reviews_allowed="
        f"{str(summary['persona_reviews_allowed']).lower()}"
    )
    console.print(f"universe_rows={len(report.re_run_universe_matrix)}")
    console.print(f"date_rows={len(report.re_run_date_matrix)}")
    console.print(f"control_rows={len(report.re_run_control_matrix)}")
    console.print(f"recommended_next_task={report.recommended_next_task}")
    console.print(f"status={report.package_status}")


@app.command("execute-controlled-re-run-trial")
def execute_controlled_re_run_trial_command(
    re_run_input_package_run_id: Annotated[
        str | None,
        typer.Option(
            "--re-run-input-package-run-id",
            help="Task 120 re-run input package used to execute Task 121.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest re-run input package manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing re-run input package and controlled trial outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Execute Task 121 controlled local re-run without rerunning Gatekeeper."""
    if bool(re_run_input_package_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --re-run-input-package-run-id or "
            "--auto-latest."
        )
    try:
        files = write_controlled_re_run_trial_report(
            outputs_root=outputs_root,
            re_run_input_package_run_id=(
                None if auto_latest else re_run_input_package_run_id
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(f"Controlled re-run trial failed: {exc}") from exc

    report = files.report
    summary = report.controlled_re_run_summary
    table = Table(title="Controlled Re-Run Trial")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Controlled Re-Run Trial Run ID", report.controlled_re_run_trial_run_id),
        ("Re-Run Input Package Run ID", report.re_run_input_package_run_id),
        ("Current Phase", "16 - Re-Run & Re-Gate Layer"),
        ("Current Task", summary["current_task_name"]),
        ("Gatekeeper Decision", summary["gatekeeper_decision"]),
        ("Progression Allowed", str(summary["progression_allowed"]).lower()),
        (
            "Persona Reviews Allowed",
            str(summary["persona_reviews_allowed"]).lower(),
        ),
        ("Scenario Rows", str(len(report.scenario_execution_plan))),
        ("Result Rows", str(len(report.scenario_results_matrix))),
        ("Control Rows", str(len(report.control_diagnostics_matrix))),
        ("Recommended Next Task", report.recommended_next_task),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.controlled_re_run_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(
        f"controlled_re_run_trial_run_id={report.controlled_re_run_trial_run_id}"
    )
    console.print(
        f"re_run_input_package_run_id={report.re_run_input_package_run_id}"
    )
    console.print("current_phase=16 - Re-Run & Re-Gate Layer")
    console.print(f"current_task={summary['current_task_name']}")
    console.print(f"gatekeeper_decision={summary['gatekeeper_decision']}")
    console.print(
        f"progression_allowed={str(summary['progression_allowed']).lower()}"
    )
    console.print(
        "persona_reviews_allowed="
        f"{str(summary['persona_reviews_allowed']).lower()}"
    )
    console.print(f"scenario_rows={len(report.scenario_execution_plan)}")
    console.print(f"result_rows={len(report.scenario_results_matrix)}")
    console.print(f"control_rows={len(report.control_diagnostics_matrix)}")
    console.print(f"recommended_next_task={report.recommended_next_task}")
    console.print(f"status={report.controlled_re_run_status}")


@app.command("compare-pre-post-repair-evidence")
def compare_pre_post_repair_evidence_command(
    controlled_re_run_trial_run_id: Annotated[
        str | None,
        typer.Option(
            "--controlled-re-run-trial-run-id",
            help="Task 121 controlled re-run trial used to execute Task 122.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest controlled re-run trial manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing controlled re-run and comparison outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Execute Task 122 pre/post repair comparison without rerunning Gatekeeper."""
    if bool(controlled_re_run_trial_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --controlled-re-run-trial-run-id or "
            "--auto-latest."
        )
    try:
        files = write_pre_post_repair_comparison_report(
            outputs_root=outputs_root,
            controlled_re_run_trial_run_id=(
                None if auto_latest else controlled_re_run_trial_run_id
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Pre/post repair evidence comparison failed: {exc}"
        ) from exc

    report = files.report
    summary = report.comparison_summary
    table = Table(title="Pre/Post Repair Evidence Comparison")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Pre/Post Repair Comparison Run ID", report.pre_post_repair_comparison_run_id),
        ("Controlled Re-Run Trial Run ID", report.controlled_re_run_trial_run_id),
        ("Current Phase", "16 - Re-Run & Re-Gate Layer"),
        ("Current Task", summary["current_task_name"]),
        ("Gatekeeper Decision", summary["gatekeeper_decision"]),
        ("Progression Allowed", str(summary["progression_allowed"]).lower()),
        (
            "Persona Reviews Allowed",
            str(summary["persona_reviews_allowed"]).lower(),
        ),
        ("Evidence Delta Rows", str(len(report.evidence_delta_matrix))),
        ("Scenario Delta Rows", str(len(report.scenario_delta_matrix))),
        ("Stability Rows", str(len(report.stability_delta_matrix))),
        ("Gatekeeper Readiness Rows", str(len(report.gatekeeper_readiness_delta))),
        ("Recommended Next Task", report.recommended_next_task),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.comparison_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(
        f"pre_post_repair_comparison_run_id={report.pre_post_repair_comparison_run_id}"
    )
    console.print(
        f"controlled_re_run_trial_run_id={report.controlled_re_run_trial_run_id}"
    )
    console.print("current_phase=16 - Re-Run & Re-Gate Layer")
    console.print(f"current_task={summary['current_task_name']}")
    console.print(f"gatekeeper_decision={summary['gatekeeper_decision']}")
    console.print(
        f"progression_allowed={str(summary['progression_allowed']).lower()}"
    )
    console.print(
        "persona_reviews_allowed="
        f"{str(summary['persona_reviews_allowed']).lower()}"
    )
    console.print(f"evidence_delta_rows={len(report.evidence_delta_matrix)}")
    console.print(f"scenario_delta_rows={len(report.scenario_delta_matrix)}")
    console.print(f"stability_rows={len(report.stability_delta_matrix)}")
    console.print(
        f"gatekeeper_readiness_rows={len(report.gatekeeper_readiness_delta)}"
    )
    console.print(f"recommended_next_task={report.recommended_next_task}")
    console.print(f"status={report.comparison_status}")


@app.command("run-gatekeeper-re-evaluation")
def run_gatekeeper_re_evaluation_command(
    pre_post_repair_comparison_run_id: Annotated[
        str | None,
        typer.Option(
            "--pre-post-repair-comparison-run-id",
            help="Task 122 comparison used to execute Task 123.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest pre/post repair comparison manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing comparison and Gatekeeper re-evaluation outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Execute Task 123 research Gatekeeper re-evaluation."""
    if bool(pre_post_repair_comparison_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --pre-post-repair-comparison-run-id or "
            "--auto-latest."
        )
    try:
        files = write_gatekeeper_re_evaluation_report(
            outputs_root=outputs_root,
            pre_post_repair_comparison_run_id=(
                None if auto_latest else pre_post_repair_comparison_run_id
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(f"Gatekeeper re-evaluation failed: {exc}") from exc

    report = files.report
    summary = report.re_evaluation_summary
    decision = report.re_gate_decision_record
    table = Table(title="Gatekeeper Re-Evaluation")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Gatekeeper Re-Evaluation Run ID", report.gatekeeper_re_evaluation_run_id),
        ("Pre/Post Repair Comparison Run ID", report.pre_post_repair_comparison_run_id),
        ("Current Phase", "16 - Re-Run & Re-Gate Layer"),
        ("Current Task", summary["current_task_name"]),
        ("Previous Gatekeeper Decision", summary["previous_gatekeeper_decision"]),
        ("New Gatekeeper Outcome", decision["new_gatekeeper_outcome"]),
        (
            "Progression Allowed After Re-Evaluation",
            str(decision["progression_allowed_after_re_evaluation"]).lower(),
        ),
        (
            "Persona Reviews Allowed After Re-Evaluation",
            str(decision["persona_reviews_allowed_after_re_evaluation"]).lower(),
        ),
        ("Recommended Next Task", report.recommended_next_task),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.gatekeeper_re_evaluation_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(
        f"gatekeeper_re_evaluation_run_id={report.gatekeeper_re_evaluation_run_id}"
    )
    console.print(
        f"pre_post_repair_comparison_run_id={report.pre_post_repair_comparison_run_id}"
    )
    console.print("current_phase=16 - Re-Run & Re-Gate Layer")
    console.print(f"current_task={summary['current_task_name']}")
    console.print(f"previous_gatekeeper_decision={summary['previous_gatekeeper_decision']}")
    console.print(f"new_gatekeeper_outcome={decision['new_gatekeeper_outcome']}")
    console.print(
        "progression_allowed_after_re_evaluation="
        f"{str(decision['progression_allowed_after_re_evaluation']).lower()}"
    )
    console.print(
        "persona_reviews_allowed_after_re_evaluation="
        f"{str(decision['persona_reviews_allowed_after_re_evaluation']).lower()}"
    )
    console.print(f"recommended_next_task={report.recommended_next_task}")
    console.print(f"status={report.gatekeeper_re_evaluation_status}")


@app.command("close-phase-16")
def close_phase_16_command(
    gatekeeper_re_evaluation_run_id: Annotated[
        str | None,
        typer.Option(
            "--gatekeeper-re-evaluation-run-id",
            help="Task 123 Gatekeeper re-evaluation used to close Phase 16.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest Gatekeeper re-evaluation manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing Gatekeeper re-evaluation and closure outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Execute Task 124 Phase 16 closure and next-phase recommendation."""
    if bool(gatekeeper_re_evaluation_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --gatekeeper-re-evaluation-run-id or "
            "--auto-latest."
        )
    try:
        files = write_phase_16_closure_report(
            outputs_root=outputs_root,
            gatekeeper_re_evaluation_run_id=(
                None if auto_latest else gatekeeper_re_evaluation_run_id
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(f"Phase 16 closure failed: {exc}") from exc

    report = files.report
    summary = report.phase_closure_summary
    table = Table(title="Phase 16 Closure")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Phase 16 Closure Run ID", report.phase_16_closure_run_id),
        ("Gatekeeper Re-Evaluation Run ID", report.gatekeeper_re_evaluation_run_id),
        ("Current Phase", "16 - Re-Run & Re-Gate Layer"),
        ("Current Task", summary["current_task_name"]),
        ("Phase Completion Status", report.phase_completion_status),
        ("Final Gatekeeper Outcome", report.final_gatekeeper_outcome),
        ("Final Progression Allowed", str(report.final_progression_allowed).lower()),
        (
            "Final Persona Reviews Allowed",
            str(report.final_persona_reviews_allowed).lower(),
        ),
        ("Recommended Next Phase", report.recommended_next_phase),
        ("Recommended Next Task", report.recommended_next_task),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.phase_completion_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"phase_16_closure_run_id={report.phase_16_closure_run_id}")
    console.print(
        f"gatekeeper_re_evaluation_run_id={report.gatekeeper_re_evaluation_run_id}"
    )
    console.print("current_phase=16 - Re-Run & Re-Gate Layer")
    console.print(f"current_task={summary['current_task_name']}")
    console.print(f"phase_completion_status={report.phase_completion_status}")
    console.print(f"final_gatekeeper_outcome={report.final_gatekeeper_outcome}")
    console.print(
        f"final_progression_allowed={str(report.final_progression_allowed).lower()}"
    )
    console.print(
        "final_persona_reviews_allowed="
        f"{str(report.final_persona_reviews_allowed).lower()}"
    )
    console.print(f"recommended_next_phase={report.recommended_next_phase}")
    console.print(f"recommended_next_task={report.recommended_next_task}")
    console.print(f"status={report.phase_completion_status}")


@app.command("define-targeted-evidence-stabilization-plan")
def define_targeted_evidence_stabilization_plan_command(
    phase_16_closure_run_id: Annotated[
        str | None,
        typer.Option(
            "--phase-16-closure-run-id",
            help="Task 124 Phase 16 closure used to start Phase 17 planning.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest Phase 16 closure manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing Phase 16 closure and stabilization outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Execute Task 125 targeted evidence stabilization planning."""
    if bool(phase_16_closure_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --phase-16-closure-run-id or --auto-latest."
        )
    try:
        files = write_targeted_evidence_stabilization_plan_report(
            outputs_root=outputs_root,
            phase_16_closure_run_id=(None if auto_latest else phase_16_closure_run_id),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Targeted evidence stabilization plan failed: {exc}"
        ) from exc

    report = files.report
    summary = report.stabilization_plan_summary
    table = Table(title="Targeted Evidence Stabilization Plan")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Stabilization Plan Run ID", report.stabilization_plan_run_id),
        ("Phase 16 Closure Run ID", report.phase_16_closure_run_id),
        ("Current Phase", "17 - Targeted Evidence Stabilization Layer"),
        ("Current Task", summary["current_task_name"]),
        (
            "Prior Gatekeeper Outcome",
            summary["prior_phase_final_gatekeeper_outcome"],
        ),
        (
            "Progression Allowed",
            str(summary["prior_phase_final_progression_allowed"]).lower(),
        ),
        (
            "Persona Reviews Allowed",
            str(summary["prior_phase_final_persona_reviews_allowed"]).lower(),
        ),
        ("Workstream Rows", str(len(report.stabilization_workstream_matrix))),
        ("Priority Rows", str(len(report.evidence_stabilization_priority_matrix))),
        ("Roadmap Rows", str(len(report.phase_17_execution_roadmap))),
        ("Recommended Next Task", report.recommended_next_task),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.plan_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"stabilization_plan_run_id={report.stabilization_plan_run_id}")
    console.print(f"phase_16_closure_run_id={report.phase_16_closure_run_id}")
    console.print("current_phase=17 - Targeted Evidence Stabilization Layer")
    console.print(f"current_task={summary['current_task_name']}")
    console.print(
        "prior_gatekeeper_outcome="
        f"{summary['prior_phase_final_gatekeeper_outcome']}"
    )
    console.print(
        "progression_allowed="
        f"{str(summary['prior_phase_final_progression_allowed']).lower()}"
    )
    console.print(
        "persona_reviews_allowed="
        f"{str(summary['prior_phase_final_persona_reviews_allowed']).lower()}"
    )
    console.print(
        f"workstream_rows={len(report.stabilization_workstream_matrix)}"
    )
    console.print(
        f"priority_rows={len(report.evidence_stabilization_priority_matrix)}"
    )
    console.print(f"roadmap_rows={len(report.phase_17_execution_roadmap)}")
    console.print(f"recommended_next_task={report.recommended_next_task}")
    console.print(f"status={report.plan_status}")


@app.command("build-residual-blocker-work-orders")
def build_residual_blocker_work_orders_command(
    stabilization_plan_run_id: Annotated[
        str | None,
        typer.Option(
            "--stabilization-plan-run-id",
            help="Task 125 stabilization plan used to build residual work orders.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest targeted evidence stabilization plan manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing stabilization plans and work-order outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Execute Task 126 residual blocker work-order packaging."""
    if bool(stabilization_plan_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --stabilization-plan-run-id or --auto-latest."
        )
    try:
        files = write_residual_blocker_work_order_report(
            outputs_root=outputs_root,
            stabilization_plan_run_id=(
                None if auto_latest else stabilization_plan_run_id
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Residual blocker work-order packaging failed: {exc}"
        ) from exc

    report = files.report
    summary = report.work_order_package_summary
    table = Table(title="Residual Blocker Work Orders")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Residual Work Order Package Run ID", report.residual_work_order_package_run_id),
        ("Stabilization Plan Run ID", report.stabilization_plan_run_id),
        ("Current Phase", "17 - Targeted Evidence Stabilization Layer"),
        ("Current Task", summary["current_task_name"]),
        ("Prior Gatekeeper Outcome", summary["prior_gatekeeper_outcome"]),
        ("Progression Allowed", str(summary["progression_allowed"]).lower()),
        ("Persona Reviews Allowed", str(summary["persona_reviews_allowed"]).lower()),
        ("Work Order Rows", str(len(report.residual_blocker_work_order_matrix))),
        ("Dependency Rows", str(len(report.work_order_dependency_matrix))),
        ("Input Rows", str(len(report.work_order_input_requirements_matrix))),
        ("Recommended Next Task", report.recommended_next_task),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.package_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(
        f"residual_work_order_package_run_id={report.residual_work_order_package_run_id}"
    )
    console.print(f"stabilization_plan_run_id={report.stabilization_plan_run_id}")
    console.print("current_phase=17 - Targeted Evidence Stabilization Layer")
    console.print(f"current_task={summary['current_task_name']}")
    console.print(f"prior_gatekeeper_outcome={summary['prior_gatekeeper_outcome']}")
    console.print(
        f"progression_allowed={str(summary['progression_allowed']).lower()}"
    )
    console.print(
        f"persona_reviews_allowed={str(summary['persona_reviews_allowed']).lower()}"
    )
    console.print(f"work_order_rows={len(report.residual_blocker_work_order_matrix)}")
    console.print(f"dependency_rows={len(report.work_order_dependency_matrix)}")
    console.print(f"input_rows={len(report.work_order_input_requirements_matrix)}")
    console.print(f"recommended_next_task={report.recommended_next_task}")
    console.print(f"status={report.package_status}")


@app.command("execute-targeted-evidence-repairs")
def execute_targeted_evidence_repairs_command(
    residual_work_order_package_run_id: Annotated[
        str | None,
        typer.Option(
            "--residual-work-order-package-run-id",
            help="Task 126 residual work-order package used for Task 127 repairs.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest residual blocker work-order manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing work-order packages and repair outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Execute Task 127 targeted evidence repairs."""
    if bool(residual_work_order_package_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --residual-work-order-package-run-id or "
            "--auto-latest."
        )
    try:
        files = write_targeted_evidence_repairs_report(
            outputs_root=outputs_root,
            residual_work_order_package_run_id=(
                None if auto_latest else residual_work_order_package_run_id
            ),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(f"Targeted evidence repairs failed: {exc}") from exc

    report = files.report
    summary = report.repair_execution_summary
    table = Table(title="Targeted Evidence Repairs")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Targeted Repair Run ID", report.targeted_repair_run_id),
        ("Residual Work Order Package Run ID", report.residual_work_order_package_run_id),
        ("Current Phase", "17 - Targeted Evidence Stabilization Layer"),
        ("Current Task", summary["current_task_name"]),
        ("Prior Gatekeeper Outcome", summary["prior_gatekeeper_outcome"]),
        ("Progression Allowed", str(summary["progression_allowed"]).lower()),
        ("Persona Reviews Allowed", str(summary["persona_reviews_allowed"]).lower()),
        ("Work Orders Total", str(summary["work_orders_total"])),
        ("Work Orders Completed", str(summary["work_orders_completed"])),
        (
            "Work Orders Partially Completed",
            str(summary["work_orders_partially_completed"]),
        ),
        ("Work Orders Blocked", str(summary["work_orders_blocked"])),
        ("Recommended Next Task", report.recommended_next_task),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.repair_execution_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"targeted_repair_run_id={report.targeted_repair_run_id}")
    console.print(
        f"residual_work_order_package_run_id={report.residual_work_order_package_run_id}"
    )
    console.print("current_phase=17 - Targeted Evidence Stabilization Layer")
    console.print(f"current_task={summary['current_task_name']}")
    console.print(f"prior_gatekeeper_outcome={summary['prior_gatekeeper_outcome']}")
    console.print(
        f"progression_allowed={str(summary['progression_allowed']).lower()}"
    )
    console.print(
        f"persona_reviews_allowed={str(summary['persona_reviews_allowed']).lower()}"
    )
    console.print(f"work_orders_total={summary['work_orders_total']}")
    console.print(f"work_orders_completed={summary['work_orders_completed']}")
    console.print(
        "work_orders_partially_completed="
        f"{summary['work_orders_partially_completed']}"
    )
    console.print(f"work_orders_blocked={summary['work_orders_blocked']}")
    console.print(f"recommended_next_task={report.recommended_next_task}")
    console.print(f"status={report.repair_execution_status}")


@app.command("run-stabilization-validation-trial")
def run_stabilization_validation_trial_command(
    targeted_repair_run_id: Annotated[
        str | None,
        typer.Option(
            "--targeted-repair-run-id",
            help="Task 127 targeted repair run used for Task 128 validation.",
        ),
    ] = None,
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Use the latest targeted evidence repairs manifest.",
        ),
    ] = False,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing targeted repair and validation outputs.",
        ),
    ] = Path("data/outputs"),
) -> None:
    """Execute Task 128 stabilization validation trial."""
    if bool(targeted_repair_run_id) == bool(auto_latest):
        raise typer.BadParameter(
            "Provide exactly one of --targeted-repair-run-id or --auto-latest."
        )
    try:
        files = write_stabilization_validation_trial_report(
            outputs_root=outputs_root,
            targeted_repair_run_id=(None if auto_latest else targeted_repair_run_id),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Stabilization validation trial failed: {exc}"
        ) from exc

    report = files.report
    summary = report.validation_trial_summary
    table = Table(title="Stabilization Validation Trial")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Stabilization Validation Run ID", report.stabilization_validation_run_id),
        ("Targeted Repair Run ID", report.targeted_repair_run_id),
        ("Current Phase", "17 - Targeted Evidence Stabilization Layer"),
        ("Current Task", summary["current_task_name"]),
        ("Prior Gatekeeper Outcome", summary["prior_gatekeeper_outcome"]),
        ("Progression Allowed", str(summary["progression_allowed"]).lower()),
        ("Persona Reviews Allowed", str(summary["persona_reviews_allowed"]).lower()),
        ("Work Orders Total", str(summary["work_orders_total"])),
        ("Work Orders Validated", str(summary["work_orders_validated"])),
        (
            "Work Orders Partially Validated",
            str(summary["work_orders_partially_validated"]),
        ),
        ("Work Orders Failed", str(summary["work_orders_failed"])),
        ("Work Orders Not Testable", str(summary["work_orders_not_testable"])),
        ("Recommended Next Task", report.recommended_next_task),
        ("Report Path", str(files.markdown_path)),
        ("Status", report.validation_trial_status),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(
        f"stabilization_validation_run_id={report.stabilization_validation_run_id}"
    )
    console.print(f"targeted_repair_run_id={report.targeted_repair_run_id}")
    console.print("current_phase=17 - Targeted Evidence Stabilization Layer")
    console.print(f"current_task={summary['current_task_name']}")
    console.print(f"prior_gatekeeper_outcome={summary['prior_gatekeeper_outcome']}")
    console.print(
        f"progression_allowed={str(summary['progression_allowed']).lower()}"
    )
    console.print(
        f"persona_reviews_allowed={str(summary['persona_reviews_allowed']).lower()}"
    )
    console.print(f"work_orders_total={summary['work_orders_total']}")
    console.print(f"work_orders_validated={summary['work_orders_validated']}")
    console.print(
        f"work_orders_partially_validated={summary['work_orders_partially_validated']}"
    )
    console.print(f"work_orders_failed={summary['work_orders_failed']}")
    console.print(f"work_orders_not_testable={summary['work_orders_not_testable']}")
    console.print(f"recommended_next_task={report.recommended_next_task}")
    console.print(f"status={report.validation_trial_status}")


@app.command("run-historical-readiness-batch")
def run_historical_readiness_batch_command(
    tickers: Annotated[
        str,
        typer.Option(
            "--tickers",
            help="Comma-separated ticker symbols for historical readiness.",
        ),
    ],
    as_of_date: Annotated[
        str,
        typer.Option(
            "--as-of-date",
            help="Shared historical readiness date in YYYY-MM-DD format.",
        ),
    ] = "2023-06-30",
    examples_root: Annotated[
        Path,
        typer.Option(
            "--examples-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing manual input packs.",
        ),
    ] = Path("examples"),
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Root directory for ticker, batch, and backtest outputs.",
        ),
    ] = Path("data/outputs"),
    fixtures_root: Annotated[
        Path,
        typer.Option(
            "--fixtures-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing offline enrichment fixtures.",
        ),
    ] = Path("tests/fixtures"),
    portfolio_context_path: Annotated[
        Path | None,
        typer.Option(
            "--portfolio-context",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Optional portfolio context for independent Bogle analysis.",
        ),
    ] = None,
    financials_provider: Annotated[
        str,
        typer.Option(
            "--financials-provider",
            help="Historical financials provider; currently historical_csv.",
        ),
    ] = "historical_csv",
    financials_root: Annotated[
        Path,
        typer.Option(
            "--financials-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing point-in-time financials CSV files.",
        ),
    ] = Path("tests/fixtures/historical_financials"),
    export_trial_ledger: Annotated[
        bool,
        typer.Option(
            "--export-trial-ledger",
            help="Export the separate readiness-only trial ledger.",
        ),
    ] = False,
    validate_trial_ledger: Annotated[
        bool,
        typer.Option(
            "--validate-trial-ledger",
            help="Validate the exported readiness-only trial ledger.",
        ),
    ] = False,
    run_readiness_backtest: Annotated[
        bool,
        typer.Option(
            "--run-readiness-backtest",
            help="Run the readiness-only trial backtest after export.",
        ),
    ] = False,
    trial_ledger_path: Annotated[
        Path,
        typer.Option(
            "--trial-ledger",
            help="Output path for the exported readiness trial ledger.",
        ),
    ] = Path(
        "data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv"
    ),
    price_fixtures_path: Annotated[
        Path,
        typer.Option(
            "--price-fixtures",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Historical local CSV prices for the optional backtest.",
        ),
    ] = Path("tests/fixtures/historical_price_history"),
    batch_label: Annotated[
        str | None,
        typer.Option(
            "--batch-label",
            help="Optional label included in the readiness batch folder.",
        ),
    ] = None,
) -> None:
    """Generate multi-ticker historical readiness research artifacts."""
    try:
        result = run_historical_readiness_batch(
            tickers=tickers,
            as_of_date=as_of_date,
            examples_root=examples_root,
            outputs_root=outputs_root,
            fixtures_root=fixtures_root,
            portfolio_context=portfolio_context_path,
            financials_provider=financials_provider,
            financials_root=financials_root,
            export_trial_ledger=export_trial_ledger,
            validate_trial_ledger=validate_trial_ledger,
            run_readiness_backtest=run_readiness_backtest,
            trial_ledger_path=trial_ledger_path,
            price_fixtures_path=price_fixtures_path,
            batch_label=batch_label,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Historical readiness batch failed: {exc}"
        ) from exc

    table = Table(title="Historical Readiness Batch")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Batch Run ID", result.batch_run_id),
        ("As-Of Date", as_of_date),
        ("Tickers Requested", tickers),
        ("Completed", str(result.total_completed)),
        ("Failed", str(result.total_failed)),
        (
            "Export Trial Ledger",
            str(result.trial_ledger_exported).lower(),
        ),
        ("Validate Trial Ledger", result.trial_ledger_validation_status),
        (
            "Run Readiness Backtest",
            str(result.readiness_backtest_run).lower(),
        ),
        (
            "Readiness Backtest Run ID",
            result.readiness_backtest_run_id or "Not run",
        ),
        ("Decision Status", result.decision_status or "Not run"),
        (
            "Statistical Validity",
            result.statistical_validity or "Not run",
        ),
        ("Batch Manifest", str(result.manifest_path)),
        ("Batch Summary", str(result.summary_path)),
        ("Batch Results", str(result.results_path)),
        ("Status", "completed"),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"batch_run_id={result.batch_run_id}")
    console.print(f"as_of_date={as_of_date}")
    console.print(f"total_requested={result.total_requested}")
    console.print(f"total_completed={result.total_completed}")
    console.print(f"total_failed={result.total_failed}")
    console.print(
        f"trial_ledger_exported="
        f"{str(result.trial_ledger_exported).lower()}"
    )
    console.print(
        f"readiness_backtest_run="
        f"{str(result.readiness_backtest_run).lower()}"
    )
    console.print("status=completed")


@app.command("backtest-signals")
def backtest_signals(
    ledger_path: Annotated[
        Path,
        typer.Option(
            "--ledger",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Signal ledger CSV or JSONL to evaluate.",
        ),
    ],
    price_fixtures_path: Annotated[
        Path,
        typer.Option(
            "--price-fixtures",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing deterministic ticker price fixtures.",
        ),
    ],
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Root directory for research backtest outputs.",
        ),
    ] = Path("data/outputs"),
    price_provider: Annotated[
        str,
        typer.Option(
            "--price-provider",
            help="Price provider: fixture, csv, or live_stub.",
        ),
    ] = "fixture",
    lookback_years: Annotated[
        int,
        typer.Option(
            "--lookback-years",
            help="Archive lookback in years; accepted values are 2, 5, or 10.",
        ),
    ] = 5,
    dedupe_mode: Annotated[
        str,
        typer.Option(
            "--dedupe-mode",
            help=(
                "Record dedupe policy: none, latest_per_ticker_per_day, "
                "first_per_ticker_per_day, or latest_per_ticker."
            ),
        ),
    ] = "latest_per_ticker_per_day",
    minimum_group_size: Annotated[
        int,
        typer.Option(
            "--minimum-group-size",
            help="Minimum category size before a small-sample warning.",
        ),
    ] = 5,
    walk_forward: Annotated[
        bool,
        typer.Option(
            "--walk-forward",
            help="Generate additional period-by-period validation outputs.",
        ),
    ] = False,
    walk_forward_frequency: Annotated[
        str,
        typer.Option(
            "--walk-forward-frequency",
            help="Walk-forward cohort frequency; currently yearly.",
        ),
    ] = "yearly",
) -> None:
    """Evaluate archived signal fields using offline price fixtures."""
    try:
        result = run_signal_backtest(
            ledger_path=ledger_path,
            price_fixtures_path=price_fixtures_path,
            outputs_root=outputs_root,
            price_provider=price_provider,
            lookback_years=lookback_years,
            dedupe_mode=dedupe_mode,
            minimum_group_size=minimum_group_size,
            walk_forward=walk_forward,
            walk_forward_frequency=walk_forward_frequency,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(f"Signal backtest failed: {exc}") from exc

    table = Table(title="Archived Signal Backtest")
    table.add_column("Field")
    table.add_column("Value")
    rows = [
        ("Backtest Run Type", result.backtest_run_type),
        ("Backtest Run ID", result.backtest_run_id),
        ("Backtest Folder", str(result.backtest_folder)),
        ("Backtest Summary", str(result.summary_path)),
        ("Backtest Results", str(result.results_path)),
        ("Metrics Summary", str(result.metrics_summary_path)),
        ("Backtest Manifest", str(result.manifest_path)),
        ("Price Provider", price_provider),
        ("Dedupe Mode", dedupe_mode),
        ("Sample Size", str(result.metrics["sample_size"])),
        (
            "Hit Rate vs Benchmark 12M",
            (
                f"{result.metrics['hit_rate_vs_benchmark_12m']:.4f}"
                if result.metrics["hit_rate_vs_benchmark_12m"] is not None
                else "Missing"
            ),
        ),
        (
            "Small Sample Warning",
            str(result.metrics["small_sample_warning"]).lower(),
        ),
        (
            "Synthetic Data Warning",
            str(result.metrics["synthetic_data_warning"]).lower(),
        ),
        ("Evaluated Records", str(result.evaluated_records)),
        ("Skipped Records", str(result.skipped_records)),
    ]
    if walk_forward:
        rows.extend(
            [
                ("Walk-Forward", "enabled"),
                ("Frequency", walk_forward_frequency),
                (
                    "Periods Evaluated",
                    str(result.walk_forward_periods_evaluated),
                ),
                (
                    "Walk-Forward Summary",
                    str(result.walk_forward_summary_path),
                ),
                (
                    "Walk-Forward Results",
                    str(result.walk_forward_results_path),
                ),
            ]
        )
        if result.backtest_run_type == "readiness_trial":
            rows.append(
                (
                    "Walk-Forward Stability",
                    result.walk_forward_stability or "Not available",
                )
            )
    if result.backtest_run_type == "readiness_trial":
        rows.extend(
            [
                (
                    "Metadata Enrichment",
                    (
                        "detected"
                        if any(
                            key not in {"not_available", "missing"}
                            for key in result.metrics.get(
                                "metadata_enrichment_status_counts",
                                {},
                            )
                        )
                        else "not available"
                    ),
                ),
                (
                    "Missing Metadata Fields",
                    ", ".join(
                        result.metrics.get("missing_metadata_fields", [])
                    )
                    or "None",
                ),
                (
                    "Metadata Attribution",
                    (
                        "available"
                        if result.metrics.get("grouped_metrics")
                        else "not available"
                    ),
                ),
                (
                    "Coverage Quality",
                    (
                        "detected"
                        if any(
                            key != "not_available"
                            for key in result.metrics.get(
                                "coverage_quality_counts",
                                {},
                            )
                        )
                        else "not available"
                    ),
                ),
                (
                    "Clean Records",
                    str(result.metrics.get("clean_record_count") or 0),
                ),
                (
                    "Warning Records",
                    str(result.metrics.get("warning_record_count") or 0),
                ),
                (
                    "Warning-Heavy Records",
                    str(
                        result.metrics.get("warning_heavy_record_count") or 0
                    ),
                ),
                ("Clean-Coverage Sensitivity", "available"),
                (
                    "Sensitivity Status",
                    str(result.sensitivity_status),
                ),
                (
                    "Clean-Only Available",
                    str(result.clean_only_available).lower(),
                ),
                (
                    "Sensitivity Report",
                    str(result.sensitivity_report_path),
                ),
                ("Delayed Anchor Impact", "available"),
                (
                    "Impact Status",
                    str(result.delayed_anchor_impact_status),
                ),
                (
                    "Delayed Anchor Records",
                    str(result.delayed_anchor_record_count),
                ),
                (
                    "No-Delayed-Anchor Records",
                    str(result.no_delayed_anchor_record_count),
                ),
                (
                    "Delayed Anchor Materially Stronger",
                    str(
                        result.delayed_anchor_materially_stronger
                    ).lower(),
                ),
                (
                    "No-Delayed-Anchor Positive",
                    str(result.no_delayed_anchor_positive).lower(),
                ),
                (
                    "Impact Report",
                    str(result.delayed_anchor_impact_report_path),
                ),
                ("Outlier Sensitivity", "available"),
                (
                    "Outlier Dependence Status",
                    str(result.outlier_dependence_status),
                ),
                ("NVDA Records", str(result.nvda_record_count)),
                (
                    "Ex-NVDA Positive",
                    str(result.ex_nvda_positive).lower(),
                ),
                (
                    "Ex-Top-2 Positive",
                    str(result.ex_top_2_positive).lower(),
                ),
                (
                    "Outlier Report",
                    str(result.outlier_sensitivity_report_path),
                ),
                ("Decision Report", str(result.decision_report_path)),
                ("Decision Status", str(result.decision_status)),
                (
                    "Statistical Validity",
                    str(result.statistical_validity),
                ),
                ("Diagnostic Report", str(result.diagnostic_report_path)),
                ("Diagnostic Status", str(result.diagnostic_status)),
            ]
        )
    rows.append(("Status", "completed"))
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)


@app.command("compare-clean-coverage-runs")
def compare_clean_coverage_runs(
    before_run_id: Annotated[
        str | None,
        typer.Option(
            "--before-run-id",
            help="Pre-clean readiness backtest run ID.",
        ),
    ] = None,
    after_run_id: Annotated[
        str | None,
        typer.Option(
            "--after-run-id",
            help="Post-clean readiness backtest run ID.",
        ),
    ] = None,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing backtests and comparison outputs.",
        ),
    ] = Path("data/outputs"),
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help=(
                "Select the latest clean_not_available and clean-supported "
                "readiness trial runs."
            ),
        ),
    ] = False,
) -> None:
    """Compare clean-coverage evidence before and after fixture improvements."""
    try:
        if auto_latest:
            before_run_id, after_run_id = find_latest_clean_coverage_runs(
                outputs_root
            )
        elif not before_run_id or not after_run_id:
            raise ValueError(
                "Provide --before-run-id and --after-run-id, or use "
                "--auto-latest."
            )
        files = write_clean_coverage_comparison_report(
            outputs_root=outputs_root,
            before_run_id=before_run_id,
            after_run_id=after_run_id,
        )
    except (
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
    ) as exc:
        raise typer.BadParameter(
            f"Clean coverage comparison failed: {exc}"
        ) from exc

    report = files.report
    before = report.before_summary
    after = report.after_summary
    table = Table(title="Clean Coverage Before/After Comparison")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Comparison Run ID", report.comparison_run_id),
        ("Before Run ID", str(report.before_run_id)),
        ("After Run ID", str(report.after_run_id)),
        ("Comparison Status", report.comparison_status),
        ("Clean Records Before", str(before["clean_record_count"])),
        ("Clean Records After", str(after["clean_record_count"])),
        (
            "Warning-Heavy Before",
            str(before["warning_heavy_record_count"]),
        ),
        (
            "Warning-Heavy After",
            str(after["warning_heavy_record_count"]),
        ),
        (
            "Clean-Only Available Before",
            str(before["clean_only_available"]).lower(),
        ),
        (
            "Clean-Only Available After",
            str(after["clean_only_available"]).lower(),
        ),
        ("Diagnostic Status Before", str(before["diagnostic_status"])),
        ("Diagnostic Status After", str(after["diagnostic_status"])),
        ("Decision Status Before", str(before["decision_status"])),
        ("Decision Status After", str(after["decision_status"])),
        ("Report Path", str(files.markdown_path)),
        ("Status", "completed"),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"comparison_run_id={report.comparison_run_id}")
    console.print(f"before_run_id={report.before_run_id}")
    console.print(f"after_run_id={report.after_run_id}")
    console.print(f"comparison_status={report.comparison_status}")
    console.print("status=completed")


@app.command("run-evidence-decision-gate")
def run_evidence_decision_gate(
    backtest_run_id: Annotated[
        str | None,
        typer.Option(
            "--backtest-run-id",
            help="Readiness trial backtest run ID to evaluate.",
        ),
    ] = None,
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Root containing backtests and gate outputs.",
        ),
    ] = Path("data/outputs"),
    auto_latest: Annotated[
        bool,
        typer.Option(
            "--auto-latest",
            help="Select the latest completed readiness trial.",
        ),
    ] = False,
) -> None:
    """Evaluate whether readiness research may expand its sample."""
    try:
        if auto_latest:
            backtest_run_id = find_latest_evidence_gate_backtest(outputs_root)
        elif not backtest_run_id:
            raise ValueError(
                "Provide --backtest-run-id or use --auto-latest."
            )
        files = write_evidence_decision_gate_report(
            outputs_root=outputs_root,
            backtest_run_id=backtest_run_id,
        )
    except (
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
    ) as exc:
        raise typer.BadParameter(
            f"Evidence decision gate failed: {exc}"
        ) from exc

    report = files.report
    evidence = report.evidence_summary
    criteria = {
        item["criterion"]: item["status"]
        for item in report.criteria_results
    }
    clean_positive = criteria.get("clean_evidence_positive") == "pass"
    table = Table(title="Evidence Decision Gate")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Gate Run ID", report.gate_run_id),
        ("Source Backtest Run ID", str(report.source_backtest_run_id)),
        ("Gate Outcome", report.gate_outcome),
        ("Gate Status", report.gate_status),
        ("Clean Records", str(evidence.get("clean_record_count", 0))),
        ("Warning Records", str(evidence.get("warning_record_count", 0))),
        (
            "Warning-Heavy Records",
            str(evidence.get("warning_heavy_record_count", 0)),
        ),
        ("Clean Evidence Positive", str(clean_positive).lower()),
        (
            "Delayed Anchor Criterion",
            str(criteria.get("delayed_anchor_not_blocking")),
        ),
        ("Outlier Criterion", str(criteria.get("outlier_not_blocking"))),
        ("Critical Pass Count", str(report.critical_pass_count)),
        ("Warning Count", str(report.warn_count)),
        ("Block Count", str(report.block_count)),
        ("Next Research Action", report.next_research_action),
        ("Report Path", str(files.markdown_path)),
        ("Status", "completed"),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print(f"gate_run_id={report.gate_run_id}")
    console.print(f"source_backtest_run_id={report.source_backtest_run_id}")
    console.print(f"gate_outcome={report.gate_outcome}")
    console.print(f"gate_status={report.gate_status}")
    console.print(f"next_research_action={report.next_research_action}")
    console.print("status=completed")


@app.command("generate-readiness-trial-decision-report")
def generate_readiness_trial_decision_report(
    backtest_folder: Annotated[
        Path,
        typer.Option(
            "--backtest-folder",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Completed readiness trial backtest folder.",
        ),
    ],
) -> None:
    """Regenerate conservative decision artifacts for a readiness trial."""
    try:
        files = regenerate_readiness_trial_decision_report(backtest_folder)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Decision report generation failed: {exc}"
        ) from exc

    table = Table(title="Readiness Trial Backtest Decision Report")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Backtest Run ID", files.report.backtest_run_id),
        ("Decision Status", files.report.decision_status),
        ("Statistical Validity", files.report.statistical_validity),
        ("Decision Report", str(files.markdown_path)),
        ("Decision Report JSON", str(files.json_path)),
        ("Status", "completed"),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)


@app.command("generate-readiness-trial-diagnostic-report")
def generate_readiness_trial_diagnostic_report(
    backtest_folder: Annotated[
        Path,
        typer.Option(
            "--backtest-folder",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=True,
            help="Completed readiness trial backtest folder.",
        ),
    ],
) -> None:
    """Regenerate attribution diagnostics for a readiness trial."""
    try:
        files = regenerate_readiness_trial_diagnostic_report(
            backtest_folder
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(
            f"Diagnostic report generation failed: {exc}"
        ) from exc

    table = Table(title="Readiness Trial Diagnostic Report")
    table.add_column("Field")
    table.add_column("Value")
    rows = (
        ("Backtest Run ID", files.report.backtest_run_id),
        ("Diagnostic Status", files.report.diagnostic_status),
        ("Diagnostic Report", str(files.markdown_path)),
        ("Diagnostic Report JSON", str(files.json_path)),
        ("Status", "completed"),
    )
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)


@app.command("validate-price-csv")
def validate_price_csv(
    price_fixtures_path: Annotated[
        Path,
        typer.Option(
            "--price-fixtures",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing local ticker price CSV files.",
        ),
    ],
    tickers: Annotated[
        str,
        typer.Option(
            "--tickers",
            help="Comma-separated ticker symbols to validate.",
        ),
    ],
    price_provider: Annotated[
        str,
        typer.Option(
            "--price-provider",
            help="Local price provider to validate; normally csv.",
        ),
    ] = "csv",
) -> None:
    """Validate local price CSV files without running a backtest."""
    ticker_list = [
        ticker.strip().upper()
        for ticker in tickers.split(",")
        if ticker.strip()
    ]
    if not ticker_list:
        raise typer.BadParameter("At least one ticker is required.")
    try:
        results = validate_price_csvs(
            ticker_list,
            price_fixtures_path,
            provider_name=price_provider,
        )
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(
            f"Price CSV validation failed: {exc}"
        ) from exc

    table = Table(title="Local Price CSV Validation")
    for column in (
        "Ticker",
        "File Found",
        "Rows",
        "Min Date",
        "Max Date",
        "Price Column Used",
        "Status",
    ):
        table.add_column(column)
    for result in results:
        table.add_row(
            result.ticker,
            str(result.file_found).lower(),
            str(result.rows_count),
            result.min_date or "Missing",
            result.max_date or "Missing",
            result.price_column_used or "Missing",
            result.status,
        )
    console.print(table)
    for result in results:
        console.print(
            " | ".join(
                (
                    f"ticker={result.ticker}",
                    f"file_found={str(result.file_found).lower()}",
                    f"rows={result.rows_count}",
                    f"min_date={result.min_date or 'missing'}",
                    f"max_date={result.max_date or 'missing'}",
                    (
                        "price_column_used="
                        f"{result.price_column_used or 'missing'}"
                    ),
                    f"status={result.status}",
                )
            )
        )


@app.command("analyze-batch")
def analyze_batch(
    tickers: Annotated[
        str | None,
        typer.Option(
            "--tickers",
            help="Comma-separated ticker symbols to analyze.",
        ),
    ] = None,
    intake_files: Annotated[
        str | None,
        typer.Option(
            "--intake-files",
            help="Comma-separated YAML or JSON analyze-stock intake files.",
        ),
    ] = None,
    batch_label: Annotated[
        str | None,
        typer.Option(
            "--batch-label",
            help="Optional label included in the batch run folder name.",
        ),
    ] = None,
    examples_root: Annotated[
        Path,
        typer.Option(
            "--examples-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing manual input packs.",
        ),
    ] = Path("examples"),
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Root directory for ticker and batch outputs.",
        ),
    ] = Path("data/outputs"),
    fixtures_root: Annotated[
        Path,
        typer.Option(
            "--fixtures-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing offline enrichment fixtures.",
        ),
    ] = Path("tests/fixtures"),
    portfolio_context_path: Annotated[
        Path | None,
        typer.Option(
            "--portfolio-context",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Optional portfolio context for Bogle analysis.",
        ),
    ] = None,
    as_of_date: Annotated[
        str | None,
        typer.Option(
            "--as-of-date",
            help="Historical-readiness date applied to each batch run.",
        ),
    ] = None,
) -> None:
    """Run the existing analyze-stock pipeline for a batch of inputs."""
    if tickers is not None and intake_files is not None:
        raise typer.BadParameter(
            "Provide either --tickers or --intake-files, not both."
        )
    if tickers is None and intake_files is None:
        raise typer.BadParameter(
            "Provide one input mode: --tickers or --intake-files."
        )

    results: list[BatchTickerResult] = []
    requested_tickers: list[str] = []
    batch_outputs_root = outputs_root
    if tickers is not None:
        input_mode = "tickers"
        ticker_values = list(
            dict.fromkeys(
                item.strip().upper()
                for item in tickers.split(",")
                if item.strip()
            )
        )
        if not ticker_values:
            raise typer.BadParameter("--tickers must include at least one ticker.")
        requested_tickers = ticker_values
        for ticker_value in ticker_values:
            try:
                intake = build_ticker_analyze_stock_intake(
                    ticker=ticker_value,
                    examples_root=examples_root,
                    outputs_root=outputs_root,
                    fixtures_root=fixtures_root,
                    portfolio_context=portfolio_context_path,
                    as_of_date=as_of_date,
                )
                execution = execute_analyze_stock(
                    intake=intake,
                    input_mode="ticker",
                )
                results.append(completed_batch_result(execution))
            except (
                OSError,
                ValueError,
                yaml.YAMLError,
                json.JSONDecodeError,
            ) as exc:
                results.append(failed_batch_result(ticker_value, exc))
    else:
        input_mode = "intake_files"
        intake_paths = [
            Path(item.strip())
            for item in (intake_files or "").split(",")
            if item.strip()
        ]
        if not intake_paths:
            raise typer.BadParameter(
                "--intake-files must include at least one path."
            )
        configured_outputs_root: Path | None = None
        for intake_path in intake_paths:
            result_ticker = intake_path.stem.upper()
            requested_added = False
            try:
                intake = load_analyze_stock_intake(intake_path)
                if as_of_date is not None:
                    intake = with_as_of_date(intake, as_of_date)
                result_ticker = intake.ticker
                requested_tickers.append(result_ticker)
                requested_added = True
                if configured_outputs_root is None:
                    configured_outputs_root = intake.outputs_root
                    batch_outputs_root = intake.outputs_root
                elif intake.outputs_root != configured_outputs_root:
                    raise ValueError(
                        "All intake files in a batch must use the same "
                        "outputs_root."
                    )
                execution = execute_analyze_stock(
                    intake=intake,
                    input_mode="intake_file",
                    intake_file=intake_path,
                )
                results.append(completed_batch_result(execution))
            except (
                OSError,
                ValueError,
                yaml.YAMLError,
                json.JSONDecodeError,
            ) as exc:
                if not requested_added:
                    requested_tickers.append(result_ticker)
                results.append(failed_batch_result(result_ticker, exc))

    bundle = create_analyze_batch_bundle(
        outputs_root=batch_outputs_root,
        input_mode=input_mode,
        batch_label=batch_label,
        requested_tickers=requested_tickers,
        results=results,
        as_of_date=as_of_date,
    )
    archived_count = 0
    signal_ledger_path = batch_outputs_root / "signal_archive" / "signal_ledger.jsonl"
    for result in results:
        if (
            result.status != "completed"
            or result.run_manifest_path is None
            or result.broker_deal_package_path is None
        ):
            continue
        archive_result = archive_completed_run(
            outputs_root=batch_outputs_root,
            run_manifest_path=Path(result.run_manifest_path),
            broker_deal_package_path=Path(result.broker_deal_package_path),
            batch_run_id=bundle.batch_run_id,
            batch_folder=bundle.batch_folder,
        )
        signal_ledger_path = archive_result.jsonl_path
        archived_count += 1
    table = Table(title="Batch Stock Analysis")
    for column in (
        "Ticker",
        "Status",
        "Run Folder",
        "Broker Deal Package",
        "Readiness Label",
        "Source Verification",
        "Promotion-Blocking Categories",
    ):
        table.add_column(column)
    for result in results:
        table.add_row(
            result.ticker,
            result.status,
            result.run_folder or "Not generated",
            result.broker_deal_package_path or "Not generated",
            result.readiness_label or "Not available",
            result.source_verification_status or "Not available",
            ", ".join(result.promotion_blocking_categories) or "None",
        )
    console.print(table)
    console.print(f"Batch Run ID: {bundle.batch_run_id}", soft_wrap=True)
    console.print(f"Batch Folder: {bundle.batch_folder}", soft_wrap=True)
    console.print(
        f"Batch Manifest: {bundle.batch_manifest_path}",
        soft_wrap=True,
    )
    console.print(
        f"Batch Summary: {bundle.batch_summary_path}",
        soft_wrap=True,
    )
    console.print(
        (
            f"Completed: {bundle.completed_count}; "
            f"Failed: {bundle.failed_count}; "
            f"Skipped: {bundle.skipped_count}"
        ),
        soft_wrap=True,
    )
    console.print(
        f"Signal Archive Records: {archived_count}",
        soft_wrap=True,
    )
    console.print(f"Signal Ledger: {signal_ledger_path}", soft_wrap=True)
    context = build_as_of_context(as_of_date)
    console.print(
        "As-Of Date: "
        f"{context.as_of_date.isoformat() if context.as_of_date else 'Not provided'}",
        soft_wrap=True,
    )
    console.print(
        "Historical Mode: "
        f"{'enabled' if context.historical_mode else 'disabled'}",
        soft_wrap=True,
    )
    if bundle.completed_count == 0:
        raise typer.Exit(code=1)


@app.command("run-deals")
def run_deals(
    tickers: Annotated[
        str,
        typer.Option("--tickers", help="Comma-separated ticker symbols to process."),
    ] = "MSFT,AAPL,NVDA",
    examples_root: Annotated[
        Path,
        typer.Option(
            "--examples-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing manual input packs.",
        ),
    ] = Path("examples"),
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Root directory for broker deal outputs.",
        ),
    ] = Path("data/outputs"),
    fixtures_root: Annotated[
        Path,
        typer.Option(
            "--fixtures-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing offline enrichment fixtures.",
        ),
    ] = Path("tests/fixtures"),
    portfolio_context_path: Annotated[
        Path | None,
        typer.Option(
            "--portfolio-context",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Optional portfolio context used only by independent Bogle reports.",
        ),
    ] = None,
) -> None:
    """Run broker deal workflows for multiple tickers without stopping the batch."""
    parsed_tickers = [ticker.strip().upper() for ticker in tickers.split(",") if ticker.strip()]
    if not parsed_tickers:
        raise typer.BadParameter("At least one ticker must be provided.")

    table = Table(title="Broker Deal Packages")
    table.add_column("Ticker")
    table.add_column("Package")
    table.add_column("Status")
    for ticker in parsed_tickers:
        input_path = examples_root / f"{ticker.lower()}_input.yaml"
        try:
            result = run_broker_deal_workflow(
                ticker=ticker,
                input_pack_path=input_path,
                outputs_root=outputs_root,
                fixtures_root=fixtures_root,
                portfolio_context_path=portfolio_context_path,
            )
        except (OSError, ValueError, yaml.YAMLError) as exc:
            console.print(f"[yellow]Skipping {ticker}: {exc}[/yellow]")
            table.add_row(ticker, str(input_path), "failed / skipped")
            continue
        table.add_row(ticker, str(result.broker_deal_package_path), "written")
    console.print(table)


@app.command("review-reports")
def review_reports(
    reports_dir: Annotated[
        Path,
        typer.Option(
            "--reports-dir",
            "-r",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing generated reports.",
        ),
    ] = Path("examples"),
    ticker: Annotated[
        str,
        typer.Option("--ticker", "-t", help="Ticker symbol used for report filenames."),
    ] = "MSFT",
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Path where the quality review should be written.",
        ),
    ] = Path("examples/msft_reports_quality_review.md"),
) -> None:
    """Review generated report quality without creating a consensus recommendation."""
    ticker_lower = ticker.lower()
    report_paths = {
        "backoffice": reports_dir / f"{ticker_lower}_backoffice_data_pack.md",
        "buffett": reports_dir / f"{ticker_lower}_buffett_report.md",
        "munger": reports_dir / f"{ticker_lower}_munger_report.md",
        "fisher": reports_dir / f"{ticker_lower}_fisher_report.md",
        "lynch": reports_dir / f"{ticker_lower}_lynch_report.md",
        "bogle": reports_dir / f"{ticker_lower}_bogle_report.md",
        "agents_summary": reports_dir / f"{ticker_lower}_agents_summary.md",
    }
    review = review_generated_reports(report_paths)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(review, encoding="utf-8")
    except OSError as exc:
        raise typer.BadParameter(f"Could not write quality review {output_path}: {exc}") from exc

    console.print(f"[bold]Reports quality review written to:[/bold] {output_path}")


@app.command("compare-summaries")
def compare_summaries(
    left_ticker: Annotated[
        str,
        typer.Option("--left", help="Left ticker to compare."),
    ],
    right_ticker: Annotated[
        str,
        typer.Option("--right", help="Right ticker to compare."),
    ],
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Root output directory containing per-ticker output folders.",
        ),
    ] = Path("data/outputs"),
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Path where the comparison report should be written.",
        ),
    ] = Path("data/outputs/msft_vs_aapl_agents_comparison.md"),
) -> None:
    """Compare two independent investor-agent summary reports."""
    left_upper = left_ticker.upper()
    right_upper = right_ticker.upper()
    left_summary_path = outputs_root / left_upper / f"{left_upper.lower()}_agents_summary.md"
    right_summary_path = outputs_root / right_upper / f"{right_upper.lower()}_agents_summary.md"
    comparison = generate_agents_comparison(
        left_upper,
        right_upper,
        left_summary_path,
        right_summary_path,
    )

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(comparison, encoding="utf-8")
    except OSError as exc:
        raise typer.BadParameter(f"Could not write comparison report {output_path}: {exc}") from exc

    console.print(f"[bold]Agents comparison written to:[/bold] {output_path}")


@app.command("compare-many")
def compare_many(
    tickers: Annotated[
        str,
        typer.Option(
            "--tickers",
            help="Comma-separated ticker symbols to compare.",
        ),
    ] = "MSFT,AAPL,NVDA",
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Root directory containing per-ticker generated outputs.",
        ),
    ] = Path("data/outputs"),
    examples_root: Annotated[
        Path,
        typer.Option(
            "--examples-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing manual company input YAML files.",
        ),
    ] = Path("examples"),
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Path where the multi-company comparison should be written.",
        ),
    ] = Path("data/outputs/multi_company_agents_comparison.md"),
    portfolio_context_path: Annotated[
        Path | None,
        typer.Option(
            "--portfolio-context",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Optional shared portfolio context YAML for Bogle comparisons.",
        ),
    ] = None,
) -> None:
    """Compare independent agent outputs across multiple companies."""
    parsed_tickers = [ticker.strip() for ticker in tickers.split(",") if ticker.strip()]
    if not parsed_tickers:
        raise typer.BadParameter("At least one ticker must be provided.")

    comparison = generate_multi_company_comparison(
        parsed_tickers,
        outputs_root,
        examples_root,
        load_portfolio_context(portfolio_context_path) if portfolio_context_path else None,
    )
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(comparison, encoding="utf-8")
    except OSError as exc:
        raise typer.BadParameter(
            f"Could not write multi-company comparison {output_path}: {exc}"
        ) from exc

    console.print(f"[bold]Multi-company comparison written to:[/bold] {output_path}")


@app.command("audit-candidates")
def audit_candidates(
    tickers: Annotated[
        str,
        typer.Option(
            "--tickers",
            help="Comma-separated ticker symbols to audit.",
        ),
    ] = "MSFT,AAPL,NVDA",
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Root directory containing per-ticker generated outputs.",
        ),
    ] = Path("data/outputs"),
    examples_root: Annotated[
        Path,
        typer.Option(
            "--examples-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing manual company input YAML files.",
        ),
    ] = Path("examples"),
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Path where the candidate audit report should be written.",
        ),
    ] = Path("data/outputs/decision_candidate_audit.md"),
    portfolio_context_path: Annotated[
        Path | None,
        typer.Option(
            "--portfolio-context",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Optional shared portfolio context YAML for Bogle audit records.",
        ),
    ] = None,
) -> None:
    """Audit provisional candidate decisions without changing final decisions."""
    parsed_tickers = [ticker.strip() for ticker in tickers.split(",") if ticker.strip()]
    if not parsed_tickers:
        raise typer.BadParameter("At least one ticker must be provided.")

    audit = generate_decision_candidate_audit(
        parsed_tickers,
        outputs_root,
        examples_root,
        load_portfolio_context(portfolio_context_path) if portfolio_context_path else None,
    )
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(audit, encoding="utf-8")
    except OSError as exc:
        raise typer.BadParameter(
            f"Could not write decision candidate audit {output_path}: {exc}"
        ) from exc

    console.print(f"[bold]Decision candidate audit written to:[/bold] {output_path}")


@app.command("missing-evidence")
def missing_evidence(
    tickers: Annotated[
        str,
        typer.Option("--tickers", help="Comma-separated ticker symbols to cover."),
    ] = "MSFT,AAPL,NVDA",
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Root directory containing per-ticker generated outputs.",
        ),
    ] = Path("data/outputs"),
    examples_root: Annotated[
        Path,
        typer.Option(
            "--examples-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing manual company input YAML files.",
        ),
    ] = Path("examples"),
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Path where the missing-evidence report should be written.",
        ),
    ] = Path("data/outputs/backoffice_missing_evidence_requests.md"),
    portfolio_context_path: Annotated[
        Path | None,
        typer.Option(
            "--portfolio-context",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Optional shared portfolio context YAML for Bogle evidence requests.",
        ),
    ] = None,
) -> None:
    """Generate a Backoffice worklist for missing investor evidence."""
    parsed_tickers = [ticker.strip() for ticker in tickers.split(",") if ticker.strip()]
    if not parsed_tickers:
        raise typer.BadParameter("At least one ticker must be provided.")

    report = generate_backoffice_missing_evidence_report(
        parsed_tickers,
        outputs_root,
        examples_root,
        load_portfolio_context(portfolio_context_path) if portfolio_context_path else None,
    )
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
    except OSError as exc:
        raise typer.BadParameter(
            f"Could not write missing-evidence report {output_path}: {exc}"
        ) from exc

    console.print(f"[bold]Missing-evidence report written to:[/bold] {output_path}")


@app.command("verify-sources")
def verify_source_data(
    tickers: Annotated[
        str,
        typer.Option("--tickers", help="Comma-separated ticker symbols to verify."),
    ] = "MSFT,AAPL,NVDA",
    examples_root: Annotated[
        Path,
        typer.Option(
            "--examples-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing manual company input YAML files.",
        ),
    ] = Path("examples"),
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Path where the source verification report should be written.",
        ),
    ] = Path("data/outputs/source_verification_report.md"),
) -> None:
    """Generate a deterministic source-quality verification report."""
    parsed_tickers = [ticker.strip() for ticker in tickers.split(",") if ticker.strip()]
    if not parsed_tickers:
        raise typer.BadParameter("At least one ticker must be provided.")

    report = generate_source_verification_report(parsed_tickers, examples_root)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
    except OSError as exc:
        raise typer.BadParameter(
            f"Could not write source verification report {output_path}: {exc}"
        ) from exc

    console.print(f"[bold]Source verification report written to:[/bold] {output_path}")


@app.command("readiness-dashboard")
def readiness_dashboard(
    tickers: Annotated[
        str,
        typer.Option("--tickers", help="Comma-separated ticker symbols to cover."),
    ] = "MSFT,AAPL,NVDA",
    outputs_root: Annotated[
        Path,
        typer.Option(
            "--outputs-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Root directory containing per-ticker generated outputs.",
        ),
    ] = Path("data/outputs"),
    examples_root: Annotated[
        Path,
        typer.Option(
            "--examples-root",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing manual company input YAML files.",
        ),
    ] = Path("examples"),
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Path where the readiness dashboard should be written.",
        ),
    ] = Path("data/outputs/investor_agent_readiness_dashboard.md"),
) -> None:
    """Generate the deterministic investor-agent readiness dashboard."""
    parsed_tickers = [ticker.strip() for ticker in tickers.split(",") if ticker.strip()]
    if not parsed_tickers:
        raise typer.BadParameter("At least one ticker must be provided.")

    dashboard = generate_investor_agent_readiness_dashboard(
        parsed_tickers,
        outputs_root,
        examples_root,
    )
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dashboard, encoding="utf-8")
    except OSError as exc:
        raise typer.BadParameter(
            f"Could not write readiness dashboard {output_path}: {exc}"
        ) from exc

    console.print(f"[bold]Readiness dashboard written to:[/bold] {output_path}")


def main() -> None:
    """Run the Typer application."""
    app()


if __name__ == "__main__":
    main()
