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
from broker_agents.agents.bogle_agent import BogleAgent
from broker_agents.agents.buffett_agent import BuffettAgent
from broker_agents.agents.fisher_agent import FisherAgent
from broker_agents.agents.lynch_agent import LynchAgent
from broker_agents.agents.munger_agent import MungerAgent
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
