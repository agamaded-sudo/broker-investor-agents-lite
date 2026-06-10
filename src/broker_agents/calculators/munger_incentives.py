"""Deterministic Munger incentives and hidden-stupidity scoring."""

from typing import Any

from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.calculators.munger_inversion import build_munger_inversion_matrix
from broker_agents.calculators.owner_earnings import calculate_owner_earnings_snapshot
from broker_agents.calculators.valuation_guardrails import calculate_valuation_guardrails


def _to_float(value: Any) -> float | None:
    """Convert a value to float when possible."""
    if value in (None, "", "unavailable"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _contains_text(value: Any, terms: tuple[str, ...]) -> bool:
    """Search nested values for any lowercase term."""
    if isinstance(value, dict):
        return any(_contains_text(item, terms) for item in value.values())
    if isinstance(value, list):
        return any(_contains_text(item, terms) for item in value)
    text = str(value).lower()
    return any(term in text for term in terms)


def _label(score: int, strong: str, neutral: str, weak: str) -> str:
    """Map a zero-to-five score to a deterministic label."""
    if score >= 4:
        return strong
    if score == 3:
        return neutral
    return weak


def _model_risks(model: str) -> list[str]:
    """Return business-model-specific hidden-stupidity evidence gaps."""
    return {
        "software_cloud": [
            "AI/cloud capex return evidence and protection against an infrastructure arms race.",
            "Platform regulation, cloud margin durability, and valuation discipline.",
        ],
        "consumer_ecosystem": [
            "Key product dependence and ecosystem durability evidence.",
            "Services regulation exposure and buyback price discipline.",
        ],
        "semiconductor": [
            "Cycle-normalized earnings and customer concentration evidence.",
            "Inventory/capacity discipline and valuation assumptions for exceptional demand.",
        ],
        "retail": [
            "Inventory discipline, unit economics, store expansion returns, and consumer demand.",
        ],
        "payments_network": [
            "Regulatory fee pressure, take-rate durability, network disruption, and competition.",
        ],
        "industrial": [
            "Cycle-normalized earnings, capex discipline, input-cost fragility, and backlog quality.",
        ],
        "financial": [
            "Leverage, underwriting incentives, hidden balance-sheet risk, and funding costs.",
        ],
        "generic": [
            "Valuation discipline, incentive quality, capital allocation, and business durability.",
        ],
    }[model]


def score_munger_incentives_and_stupidity(pack: dict) -> dict:
    """Score incentives, capital allocation, and avoidable-error risk."""
    signals = extract_company_signals(pack)
    model = signals["business_model_type"]
    management = pack.get("management_ownership_incentives", {})
    allocation = pack.get("capital_allocation", {})
    annual = pack.get("financial_statements_summary", {}).get("annual", {})
    valuation = calculate_valuation_guardrails(pack)
    owner = calculate_owner_earnings_snapshot(pack)
    inversion = build_munger_inversion_matrix(pack)
    top_risk = next(
        (row for row in inversion if str(row.get("severity", "")).lower() == "high"),
        inversion[0],
    )
    gaps: list[str] = []
    positive: list[str] = []
    negative: list[str] = []
    required: list[str] = []

    has_compensation = _contains_text(
        management,
        ("compensation metric", "long-term incentive", "performance shares"),
    ) and not _contains_text(management, ("not included", "missing", "require"))
    has_ownership = _contains_text(
        management,
        ("insider ownership", "management ownership", "founder ownership"),
    ) and not _contains_text(management, ("missing", "require"))
    concerning_incentives = _contains_text(
        management,
        ("short-term", "aggressive", "misaligned", "concerning"),
    )
    if concerning_incentives:
        incentives_score = 2
        negative.append("Current incentive language indicates possible short-term or misaligned behavior.")
    elif has_compensation and has_ownership:
        incentives_score = 5
        positive.append("Compensation and ownership alignment evidence is present.")
    elif has_compensation or has_ownership:
        incentives_score = 4
        positive.append("Partial management alignment evidence is present.")
    else:
        incentives_score = 3
        gaps.extend(
            [
                "Management compensation metrics are missing.",
                "Insider ownership and alignment evidence are missing.",
                "Share-based compensation trend is missing.",
            ]
        )
        required.extend(
            [
                "Management compensation metrics.",
                "Insider ownership.",
                "Compensation structure and share-based compensation trend.",
            ]
        )

    repurchases = _to_float(
        allocation.get("share_repurchases", annual.get("share_repurchases"))
    )
    dividends = _to_float(allocation.get("dividends_paid", annual.get("dividends_paid")))
    fcf = owner["free_cash_flow"]
    if repurchases is None:
        buyback_score = 3
        gaps.append("Share repurchase history and buyback price discipline are missing.")
    elif repurchases > 0 and valuation["valuation_status"] == "demanding":
        buyback_score = 2
        negative.append("Buybacks occurred while preliminary valuation guardrails are demanding.")
        gaps.append("Buyback prices relative to intrinsic value are not established.")
    elif repurchases > 0 and valuation["valuation_status"] == "reasonable" and fcf:
        buyback_score = 4
        positive.append("Buybacks are supported by free cash flow and reasonable guardrails.")
        gaps.append("Buyback price discipline still needs transaction-level evidence.")
    else:
        buyback_score = 3
        gaps.append("Buyback value-accretion evidence is incomplete.")
    required.append("Buyback price discipline relative to intrinsic value.")

    if fcf and (repurchases is not None or dividends is not None):
        capital_score = 4
        positive.append("Capital returns are funded alongside positive free cash flow.")
    else:
        capital_score = 3
        gaps.append("Capital allocation funding and return evidence are incomplete.")
    if owner["capex_intensity_label"] == "high":
        capital_score = min(capital_score, 3)
        negative.append("High capex intensity requires clearer return-on-investment evidence.")

    cash = _to_float(annual.get("cash_and_short_term_investments"))
    debt = _to_float(annual.get("long_term_debt"))
    liabilities = _to_float(annual.get("total_liabilities"))
    if cash is not None and debt is not None and fcf:
        if cash >= debt:
            balance_score = 5
            positive.append("Cash exceeds long-term debt and free cash flow is positive.")
        elif debt <= fcf:
            balance_score = 4
            positive.append("Long-term debt appears manageable relative to annual free cash flow.")
        else:
            balance_score = 3
            gaps.append("Debt purpose, maturity schedule, and leverage policy need review.")
    else:
        balance_score = 3
        gaps.append("Complete cash, debt, liabilities, and debt-use evidence is missing.")
    if liabilities is None:
        gaps.append("Total liabilities evidence is incomplete.")
    required.append("Debt discipline, maturities, and use-of-debt evidence.")

    acquisition_section = allocation.get("acquisitions")
    if acquisition_section is None:
        acquisition_score = 3
        gaps.append("Acquisition history and post-acquisition returns are missing.")
    elif _contains_text(acquisition_section, ("disciplined", "return-focused", "limited")):
        acquisition_score = 4
        positive.append("Acquisition evidence indicates disciplined or return-focused behavior.")
    elif _contains_text(acquisition_section, ("aggressive", "unclear returns", "write-down")):
        acquisition_score = 2
        negative.append("Acquisition behavior may indicate empire building or weak return discipline.")
    else:
        acquisition_score = 3
        gaps.append("Acquisition return evidence remains incomplete.")
    required.append("Acquisition history, purchase prices, and realized returns.")

    hidden_score = 5
    if str(top_risk.get("severity", "")).lower() == "high":
        hidden_score -= 1
        negative.append(f"Top inversion risk is high: {top_risk['failure_mode']}.")
    if valuation["valuation_status"] == "demanding":
        hidden_score -= 1
        negative.append("Demanding valuation increases overconfidence and overpayment risk.")
    if model in {"semiconductor", "industrial", "financial"}:
        hidden_score -= 1
        negative.append("Cycle or balance-sheet sensitivity raises normalization risk.")
    if owner["capex_intensity_label"] == "high":
        hidden_score -= 1
        negative.append("High capex intensity lacks fully evidenced return attribution.")
    if buyback_score <= 2:
        hidden_score -= 1
    if incentives_score == 3:
        hidden_score -= 1
    hidden_score = max(1, min(5, hidden_score))

    model_gaps = _model_risks(model)
    gaps.extend(model_gaps)
    required.append(f"Evidence addressing top hidden-stupidity risk: {top_risk['failure_mode']}.")
    required.extend(model_gaps)
    overall = round(
        (
            incentives_score
            + capital_score
            + buyback_score
            + balance_score
            + acquisition_score
            + hidden_score
        )
        / 6,
        1,
    )
    interpretation = (
        f"The {model} business has an overall Munger quality score of {overall}/5. "
        f"Visible hidden-stupidity protection scores {hidden_score}/5; "
        "the result remains evidence-constrained rather than a final management judgment."
    )

    return {
        "business_model_type": model,
        "incentives_score": incentives_score,
        "capital_allocation_score": capital_score,
        "buyback_discipline_score": buyback_score,
        "balance_sheet_discipline_score": balance_score,
        "acquisition_discipline_score": acquisition_score,
        "hidden_stupidity_risk_score": hidden_score,
        "overall_munger_quality_score": overall,
        "incentives_label": _label(
            incentives_score,
            "aligned / evidence-backed",
            "unclear / needs evidence",
            "weak or concerning",
        ),
        "capital_allocation_label": _label(
            capital_score,
            "rational / disciplined",
            "adequate but incomplete evidence",
            "concerning",
        ),
        "hidden_stupidity_label": _label(
            hidden_score,
            "low visible risk",
            "medium / needs evidence",
            "high concern",
        ),
        "key_positive_evidence": list(dict.fromkeys(positive)),
        "key_negative_evidence": list(dict.fromkeys(negative)),
        "evidence_gaps": list(dict.fromkeys(gaps)),
        "munger_interpretation": interpretation,
        "required_evidence": list(dict.fromkeys(required)),
    }
