"""Deterministic company-specific language for broker-facing responses."""

import re

from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.calculators.bogle_index_overlap import (
    calculate_bogle_index_overlap,
)
from broker_agents.calculators.fisher_scuttlebutt import (
    build_fisher_scuttlebutt_checklist,
)
from broker_agents.calculators.intrinsic_value import (
    calculate_buffett_intrinsic_value_range,
)
from broker_agents.calculators.owner_earnings import calculate_owner_earnings_snapshot
from broker_agents.calculators.valuation_history import analyze_valuation_history


def _pack_text(pack: dict) -> str:
    """Return compact searchable company language."""
    values = [
        pack.get("business_model", {}),
        pack.get("company_identity", {}),
        pack.get("sector_specific_operating_kpis", {}),
        pack.get("growth_drivers", {}),
    ]
    return " ".join(str(value).lower() for value in values)


def _is_membership_retail(pack: dict) -> bool:
    signals = extract_company_signals(pack)
    return signals["business_model_type"] == "retail" and "membership" in _pack_text(pack)


def build_company_quality_thesis(pack: dict, investor_name: str) -> str:
    """Build a company-specific quality thesis for one investor."""
    investor = investor_name.lower()
    signals = extract_company_signals(pack)
    model = signals["business_model_type"]

    if _is_membership_retail(pack):
        theses = {
            "buffett": (
                "Membership economics, customer loyalty, pricing discipline, and "
                "recurring renewal behavior suggest a potentially durable retail franchise."
            ),
            "munger": (
                "High renewal behavior, disciplined merchandising, and a strong customer "
                "value proposition suggest an unusually durable retail culture."
            ),
            "fisher": (
                "Membership renewal, customer loyalty, warehouse productivity, and "
                "international expansion provide a credible long-term growth runway."
            ),
            "lynch": (
                "The story is concrete: membership renewal, comparable sales, warehouse "
                "expansion, pricing discipline, and a trusted customer value proposition."
            ),
            "bogle": (
                "The company may be high quality, but broad market or consumer-sector funds "
                "may already provide meaningful exposure."
            ),
        }
        return theses.get(investor, theses["buffett"])

    model_theses = {
        "software_cloud": (
            "Recurring enterprise demand, customer retention, and platform adoption support "
            "a potentially durable software and cloud franchise."
        ),
        "consumer_ecosystem": (
            "Installed-base loyalty, services adoption, and ecosystem retention support "
            "the quality case."
        ),
        "semiconductor": (
            "Product leadership, platform adoption, and data-center demand support the "
            "quality case, subject to cycle normalization."
        ),
        "retail": (
            "Customer loyalty, comparable sales, store economics, and inventory discipline "
            "support the retail quality case."
        ),
        "payments_network": (
            "Network effects, acceptance, and transaction growth support durable economics."
        ),
        "industrial": (
            "Customer relationships, product quality, and backlog conversion support the "
            "business-quality case."
        ),
        "financial": (
            "Customer franchise quality, underwriting discipline, and funding stability "
            "support the business-quality case."
        ),
        "generic": signals["investor_specific_angles"].get(
            investor,
            "Business quality requires additional company-specific evidence.",
        ),
    }
    return model_theses[model]


def build_company_growth_thesis(pack: dict, investor_name: str) -> str:
    """Build a concrete growth thesis from generalized company signals."""
    signals = extract_company_signals(pack)
    growth_engine = signals["primary_growth_engine"]
    investor = investor_name.lower()
    if _is_membership_retail(pack):
        if investor == "lynch":
            return (
                "Membership renewal, comparable sales, warehouse expansion, pricing "
                "discipline, and customer value define the growth story."
            )
        if investor == "fisher":
            return (
                "The growth runway depends on renewal durability, member loyalty, warehouse "
                "economics, supplier relationships, and international execution."
            )
    return f"The company-specific growth case centers on {growth_engine.lower()}."


def _fisher_follow_ups(pack: dict) -> list[str]:
    checklist = build_fisher_scuttlebutt_checklist(pack)
    items = [
        str(item["evidence_needed"]).rstrip(".")
        for item in checklist["priority_items"]
        if item["blocks_fisher_upgrade"]
    ]
    if _is_membership_retail(pack):
        items.extend(
            [
                "Validate membership renewal-rate durability and customer loyalty",
                "Assess supplier relationship quality and merchandising discipline",
                "Review international expansion quality and warehouse execution",
                "Assess employee culture and operating execution",
            ]
        )
    return list(dict.fromkeys(items))


