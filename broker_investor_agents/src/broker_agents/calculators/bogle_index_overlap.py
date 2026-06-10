"""Deterministic Bogle index-overlap and limited-weight guardrails."""

from typing import Any


def _to_float(value: Any) -> float | None:
    """Convert a value to float when possible."""
    if value in (None, "", "unavailable"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_bogle_index_overlap(pack: dict) -> dict:
    """Calculate indirect exposure and limited-weight portfolio guardrails."""
    identity = pack.get("company_identity", {})
    metadata = pack.get("metadata", {})
    ticker = str(identity.get("ticker") or metadata.get("ticker") or "").upper()
    context = pack.get("portfolio_context_form", {})
    provided = context.get("provided") is True
    holdings = context.get("current_holdings", {})
    index_funds = holdings.get("index_funds", []) if isinstance(holdings, dict) else []
    direct_stocks = holdings.get("direct_stocks", []) if isinstance(holdings, dict) else []
    constraints = context.get("constraints", {})
    estimates = context.get("indirect_exposure_estimates", {}).get(ticker, {})

    index_funds_owned = [
        str(item.get("ticker") or item.get("name") or "Unknown")
        for item in index_funds
        if isinstance(item, dict)
    ]
    index_core_weight = sum(
        _to_float(item.get("weight")) or 0
        for item in index_funds
        if isinstance(item, dict)
    )
    direct_holding = next(
        (
            item
            for item in direct_stocks
            if isinstance(item, dict)
            and str(item.get("ticker", "")).upper() == ticker
        ),
        {},
    )
    current_direct = _to_float(
        estimates.get("current_direct", direct_holding.get("weight"))
    )
    indirect = _to_float(estimates.get("via_index_funds"))
    total = _to_float(estimates.get("current_total"))
    if total is None and current_direct is not None and indirect is not None:
        total = current_direct + indirect

    maximum_weight = _to_float(constraints.get("maximum_single_stock_weight"))
    minimum_index_core = _to_float(constraints.get("minimum_index_core_weight"))
    technology_limit = _to_float(
        constraints.get("maximum_sector_weight_technology")
    )
    satellites_allowed = constraints.get("satellite_positions_allowed") is True
    remaining_capacity = (
        maximum_weight - current_direct
        if maximum_weight is not None and current_direct is not None
        else None
    )

    if indirect is None:
        overlap_label = "unknown"
    elif indirect >= 0.03:
        overlap_label = "high index overlap"
    elif indirect >= 0.01:
        overlap_label = "moderate index overlap"
    else:
        overlap_label = "low index overlap"

    if total is None or maximum_weight is None:
        concentration_label = "unknown"
    elif total >= maximum_weight:
        concentration_label = "high concentration risk"
    elif total >= 0.75 * maximum_weight:
        concentration_label = "moderate concentration risk"
    else:
        concentration_label = "manageable concentration risk"

    limited_candidate = bool(
        provided
        and satellites_allowed
        and minimum_index_core is not None
        and index_core_weight >= minimum_index_core
        and total is not None
        and maximum_weight is not None
        and total < maximum_weight
        and remaining_capacity is not None
        and remaining_capacity > 0
    )
    if limited_candidate:
        suggested_weight_range: dict | str = {
            "conservative": "1% to 2%",
            "moderate": "2% to 3%",
            "maximum_guardrail": min(remaining_capacity, maximum_weight),
        }
    else:
        suggested_weight_range = "No separate position suggested by guardrail"

    required_evidence = [
        "Index and ETF holdings validation.",
        "Benchmark-relative return and risk evidence.",
        "Proposed direct position size.",
        "Technology-sector exposure after the proposed position.",
    ]
    if not provided:
        required_evidence.insert(0, "Portfolio context.")
    if indirect is None:
        required_evidence.append("Verified indirect exposure through each index fund.")

    warnings = [
        "This is not a recommendation; it is a limited-weight guardrail for Bogle analysis.",
        "Indirect exposure estimates are manual placeholders and require index-holdings validation.",
        (
            "Remaining allowed single-stock capacity is calculated from current direct weight, "
            "while concentration risk includes indirect index exposure."
        ),
    ]
    if overlap_label == "high index overlap":
        warnings.append(
            "High index overlap means a separate position duplicates meaningful existing exposure."
        )

    return {
        "ticker": ticker,
        "portfolio_context_provided": provided,
        "index_funds_owned": index_funds_owned,
        "current_direct_weight": current_direct,
        "estimated_indirect_exposure": indirect,
        "current_total_exposure": total,
        "maximum_single_stock_weight": maximum_weight,
        "remaining_allowed_single_stock_capacity": remaining_capacity,
        "index_core_weight": index_core_weight if provided else None,
        "technology_sector_limit": technology_limit,
        "satellite_positions_allowed": satellites_allowed,
        "overlap_label": overlap_label,
        "concentration_risk_label": concentration_label,
        "limited_weight_candidate": limited_candidate,
        "suggested_weight_range": suggested_weight_range,
        "required_evidence": required_evidence,
        "warnings": warnings,
    }
