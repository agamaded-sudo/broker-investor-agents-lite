"""Deterministic Buffett decision upgrade and downgrade conditions."""

from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.calculators.owner_earnings import calculate_owner_earnings_snapshot
from broker_agents.calculators.valuation_guardrails import calculate_valuation_guardrails


def build_buffett_decision_conditions(pack: dict) -> dict:
    """Build Buffett decision upgrade, downgrade, and watch conditions."""
    owner_earnings = calculate_owner_earnings_snapshot(pack)
    valuation = calculate_valuation_guardrails(pack)
    signals = extract_company_signals(pack)
    valuation_status = valuation.get("valuation_status")
    capex_profile = signals.get("capex_profile", "unknown")
    quality_label = owner_earnings.get("owner_earnings_quality_label")
    business_model_type = signals.get("business_model_type", "generic")
    major_data_gaps = signals.get("major_data_gaps", [])

    upgrade_conditions: list[str] = []
    watch_items: list[str] = []

    if valuation_status == "demanding":
        upgrade_conditions.extend(
            [
                "P/FCF moves closer to a reasonable range.",
                "FCF yield improves.",
                "Intrinsic value work shows adequate margin of safety.",
                "Owner earnings remain durable after capex normalization.",
            ]
        )
    elif valuation_status == "reasonable":
        upgrade_conditions.extend(
            [
                "Intrinsic value work confirms adequate margin of safety.",
                "Owner earnings remain durable over multiple years.",
                "Management capital allocation remains rational.",
                "Business quality and moat evidence remain strong.",
            ]
        )
    else:
        upgrade_conditions.extend(
            [
                "Valuation guardrails become established with reliable market data.",
                "Intrinsic value work shows adequate margin of safety.",
            ]
        )

    if capex_profile == "high_capex_intensity":
        upgrade_conditions.extend(
            [
                "Clearer maintenance vs growth capex split.",
                f"Evidence that {signals['major_capex_issue'].lower()} produces attractive returns.",
                "Stable or improving FCF after growth capex.",
            ]
        )

    if capex_profile == "low_capex_intensity" and quality_label == "strong":
        watch_items.extend(
            [
                "Whether strong cash conversion persists.",
                "Whether buybacks are value-accretive.",
                "Whether growth remains durable.",
            ]
        )

    if business_model_type != "generic":
        watch_items.append(
            f"Durability of the {business_model_type.replace('_', ' ')} business model."
        )
    if major_data_gaps:
        watch_items.append(f"Resolution of key data gap: {major_data_gaps[0]}")
    watch_items.extend(
        [
            signals.get("major_capex_issue", "Capex issue not established."),
            signals.get("major_margin_issue", "Margin issue not established."),
        ]
    )

    return {
        "current_decision": "Wait for Better Price / Complete Intrinsic Value Work",
        "upgrade_conditions": upgrade_conditions,
        "downgrade_conditions": [
            "Weakening FCF margin.",
            "Rising capex intensity without evidence of returns.",
            "Deterioration in moat or pricing power.",
            "Aggressive debt-funded buybacks or acquisitions.",
            "Valuation becomes more demanding without earnings growth.",
        ],
        "watch_items": watch_items,
    }
