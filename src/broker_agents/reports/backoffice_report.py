"""Backoffice Markdown report generation."""

from pathlib import Path
from typing import Any

from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.calculators.owner_earnings import calculate_owner_earnings_snapshot
from broker_agents.calculators.valuation_guardrails import calculate_valuation_guardrails
from broker_agents.reports.markdown_report import render_markdown_template

TEMPLATE_PATH = Path(__file__).resolve().parent / "report_templates" / "backoffice_data_pack.md.j2"


def _as_list(value: Any) -> list[Any]:
    """Return value as a list for template iteration."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def generate_backoffice_report(pack: dict) -> str:
    """Generate a neutral Markdown Backoffice Data Pack report."""
    source_log = _as_list(pack.get("sources_confidence_data_gaps", {}).get("source_log"))
    source_ids = {
        str(source.get("source_id"))
        for source in source_log
        if isinstance(source, dict) and source.get("source_id")
    }
    context = {
        "pack": pack,
        "metadata": pack.get("metadata", {}),
        "company_identity": pack.get("company_identity", {}),
        "business_model": pack.get("business_model", {}),
        "segments": pack.get("products_customers_revenue_segments", {}).get("segments", []),
        "financials": pack.get("financial_statements_summary", {}),
        "annual": pack.get("financial_statements_summary", {}).get("annual", {}),
        "quarterly": pack.get("financial_statements_summary", {}).get("quarterly", {}),
        "metrics": pack.get("calculated_financial_metrics", {}),
        "quality_of_earnings": pack.get("quality_of_earnings", {}),
        "growth_drivers": _as_list(pack.get("growth_drivers", {}).get("drivers")),
        "capex_owner_earnings_proxy": pack.get("capex_owner_earnings_proxy", {}),
        "valuation_snapshot": pack.get("valuation_snapshot", {}),
        "risk_register": _as_list(pack.get("risk_register", {}).get("risks")),
        "scuttlebutt": pack.get("scuttlebutt", {}),
        "benchmark": pack.get("index_benchmark_alternative", {}),
        "sources_section": pack.get("sources_confidence_data_gaps", {}),
        "source_log": source_log,
        "known_gaps": _as_list(pack.get("sources_confidence_data_gaps", {}).get("known_gaps")),
        "company_signals": extract_company_signals(pack),
        "owner_earnings_snapshot": calculate_owner_earnings_snapshot(pack),
        "valuation_guardrails": calculate_valuation_guardrails(pack),
        "annual_source_id": "msft_ar_2025" if "msft_ar_2025" in source_ids else "not provided",
        "quarterly_source_id": "msft_fy26_q3" if "msft_fy26_q3" in source_ids else "not provided",
        "market_source_id": "market_data_current"
        if "market_data_current" in source_ids
        else "not provided",
    }
    return render_markdown_template(TEMPLATE_PATH, context)
