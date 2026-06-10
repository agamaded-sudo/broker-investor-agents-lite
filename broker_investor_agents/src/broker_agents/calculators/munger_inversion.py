"""Munger-style inversion risk matrix generation."""

from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.calculators.owner_earnings import calculate_owner_earnings_snapshot
from broker_agents.calculators.valuation_guardrails import calculate_valuation_guardrails


def build_munger_inversion_matrix(pack: dict) -> list[dict]:
    """Build a deterministic company-specific Munger inversion risk matrix."""
    signals = extract_company_signals(pack)
    owner_earnings = calculate_owner_earnings_snapshot(pack)
    valuation = calculate_valuation_guardrails(pack)
    business_model_type = signals.get("business_model_type", "generic")
    capex_profile = signals.get("capex_profile", "unknown")
    major_capex_issue = signals.get("major_capex_issue", "Capex issue not established")
    valuation_status = valuation.get("valuation_status", "not established")
    capex_evidence = (
        f"{capex_profile}; {major_capex_issue}; owner earnings capex label is "
        f"{owner_earnings.get('capex_intensity_label', 'unknown')}."
    )

    matrices: dict[str, list[dict]] = {
        "software_cloud": [
            {
                "failure_mode": "AI infrastructure capex / cloud expansion becomes an expensive arms race",
                "evidence": capex_evidence,
                "severity": "high",
                "what_would_reduce_the_risk": "Evidence that AI capex produces durable revenue, margin, and FCF growth.",
            },
            {
                "failure_mode": "Cloud margin compression",
                "evidence": "Cloud growth is strong but capex and competition remain important.",
                "severity": "medium",
                "what_would_reduce_the_risk": "Stable or improving cloud margins and segment profitability.",
            },
            {
                "failure_mode": "Regulatory/platform risk",
                "evidence": "Large platform company with enterprise software, cloud, and AI reach.",
                "severity": "medium",
                "what_would_reduce_the_risk": "Manageable fines, no structural remedies, continued customer retention.",
            },
            {
                "failure_mode": "Overpaying for a great business",
                "evidence": f"Valuation guardrails are {valuation_status} based on available P/FCF and FCF yield.",
                "severity": "high",
                "what_would_reduce_the_risk": "Lower valuation or faster owner earnings growth.",
            },
        ],
        "consumer_ecosystem": [
            {
                "failure_mode": "Key product dependence weakens long-term growth",
                "evidence": f"The dominant revenue stream is {signals.get('dominant_revenue_stream', 'not established')}.",
                "severity": "high",
                "what_would_reduce_the_risk": "Services and other products grow enough to reduce dependency.",
            },
            {
                "failure_mode": "Services regulation or platform fee pressure",
                "evidence": "Services monetization is a major growth engine.",
                "severity": "medium",
                "what_would_reduce_the_risk": "Services growth continues with resilient margins despite regulation.",
            },
            {
                "failure_mode": "Supply chain / geographic concentration risk",
                "evidence": "A hardware-led ecosystem depends on resilient production and international markets.",
                "severity": "medium",
                "what_would_reduce_the_risk": "Geographic diversification and resilient supply chain execution.",
            },
            {
                "failure_mode": "Buybacks become value-destructive if valuation is too high",
                "evidence": "Large repurchases and valuation guardrails require discipline.",
                "severity": "medium",
                "what_would_reduce_the_risk": "Repurchases remain disciplined relative to intrinsic value.",
            },
        ],
        "semiconductor": [
            {
                "failure_mode": "Semiconductor cycle turns against earnings",
                "evidence": "Demand, pricing, and utilization can move sharply across the semiconductor cycle.",
                "severity": "high",
                "what_would_reduce_the_risk": "Resilient normalized earnings across a full demand cycle.",
            },
            {
                "failure_mode": "Customer concentration or demand normalization",
                "evidence": "Large customers and concentrated end markets can amplify demand changes.",
                "severity": "high",
                "what_would_reduce_the_risk": "Broader customers, end markets, and durable platform adoption.",
            },
            {
                "failure_mode": "Inventory / capacity mismatch",
                "evidence": capex_evidence,
                "severity": "medium",
                "what_would_reduce_the_risk": "Disciplined inventory, utilization, and capacity planning.",
            },
            {
                "failure_mode": "Valuation reflects peak earnings",
                "evidence": f"Valuation guardrails are {valuation_status}.",
                "severity": "high",
                "what_would_reduce_the_risk": "Valuation supported by normalized rather than peak-cycle earnings.",
            },
        ],
        "retail": [
            {
                "failure_mode": "Same-store sales weaken",
                "evidence": "Comparable-store demand is central to retail operating leverage.",
                "severity": "high",
                "what_would_reduce_the_risk": "Sustained traffic, ticket, and same-store sales growth.",
            },
            {
                "failure_mode": "Inventory mistakes pressure margins",
                "evidence": "Markdowns and poor inventory turns can erase retail margins.",
                "severity": "high",
                "what_would_reduce_the_risk": "Healthy inventory turns and limited markdown pressure.",
            },
            {
                "failure_mode": "Store expansion destroys returns",
                "evidence": major_capex_issue,
                "severity": "medium",
                "what_would_reduce_the_risk": "New stores achieve attractive unit economics and payback periods.",
            },
            {
                "failure_mode": "Consumer demand slows",
                "evidence": "Retail revenue is exposed to customer traffic and discretionary spending.",
                "severity": "medium",
                "what_would_reduce_the_risk": "Resilient demand across economic conditions.",
            },
        ],
        "payments_network": [
            {
                "failure_mode": "Regulatory fee pressure",
                "evidence": "Network fees and market power can attract regulatory scrutiny.",
                "severity": "high",
                "what_would_reduce_the_risk": "Stable economics after regulatory changes.",
            },
            {
                "failure_mode": "Payment volume slowdown",
                "evidence": "Transaction revenue depends on payment and cross-border volume.",
                "severity": "medium",
                "what_would_reduce_the_risk": "Durable volume growth across regions and payment types.",
            },
            {
                "failure_mode": "Network disruption or competition",
                "evidence": "Alternative rails and technology shifts may weaken network effects.",
                "severity": "medium",
                "what_would_reduce_the_risk": "Stable acceptance, share, and transaction growth.",
            },
            {
                "failure_mode": "Valuation exceeds durable growth",
                "evidence": f"Valuation guardrails are {valuation_status}.",
                "severity": "high",
                "what_would_reduce_the_risk": "Price discipline or faster durable owner earnings growth.",
            },
        ],
        "industrial": [
            {
                "failure_mode": "Cycle downturn hits orders and margins",
                "evidence": "Orders, backlog, utilization, and pricing are cycle-sensitive.",
                "severity": "high",
                "what_would_reduce_the_risk": "Resilient backlog conversion and normalized margins.",
            },
            {
                "failure_mode": "Input cost or energy pressure",
                "evidence": "Industrial margins can be exposed to commodity, labor, and energy costs.",
                "severity": "medium",
                "what_would_reduce_the_risk": "Pricing power and effective cost pass-through.",
            },
            {
                "failure_mode": "Capital intensity weakens owner returns",
                "evidence": capex_evidence,
                "severity": "high",
                "what_would_reduce_the_risk": "Strong returns on maintenance and expansion capital.",
            },
            {
                "failure_mode": "Backlog quality deteriorates",
                "evidence": "Reported backlog may not convert if demand or financing weakens.",
                "severity": "medium",
                "what_would_reduce_the_risk": "Stable cancellations and reliable backlog conversion.",
            },
        ],
        "financial": [
            {
                "failure_mode": "Credit losses or balance sheet risk emerge",
                "evidence": "Leverage and underwriting can hide losses until the credit cycle turns.",
                "severity": "high",
                "what_would_reduce_the_risk": "Conservative reserves, capital, and through-cycle loss performance.",
            },
            {
                "failure_mode": "Incentives encourage leverage or poor underwriting",
                "evidence": "Compensation can reward growth before risk becomes visible.",
                "severity": "high",
                "what_would_reduce_the_risk": "Long-term incentives tied to risk-adjusted returns.",
            },
            {
                "failure_mode": "Funding cost pressure",
                "evidence": "Funding mix and rates can compress spreads.",
                "severity": "medium",
                "what_would_reduce_the_risk": "Stable deposits or funding and resilient spreads.",
            },
            {
                "failure_mode": "Book value quality deteriorates",
                "evidence": "Asset marks, reserves, and credit quality determine usable book value.",
                "severity": "high",
                "what_would_reduce_the_risk": "Transparent asset quality and stable tangible book value.",
            },
        ],
        "generic": [
            {
                "failure_mode": "Overpaying for quality",
                "evidence": "Valuation history and intrinsic value work are incomplete.",
                "severity": "medium",
                "what_would_reduce_the_risk": "Clear margin of safety and valuation history.",
            },
            {
                "failure_mode": "Margin deterioration",
                "evidence": "Future margins are not fully established.",
                "severity": "medium",
                "what_would_reduce_the_risk": "Stable or improving margins over multiple periods.",
            },
            {
                "failure_mode": "Capital allocation error",
                "evidence": "Capital allocation quality requires deeper review.",
                "severity": "medium",
                "what_would_reduce_the_risk": "Evidence of disciplined reinvestment, buybacks, and balance sheet use.",
            },
            {
                "failure_mode": "Business model weakening",
                "evidence": "Durability indicators require more company-specific evidence.",
                "severity": "medium",
                "what_would_reduce_the_risk": "Stable retention, pricing power, and competitive position.",
            },
        ],
    }
    return matrices.get(business_model_type, matrices["generic"])
