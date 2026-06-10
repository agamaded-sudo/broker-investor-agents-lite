"""Owner earnings snapshot calculations."""

from typing import Any


def _first_row(section: dict, key: str) -> dict:
    """Return the first row for a statement list if available."""
    rows = section.get(key, [])
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows[0]
    return {}


def _to_float(value: Any) -> float | None:
    """Convert a value to float when possible."""
    if value in (None, "", "unavailable"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_number(*values: Any) -> float | None:
    """Return the first value that can be interpreted as a number."""
    for value in values:
        number = _to_float(value)
        if number is not None:
            return number
    return None


def _capex_intensity_label(capex_to_ocf: float | None) -> str:
    """Classify capex intensity from capex to operating cash flow."""
    if capex_to_ocf is None:
        return "unknown"
    if capex_to_ocf < 0.15:
        return "low"
    if capex_to_ocf < 0.35:
        return "moderate"
    return "high"


def _owner_earnings_quality_label(
    fcf_margin: float | None,
    capex_to_ocf: float | None,
) -> str:
    """Classify owner earnings quality from FCF margin and capex intensity."""
    if fcf_margin is None or capex_to_ocf is None:
        return "unknown"
    if fcf_margin >= 0.20 and capex_to_ocf < 0.25:
        return "strong"
    if fcf_margin >= 0.15 and capex_to_ocf >= 0.25:
        return "good but capex-intensive"
    if fcf_margin >= 0.10:
        return "moderate"
    return "weak or not established"


def calculate_owner_earnings_snapshot(pack: dict) -> dict:
    """Calculate a preliminary owner earnings snapshot from Backoffice cash flow data."""
    financials = pack.get("financial_statements_summary", {})
    income_statement = _first_row(financials, "income_statement")
    cash_flow_statement = _first_row(financials, "cash_flow_statement")
    annual = financials.get("annual", {}) if isinstance(financials.get("annual", {}), dict) else {}
    proxy = pack.get("capex_owner_earnings_proxy", {})

    operating_cash_flow = _first_number(
        cash_flow_statement.get("operating_cash_flow"),
        cash_flow_statement.get("net_cash_provided_by_operating_activities"),
        annual.get("operating_cash_flow"),
        proxy.get("operating_cash_flow"),
    )
    capex = _first_number(
        cash_flow_statement.get("capex"),
        cash_flow_statement.get("capital_expenditures"),
        annual.get("capex"),
        proxy.get("capex"),
    )
    revenue = _first_number(
        income_statement.get("revenue"),
        income_statement.get("total_revenue"),
        annual.get("revenue"),
    )

    free_cash_flow = None
    if operating_cash_flow is not None and capex is not None:
        free_cash_flow = operating_cash_flow - capex

    fcf_margin = None
    if free_cash_flow is not None and revenue:
        fcf_margin = free_cash_flow / revenue

    capex_to_ocf = None
    if capex is not None and operating_cash_flow:
        capex_to_ocf = capex / operating_cash_flow

    capex_intensity_label = _capex_intensity_label(capex_to_ocf)
    owner_earnings_quality_label = _owner_earnings_quality_label(fcf_margin, capex_to_ocf)
    notes: list[str] = []
    if free_cash_flow is None:
        notes.append("Operating cash flow or capex is missing; owner earnings proxy is not established.")
    else:
        notes.append("Owner earnings proxy uses operating cash flow minus capex.")
    if capex_intensity_label == "high":
        notes.append("Capex absorbs a large share of operating cash flow.")
    if capex_intensity_label == "low" and owner_earnings_quality_label == "strong":
        notes.append("Cash conversion appears strong on this preliminary snapshot.")

    return {
        "operating_cash_flow": operating_cash_flow,
        "capex": capex,
        "free_cash_flow": free_cash_flow,
        "revenue": revenue,
        "fcf_margin": fcf_margin,
        "capex_to_ocf": capex_to_ocf,
        "owner_earnings_proxy": free_cash_flow,
        "capex_intensity_label": capex_intensity_label,
        "owner_earnings_quality_label": owner_earnings_quality_label,
        "notes": notes,
    }
