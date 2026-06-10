"""Deterministic normalized owner-earnings evidence."""

from statistics import median
from typing import Any

from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.calculators.owner_earnings import calculate_owner_earnings_snapshot


def _to_float(value: Any) -> float | None:
    """Convert a value to float when possible."""
    if value in (None, "", "unavailable"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fcf_history(pack: dict) -> list[float]:
    """Collect usable free-cash-flow observations from statement history."""
    financials = pack.get("financial_statements_summary", {})
    values: list[float] = []
    rows = financials.get("cash_flow_statement", [])
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            fcf = _to_float(row.get("free_cash_flow"))
            if fcf is None:
                ocf = _to_float(row.get("operating_cash_flow"))
                capex = _to_float(row.get("capex"))
                if ocf is not None and capex is not None:
                    fcf = ocf - capex
            if fcf is not None:
                values.append(fcf)
    annual = financials.get("annual", {})
    if isinstance(annual, dict):
        annual_fcf = _to_float(annual.get("free_cash_flow"))
        if annual_fcf is None:
            ocf = _to_float(annual.get("operating_cash_flow"))
            capex = _to_float(annual.get("capex"))
            if ocf is not None and capex is not None:
                annual_fcf = ocf - capex
        if annual_fcf is not None and annual_fcf not in values:
            values.append(annual_fcf)
    return values


def calculate_normalized_owner_earnings(pack: dict) -> dict:
    """Normalize owner earnings from available FCF history or a latest-year proxy."""
    owner = calculate_owner_earnings_snapshot(pack)
    signals = extract_company_signals(pack)
    history = _fcf_history(pack)
    latest = owner["owner_earnings_proxy"]
    years = len(history)
    gaps: list[str] = []

    if years >= 5:
        normalized = float(median(history))
        method = "Median free cash flow across available 5+ year history."
        durability = "durable / evidence-backed"
        confidence = "High"
    elif latest is not None:
        normalized = float(latest)
        method = "Latest free cash flow used as a placeholder."
        if signals["business_model_type"] in {"semiconductor", "industrial", "financial"}:
            durability = "cycle-sensitive / needs normalization"
        else:
            durability = "promising but needs history"
        confidence = "Medium"
        gaps.append("5-10 year free cash flow history is required.")
    else:
        normalized = None
        method = "Owner earnings could not be normalized."
        durability = "not established"
        confidence = "Insufficient Data"
        gaps.append("Free cash flow evidence is missing.")

    if owner["capex_intensity_label"] == "high" and confidence != "Insufficient Data":
        confidence = "Low"
        gaps.append("Maintenance versus growth capex split is required.")
    if signals["business_model_type"] in {"semiconductor", "industrial", "financial"}:
        if confidence == "High":
            confidence = "Medium"
        elif confidence == "Medium":
            confidence = "Low"
        gaps.append("Cycle-normalized owner earnings are required.")

    revenue = owner["revenue"]
    normalized_margin = (
        normalized / revenue
        if normalized is not None and revenue not in (None, 0)
        else None
    )
    notes = [
        f"{years} year(s) of free cash flow evidence are available.",
        "Normalized owner earnings remain a deterministic Backoffice proxy.",
    ]

    return {
        "latest_owner_earnings": latest,
        "normalized_owner_earnings": normalized,
        "normalization_method": method,
        "fcf_history_available_years": years,
        "normalized_fcf_margin": normalized_margin,
        "owner_earnings_durability_label": durability,
        "normalized_owner_earnings_confidence": confidence,
        "notes": notes,
        "evidence_gaps": list(dict.fromkeys(gaps)),
    }
