"""Preliminary deterministic Buffett intrinsic value range."""

from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.calculators.owner_earnings import calculate_owner_earnings_snapshot

ASSUMPTIONS = {
    "software_cloud": (0.03, 0.06, 0.09, 15, 20, 25),
    "consumer_ecosystem": (0.02, 0.04, 0.06, 14, 18, 22),
    "semiconductor": (0.00, 0.05, 0.10, 10, 16, 22),
    "retail": (0.01, 0.03, 0.05, 10, 14, 18),
    "payments_network": (0.03, 0.06, 0.08, 16, 22, 26),
    "industrial": (0.00, 0.03, 0.05, 8, 12, 16),
    "financial": (0.00, 0.03, 0.05, 8, 11, 14),
    "generic": (0.00, 0.03, 0.05, 8, 12, 16),
}


def _project_value(
    owner_earnings: float,
    growth_rate: float,
    discount_rate: float,
    terminal_multiple: float,
) -> float:
    """Discount ten years of owner earnings and the year-ten terminal value."""
    present_value = 0.0
    year_earnings = owner_earnings
    for year in range(1, 11):
        year_earnings *= 1 + growth_rate
        present_value += year_earnings / ((1 + discount_rate) ** year)
    terminal_value = year_earnings * terminal_multiple
    return present_value + terminal_value / ((1 + discount_rate) ** 10)


def _margin_of_safety(
    intrinsic_value: float | None,
    market_cap: float | None,
) -> float | None:
    """Calculate margin of safety relative to market capitalization."""
    if intrinsic_value is None or market_cap in (None, 0):
        return None
    return (intrinsic_value - market_cap) / market_cap


def _valuation_gap_label(mid_margin: float | None) -> str:
    """Classify the midpoint margin of safety."""
    if mid_margin is None:
        return "not established"
    if mid_margin >= 0.30:
        return "materially undervalued"
    if mid_margin >= 0.10:
        return "moderately undervalued"
    if mid_margin > -0.10:
        return "near fair value"
    return "overvalued"


def calculate_buffett_intrinsic_value_range(pack: dict) -> dict:
    """Calculate a cautious ten-year owner-earnings intrinsic value range."""
    signals = extract_company_signals(pack)
    owner = calculate_owner_earnings_snapshot(pack)
    model = signals["business_model_type"]
    (
        growth_low,
        growth_mid,
        growth_high,
        multiple_low,
        multiple_mid,
        multiple_high,
    ) = ASSUMPTIONS[model]
    discount_rate = 0.10
    owner_earnings_base = owner["owner_earnings_proxy"]
    market_cap = pack.get("valuation_snapshot", {}).get("market_cap")
    try:
        market_cap = float(market_cap)
    except (TypeError, ValueError):
        market_cap = None

    values: list[float | None] = [None, None, None]
    if owner_earnings_base is not None:
        values = [
            _project_value(
                float(owner_earnings_base),
                growth_rate,
                discount_rate,
                terminal_multiple,
            )
            for growth_rate, terminal_multiple in (
                (growth_low, multiple_low),
                (growth_mid, multiple_mid),
                (growth_high, multiple_high),
            )
        ]

    margins = [_margin_of_safety(value, market_cap) for value in values]
    if owner_earnings_base is None or market_cap is None:
        confidence = "Insufficient Data"
    elif (
        owner["capex_intensity_label"] == "high"
        or model in {"semiconductor", "industrial", "financial"}
    ):
        confidence = "Low"
    elif owner["owner_earnings_quality_label"] == "strong":
        confidence = "Medium"
    else:
        confidence = "Low"

    warnings = [
        "This is a preliminary deterministic estimate, not a full DCF.",
        "Growth and terminal multiples are simplified assumptions.",
        "Historical valuation and full normalized earnings are still needed.",
    ]
    if model in {"semiconductor", "industrial", "financial"}:
        warnings.append(
            "For semiconductor or cyclical companies, normalized cycle earnings are especially important."
        )
    if owner["capex_intensity_label"] == "high":
        warnings.append(
            "For high capex companies, the maintenance versus growth capex split is still needed."
        )

    return {
        "owner_earnings_base": owner_earnings_base,
        "growth_rate_low": growth_low,
        "growth_rate_mid": growth_mid,
        "growth_rate_high": growth_high,
        "discount_rate": discount_rate,
        "terminal_multiple_low": multiple_low,
        "terminal_multiple_mid": multiple_mid,
        "terminal_multiple_high": multiple_high,
        "intrinsic_value_low": values[0],
        "intrinsic_value_mid": values[1],
        "intrinsic_value_high": values[2],
        "market_cap": market_cap,
        "margin_of_safety_low": margins[0],
        "margin_of_safety_mid": margins[1],
        "margin_of_safety_high": margins[2],
        "valuation_gap_label": _valuation_gap_label(margins[1]),
        "intrinsic_value_confidence": confidence,
        "assumptions": [
            f"Business model type: {model}.",
            f"Discount rate: {discount_rate:.0%}.",
            (
                f"Growth rates: {growth_low:.0%} low, {growth_mid:.0%} mid, "
                f"{growth_high:.0%} high."
            ),
            (
                f"Terminal multiples: {multiple_low}x low, {multiple_mid}x mid, "
                f"{multiple_high}x high."
            ),
            "Owner earnings base uses the current operating cash flow minus capex proxy.",
        ],
        "warnings": warnings,
    }
