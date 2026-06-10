"""Deterministic analysis of manual valuation-history evidence."""

from typing import Any

from broker_agents.calculators.valuation_guardrails import (
    calculate_valuation_guardrails,
)


def _to_float(value: Any) -> float | None:
    """Convert a value to float when possible."""
    if value in (None, "", "unavailable"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def analyze_valuation_history(pack: dict) -> dict:
    """Compare current valuation with manual 5Y and 10Y history placeholders."""
    history = pack.get("historical_valuation", {})
    guardrails = calculate_valuation_guardrails(pack)
    current_p_fcf = guardrails["p_fcf"]
    p_fcf_5y = _to_float(history.get("p_fcf_5y_median"))
    p_fcf_10y = _to_float(history.get("p_fcf_10y_median"))

    if current_p_fcf is None or p_fcf_5y is None or p_fcf_10y is None:
        label = "not established"
    elif current_p_fcf < 0.85 * p_fcf_5y and current_p_fcf < 0.85 * p_fcf_10y:
        label = "below historical range"
    elif 0.85 * p_fcf_5y <= current_p_fcf <= 1.15 * p_fcf_5y:
        label = "near historical range"
    elif current_p_fcf > 1.15 * p_fcf_5y:
        label = "above historical range"
    else:
        label = "near historical range"

    confidence = str(
        history.get("valuation_history_confidence") or "not established"
    )
    gaps: list[str] = []
    required_fields = (
        "pe_5y_median",
        "pe_10y_median",
        "p_fcf_5y_median",
        "p_fcf_10y_median",
        "ev_ebitda_5y_median",
        "ev_ebitda_10y_median",
    )
    for field in required_fields:
        if _to_float(history.get(field)) is None:
            gaps.append(f"{field} is missing.")
    if "placeholder" in confidence.lower():
        gaps.extend(
            [
                "Valuation history source verification is required.",
                "5Y/10Y valuation data validation is required.",
            ]
        )

    notes = ["Current P/FCF is calculated from market cap and latest free cash flow."]
    if "market" in confidence.lower() and "placeholder" not in confidence.lower():
        notes.append(
            "Historical valuation values use a medium-confidence market fixture; "
            "provider and calculation methodology still require validation."
        )
    else:
        notes.append(
            "Historical valuation values are manual placeholders until source-verified."
        )
    if label == "above historical range":
        notes.append("Current P/FCF is more than 15% above the 5Y median.")
    elif label == "near historical range":
        notes.append("Current P/FCF is within 15% of the 5Y median.")
    elif label == "below historical range":
        notes.append("Current P/FCF is meaningfully below both 5Y and 10Y medians.")

    return {
        "current_pe": guardrails["pe"],
        "current_p_fcf": current_p_fcf,
        "pe_5y_median": _to_float(history.get("pe_5y_median")),
        "pe_10y_median": _to_float(history.get("pe_10y_median")),
        "p_fcf_5y_median": p_fcf_5y,
        "p_fcf_10y_median": p_fcf_10y,
        "ev_ebitda_5y_median": _to_float(history.get("ev_ebitda_5y_median")),
        "ev_ebitda_10y_median": _to_float(history.get("ev_ebitda_10y_median")),
        "current_vs_5y_p_fcf_percentile": _to_float(
            history.get("current_vs_5y_p_fcf_percentile")
        ),
        "current_vs_10y_p_fcf_percentile": _to_float(
            history.get("current_vs_10y_p_fcf_percentile")
        ),
        "valuation_history_label": label,
        "valuation_history_confidence": confidence,
        "notes": notes,
        "evidence_gaps": list(dict.fromkeys(gaps)),
    }
