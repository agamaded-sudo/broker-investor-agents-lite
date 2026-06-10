"""Broker-facing investor response letter generation."""

from pathlib import Path

from broker_agents.deals.investor_interest_response import InvestorInterestResponse

FINAL_RESPONSE_BY_TYPE = {
    "Buy Gradually Interest": (
        "I am conditionally interested, but only through a gradual and "
        "evidence-gated approach."
    ),
    "Buy Interest": (
        "I am interested in reviewing this company further as a potential purchase "
        "candidate, subject to evidence quality and valuation discipline."
    ),
    "Watchlist": "I am not ready to buy, but I would keep this company under observation.",
    "Research Only": (
        "I am not prepared to express purchase interest yet. Further research is required."
    ),
    "Index Preferred": (
        "I would prefer broad index exposure rather than a separate individual "
        "position at this stage."
    ),
    "Needs Evidence": (
        "I cannot express serious interest until the missing evidence is provided."
    ),
    "Pass": "I am not interested based on the current company file.",
}

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


def generate_investor_response_letter(
    ticker: str,
    company_name: str,
    investor_response: InvestorInterestResponse,
) -> str:
    """Generate one deterministic broker-facing investor response letter."""
    final_response = FINAL_RESPONSE_BY_TYPE.get(
        investor_response.interest_type,
        "No final interest response can be made until the file is improved.",
    )
    return "\n".join(
        [
            (
                f"# Investor Response Letter - {investor_response.investor} - "
                f"{ticker.upper()}"
            ),
            "",
            "Dear Broker,",
            "",
            (
                f"After reviewing the Backoffice company file for {company_name} "
                f"({ticker.upper()}), my response is as follows:"
            ),
            "",
            "## 1. Interest Response",
            "",
            "| Investor | Interest Level | Interest Type | Response Label | Confidence |",
            "| --- | --- | --- | --- | --- |",
            (
                f"| {investor_response.investor} | "
                f"{investor_response.interest_level} | "
                f"{investor_response.interest_type} | "
                f"{investor_response.response_label} | "
                f"{investor_response.confidence} |"
            ),
            "",
            "## 2. Independent View",
            "",
            (
                "- Final Decision: "
                f"{investor_response.broker_facing_final_decision}"
            ),
            f"- Candidate Decision: {investor_response.candidate_decision}",
            f"- Main Positive Reason: {investor_response.main_positive_reason}",
            f"- Main Concern: {investor_response.main_concern}",
            (
                "- Required Evidence Before Serious Interest: "
                f"{investor_response.required_evidence_before_serious_interest}"
            ),
            "",
            "## 3. Broker Follow-Up Required",
            "",
            *[
                f"- {item.rstrip('.')}."
                for item in investor_response.broker_follow_up_items
            ],
            "- Validate the relevant source provenance and methodology.",
            "- Refresh the enriched company file before requesting a stronger response.",
            "",
            "## 4. Boundary Statement",
            "",
            (
                "This is an independent investor-agent research response for broker "
                "follow-up only. It cannot be combined with other responses or used "
                "as a portfolio or transaction instruction."
            ),
            "",
            "## 5. Final Response",
            "",
            final_response,
            "",
        ]
    )


def save_investor_response_letters(
    ticker: str,
    company_name: str,
    investor_responses: list[InvestorInterestResponse],
    output_dir: Path,
) -> list[Path]:
    """Save one response letter per investor and return their paths."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ticker_lower = ticker.lower()
    paths: list[Path] = []
    for response in investor_responses:
        investor_key = INVESTOR_KEYS.get(response.investor.lower())
        if investor_key is None:
            investor_key = response.investor.lower().replace(" ", "_")
        path = output_dir / f"{ticker_lower}_{investor_key}_response_letter.md"
        path.write_text(
            generate_investor_response_letter(ticker, company_name, response),
            encoding="utf-8",
        )
        paths.append(path)
    return paths