def build_company_specific_follow_up_items(
    pack: dict,
    investor_name: str,
) -> list[str]:
    """Build ordered, investor-specific broker follow-up items."""
    investor = investor_name.lower()
    signals = extract_company_signals(pack)
    follow_ups = {
        "buffett": [
            "Update the owner-earnings range and margin-of-safety assessment",
            "Validate maintenance versus growth capex",
            "Compare current valuation with the 10-year valuation history",
        ],
        "munger": [
            "Validate management incentives, ownership, and compensation metrics",
            "Review capital allocation and buyback discipline",
            "Test the leading inversion risks and avoidable-error scenarios",
        ],
        "fisher": _fisher_follow_ups(pack),
        "lynch": [
            "Validate growth rates and PEG methodology",
            "Confirm the Lynch category classification and growth runway",
            f"Validate operating evidence for {signals['primary_growth_engine'].lower()}",
        ],
        "bogle": [
            "Validate index and ETF overlap",
            "Compare individual-stock risk with broad-index exposure",
            "Confirm current indirect exposure and any proposed position size",
        ],
    }
    return follow_ups.get(
        investor,
        ["Collect the company-specific evidence required by the investor report"],
    )


def clean_mismatched_investor_language(text: str, pack: dict) -> str:
    """Replace sector-mismatched technology language in broker-facing text."""
    if not text:
        return text
    model = extract_company_signals(pack)["business_model_type"]
    if model in {"software_cloud", "semiconductor"}:
        return text

    if _is_membership_retail(pack):
        replacements = {
            r"AI Capex Returns": "Incentives and Long-Term Durability",
            r"AI infrastructure capex": "store expansion quality and capital discipline",
            r"GPU cycle": "retail demand and inventory cycle",
            r"cloud workload growth": "membership and comparable-sales growth",
        }
    else:
        replacements = {
            r"AI Capex Returns": "Business Durability and Capital Returns",
            r"AI infrastructure capex": "business-model-specific capital investment",
            r"GPU cycle": "business cycle",
            r"cloud workload growth": "company-specific growth",
        }
    cleaned = text
    for pattern, replacement in replacements.items():
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    return cleaned


def build_polished_response_language(pack: dict, investor_name: str) -> dict:
    """Build polished response fields while preserving governed decisions."""
    investor = investor_name.lower()
    signals = extract_company_signals(pack)
    quality = build_company_quality_thesis(pack, investor)
    growth = build_company_growth_thesis(pack, investor)
    follow_ups = build_company_specific_follow_up_items(pack, investor)

    if investor == "buffett":
        owner = calculate_owner_earnings_snapshot(pack)
        history = analyze_valuation_history(pack)
        intrinsic = calculate_buffett_intrinsic_value_range(pack)
        concern = (
            f"Owner earnings quality is {owner['owner_earnings_quality_label']}, while "
            f"valuation history is {history['valuation_history_label']} and the preliminary "
            f"intrinsic value gap is {intrinsic['valuation_gap_label']}."
        )
        required = follow_ups[0]
        positive = quality
    elif investor == "munger":
        concern = (
            "Business quality does not remove the need to validate incentives, capital "
            "allocation discipline, and the risk of overpaying."
        )
        required = follow_ups[0]
        positive = quality
    elif investor == "fisher":
        checklist = build_fisher_scuttlebutt_checklist(pack)
        areas = [
            str(item["evidence_area"])
            for item in checklist["priority_items"]
            if item["blocks_fisher_upgrade"]
        ]
        concern = "High-priority scuttlebutt gaps include: " + ", ".join(areas[:5]) + "."
        required = "; ".join(follow_ups[:3]) + "."
        positive = growth
    elif investor == "lynch":
        growth_peg = pack.get("growth_peg_analysis", {})
        peg = growth_peg.get("peg_ratio")
        concern = (
            f"The PEG ratio of {peg:.2f} is demanding relative to current growth."
            if isinstance(peg, (int, float))
            else "Valuation versus growth still requires a verified PEG assessment."
        )
        required = follow_ups[0]
        positive = growth
    elif investor == "bogle":
        overlap = calculate_bogle_index_overlap(pack)
        if overlap["overlap_label"] == "unknown":
            concern = (
                "Before discussing any individual-position case, validate whether broad "
                "market or consumer/retail ETFs already provide sufficient exposure."
            )
        else:
            concern = (
                f"Estimated index overlap is {overlap['overlap_label']}; separate ownership "
                "still requires portfolio-level justification."
            )
        required = follow_ups[0]
        positive = quality
    else:
        concern = signals["decision_rationales"].get(
            investor,
            "Company-specific evidence remains incomplete.",
        )
        required = follow_ups[0]
        positive = quality

    return {
        "main_positive_reason": clean_mismatched_investor_language(positive, pack),
        "main_concern": clean_mismatched_investor_language(concern, pack),
        "required_evidence_before_serious_interest": clean_mismatched_investor_language(
            required,
            pack,
        ),
        "broker_follow_up_items": [
            clean_mismatched_investor_language(item, pack) for item in follow_ups
        ],
    }
