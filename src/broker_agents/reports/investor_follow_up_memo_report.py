"""Investor-specific evidence collection memos for broker follow-up."""

from pathlib import Path

from broker_agents.deals.investor_interest_response import InvestorInterestResponse

INVESTOR_KEYS = {
    "buffett": "buffett",
    "warren buffett": "buffett",
    "munger": "munger",
    "charlie munger": "munger",
    "fisher": "fisher",
    "philip fisher": "fisher",
    "lynch": "lynch",
    "peter lynch": "lynch",
    "bogle": "bogle",
    "john bogle": "bogle",
}

INVESTOR_MEMO_SPECS = {
    "buffett": {
        "categories": [
            "official_financials",
            "historical_valuation",
            "market_data",
        ],
        "focus": "Owner earnings, intrinsic value, margin of safety, and capex normalization",
        "checklist": [
            (
                "Normalized owner earnings and free-cash-flow history",
                "Official filings and calculated history",
                "Tests whether current owner earnings are durable across operating conditions.",
                "official_financials",
                "high",
            ),
            (
                "Maintenance versus growth capital expenditure",
                "Official filings and management disclosures",
                "Separates sustaining economics from discretionary growth investment.",
                "official_financials",
                "high",
            ),
            (
                "Intrinsic value range and margin-of-safety validation",
                "Calculation with verified market data",
                "Tests whether price leaves a conservative valuation buffer.",
                "market_data",
                "high",
            ),
            (
                "Five-year and ten-year valuation history",
                "Historical market-data provider",
                "Places current valuation and free-cash-flow multiples in context.",
                "historical_valuation",
                "medium",
            ),
        ],
    },
    "munger": {
        "categories": [
            "management_incentives",
            "official_financials",
            "scuttlebutt",
        ],
        "focus": "Management incentives, ownership, capital allocation, and inversion risks",
        "checklist": [
            (
                "Management compensation metrics and incentive structure",
                "Proxy statement and compensation disclosures",
                "Shows whether incentives reward durable per-share value creation.",
                "management_incentives",
                "high",
            ),
            (
                "Insider ownership and management tenure",
                "Proxy statement and ownership filings",
                "Tests alignment with long-term owners.",
                "management_incentives",
                "high",
            ),
            (
                "Capital allocation and buyback discipline",
                "Official filings and capital-return history",
                "Tests whether cash is deployed rationally and at sensible prices.",
                "official_financials",
                "high",
            ),
            (
                "Culture, acquisition discipline, and avoidable-error checks",
                "Qualitative field evidence and governance review",
                "Surfaces incentive-caused bias and hidden-stupidity risks.",
                "scuttlebutt",
                "medium",
            ),
        ],
    },
    "fisher": {
        "categories": ["scuttlebutt", "management_incentives"],
        "focus": "Customer, product, supplier, employee-culture, and competitive evidence",
        "checklist": [
            (
                "Customer traffic and visit-frequency evidence",
                "Customer and operating KPI evidence",
                "Tests real customer engagement and demand durability.",
                "scuttlebutt",
                "high",
            ),
            (
                "Repeat purchase, loyalty, and renewal durability",
                "Customer retention and membership evidence",
                "Tests whether customer relationships compound over time.",
                "scuttlebutt",
                "high",
            ),
            (
                "Same-store sales and store economics",
                "Operating data and source verification",
                "Tests unit-level growth quality and economic productivity.",
                "scuttlebutt",
                "high",
            ),
            (
                "Inventory discipline and supplier relationships",
                "Supplier, partner, and operating evidence",
                "Tests execution quality and merchandise economics.",
                "scuttlebutt",
                "medium",
            ),
            (
                "Employee culture and management depth",
                "Employee, culture, and management evidence",
                "Tests whether the organization can sustain expansion and service quality.",
                "management_incentives",
                "medium",
            ),
        ],
    },
    "lynch": {
        "categories": [
            "growth_peg",
            "market_data",
            "historical_valuation",
        ],
        "focus": "PEG, growth methodology, category classification, and operating runway",
        "checklist": [
            (
                "PEG and growth-rate methodology",
                "Growth estimates and calculation validation",
                "Tests whether valuation is supported by a realistic growth rate.",
                "growth_peg",
                "high",
            ),
            (
                "Company category classification",
                "Business-model and operating evidence",
                "Tests whether the story fits the expected growth and cyclicality profile.",
                "growth_peg",
                "medium",
            ),
            (
                "Comparable sales and warehouse expansion quality",
                "Operating KPI history",
                "Tests the concrete drivers behind the understandable growth story.",
                "growth_peg",
                "high",
            ),
            (
                "Pricing discipline and valuation history",
                "Market and historical valuation data",
                "Tests whether a good story is being purchased at an excessive price.",
                "historical_valuation",
                "medium",
            ),
        ],
    },
    "bogle": {
        "categories": ["index_overlap", "market_data"],
        "focus": "Index overlap, ETF holdings, concentration, and benchmark-relative risk",
        "checklist": [
            (
                "Index and ETF holdings overlap",
                "Verified fund holdings",
                "Determines how much exposure already exists through broad funds.",
                "index_overlap",
                "high",
            ),
            (
                "Current indirect and total company exposure",
                "Portfolio holdings calculation",
                "Tests whether a separate position would duplicate existing exposure.",
                "index_overlap",
                "high",
            ),
            (
                "Beta, volatility, drawdown, and correlation",
                "Benchmark-relative market data",
                "Compares individual-stock risk with broad index exposure.",
                "index_overlap",
                "high",
            ),
            (
                "Proposed position size and concentration guardrail",
                "User portfolio input",
                "Tests whether any satellite exposure fits the investor's constraints.",
                "market_data",
                "medium",
            ),
        ],
    },
}


