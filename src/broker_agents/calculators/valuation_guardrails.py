"""Preliminary valuation guardrail calculations."""

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
    """Return the first numeric value."""
    for value in values:
        number = _to_float(value)
        if number is not None:
            return number
    return None


def _valuation_status(p_fcf: float | None, fcf_yield: float | None, has_any_data: bool) -> str:
    """Classify valuation status from P/FCF and FCF yield."""
    if not has_any_data:
        return "not established"
    if p_fcf is None and fcf_yield is None:
        return "not established"
    if (p_fcf is not None and p_fcf > 30) or (fcf_yield is not None and fcf_yield < 0.03):
        return "demanding"
    if p_fcf is not None and 15 <= p_fcf <= 30:
        return "reasonable"
    if p_fcf is not None and p_fcf < 15 and fcf_yield is not None and fcf_yield >= 0.06:
        return "potentially attractive"
    return "not established"


def calculate_valuation_guardrails(pack: dict) -> dict:
    """Calculate preliminary valuation guardrails from valuation and financial data."""
    valuation_snapshot = pack.get("valuation_snapshot", {})
    financials = pack.get("financial_statements_summary", {})
    income_statement = _first_row(financials, "income_statement")
    cash_flow_statement = _first_row(financials, "cash_flow_statement")
    annual = financials.get("annual", {}) if isinstance(financials.get("annual", {}), dict) else {}
    proxy = pack.get("capex_owner_earnings_proxy", {})

    market_cap = _first_number(valuation_snapshot.get("market_cap"))
    current_price = _first_number(valuation_snapshot.get("current_price"))
    net_income = _first_number(income_statement.get("net_income"), annual.get("net_income"))
    free_cash_flow = _first_number(
        cash_flow_statement.get("free_cash_flow"),
        annual.get("free_cash_flow"),
        proxy.get("free_cash_flow"),
    )
    pe = _first_number(valuation_snapshot.get("pe"), valuation_snapshot.get("pe_ratio"))
    p_fcf = _first_number(valuation_snapshot.get("p_fcf"), valuation_snapshot.get("price_to_fcf"))

    if market_cap is not None and net_income:
        pe = market_cap / net_income
    if market_cap is not None and free_cash_flow:
        p_fcf = market_cap / free_cash_flow

    earnings_yield = None
    if pe:
        earnings_yield = 1 / pe

    fcf_yield = None
    if market_cap is not None and free_cash_flow:
        fcf_yield = free_cash_flow / market_cap

    has_any_data = any(value is not None for value in [market_cap, pe, p_fcf])
    valuation_status = _valuation_status(p_fcf, fcf_yield, has_any_data)
    if market_cap is not None and free_cash_flow is not None:
        valuation_confidence = "Medium"
    elif pe is not None or p_fcf is not None:
        valuation_confidence = "Low"
    else:
        valuation_confidence = "Insufficient Data"

    notes: list[str] = []
    if market_cap is None:
        notes.append("Market cap is missing; valuation guardrails are limited.")
    if p_fcf is not None:
        notes.append("P/FCF uses market cap divided by free cash flow when market cap is available.")
    if valuation_status == "demanding":
        notes.append("Valuation appears demanding by preliminary P/FCF or FCF yield guardrails.")
    if valuation_status == "reasonable":
        notes.append("Valuation appears reasonable by preliminary P/FCF guardrails.")

    return {
        "market_cap": market_cap,
        "current_price": current_price,
        "net_income": net_income,
        "free_cash_flow": free_cash_flow,
        "pe": pe,
        "p_fcf": p_fcf,
        "earnings_yield": earnings_yield,
        "fcf_yield": fcf_yield,
        "valuation_status": valuation_status,
        "valuation_confidence": valuation_confidence,
        "notes": notes,
    }