def _investor_key(investor: str) -> str:
    """Normalize an investor display name to a memo specification key."""
    return INVESTOR_KEYS.get(investor.lower(), investor.lower().replace(" ", "_"))


def get_investor_follow_up_focus(investor: str) -> str:
    """Return the compact evidence focus used in the broker package."""
    spec = INVESTOR_MEMO_SPECS.get(_investor_key(investor))
    if spec is None:
        return "Investor-specific evidence and source verification"
    return str(spec["focus"])


def _relevant_categories(
    investor: str,
    source_verification_summary: dict,
) -> list[dict]:
    """Select source-matrix rows relevant to one investor."""
    spec = INVESTOR_MEMO_SPECS.get(_investor_key(investor), {})
    wanted = set(spec.get("categories", []))
    return [
        item
        for item in source_verification_summary.get("categories", [])
        if item.get("category") in wanted
    ]


def generate_investor_follow_up_memo(
    ticker: str,
    company_name: str,
    investor_response: InvestorInterestResponse,
    source_verification_summary: dict,
) -> str:
    """Generate one deterministic investor-specific evidence collection memo."""
    key = _investor_key(investor_response.investor)
    spec = INVESTOR_MEMO_SPECS.get(
        key,
        {
            "categories": [],
            "focus": "Investor-specific evidence and source verification",
            "checklist": [],
        },
    )
    relevant = _relevant_categories(
        investor_response.investor,
        source_verification_summary,
    )
    blocking = [
        item
        for item in relevant
        if item.get("blocks_promotion")
    ]
    evidence_items = list(
        dict.fromkeys(
            [
                investor_response.required_evidence_before_serious_interest,
                *investor_response.broker_follow_up_items,
            ]
        )
    )
    lines = [
        f"# {investor_response.investor} Follow-Up Memo - {ticker.upper()}",
        "",
        "## 1. Purpose",
        "",
        (
            f"This memo helps the broker and Backoffice collect missing evidence "
            f"for {investor_response.investor}'s independent review of "
            f"{company_name} ({ticker.upper()})."
        ),
        "",
        "## 2. Investor Decision Snapshot",
        "",
        f"- Final Decision: {investor_response.broker_facing_final_decision}",
        f"- Candidate Decision: {investor_response.candidate_decision}",
        f"- Interest Level: {investor_response.interest_level}",
        f"- Interest Type: {investor_response.interest_type}",
        f"- Confidence: {investor_response.confidence}",
        f"- Main Positive Reason: {investor_response.main_positive_reason}",
        f"- Main Concern: {investor_response.main_concern}",
        "",
        "## 3. Evidence Required Before Serious Interest",
        "",
        *[f"- {item}" for item in evidence_items],
        "",
        "## 4. Source Verification Gaps Relevant to This Investor",
        "",
        "| Category | Status | Available Evidence | Missing Evidence | Broker Action | Blocks Promotion |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    if relevant:
        for item in relevant:
            available = "; ".join(item.get("available_evidence", [])) or "None"
            missing = "; ".join(item.get("missing_evidence", [])) or "None"
            lines.append(
                f"| {item.get('category', 'unknown')} | "
                f"{item.get('status', 'missing')} | {available} | {missing} | "
                f"{item.get('broker_action', 'Collect missing evidence.')} | "
                f"{'Yes' if item.get('blocks_promotion') else 'No'} |"
            )
    else:
        lines.append(
            "| general | missing | None established | Investor-specific evidence | "
            "Collect and verify the required evidence. | Yes |"
        )

    lines.extend(
        [
            "",
            "## 5. Backoffice Collection Checklist",
            "",
            "| Evidence Item | Source Type Needed | Why This Investor Cares | Related Source Verification Category | Priority |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for evidence, source_type, why, category, priority in spec["checklist"]:
        lines.append(
            f"| {evidence} | {source_type} | {why} | {category} | {priority} |"
        )

    lines.extend(
        [
            "",
            "## 6. Promotion / Review Blocking Items",
            "",
        ]
    )
    if blocking:
        for item in blocking:
            lines.append(
                f"- {item['category']}: {item.get('limitation', 'Evidence remains incomplete')} "
                f"Next action: {item.get('broker_action', 'Collect missing evidence.')}"
            )
    else:
        lines.append(
            "- No matrix category in this memo is currently marked as a promotion blocker; "
            "the investor's stated evidence requirements still require review."
        )

    lines.extend(
        [
            "",
            "## 7. Broker Notes",
            "",
            (
                "Use this memo only to coordinate evidence collection and source "
                "validation. It does not change the investor's final decision, "
                "candidate decision, interest mapping, or promotion eligibility."
            ),
            "",
            "## 8. Safety Note",
            "",
            (
                "This memo is not a recommendation, ranking, vote, average score, "
                "consensus, allocation instruction, rebalancing instruction, or "
                "trade signal."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def save_investor_follow_up_memos(
    ticker: str,
    company_name: str,
    investor_responses: list[InvestorInterestResponse],
    source_verification_summary: dict,
    output_dir: Path,
) -> dict[str, Path]:
    """Save one follow-up memo per investor and return paths by display name."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for response in investor_responses:
        key = _investor_key(response.investor)
        path = output_dir / f"{ticker.lower()}_{key}_follow_up_memo.md"
        path.write_text(
            generate_investor_follow_up_memo(
                ticker,
                company_name,
                response,
                source_verification_summary,
            ),
            encoding="utf-8",
        )
        paths[response.investor] = path
    return paths
