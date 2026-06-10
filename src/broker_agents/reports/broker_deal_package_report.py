"""Broker deal package Markdown generation."""

from pathlib import Path

from broker_agents.deals.deal_executive_summary import BrokerDealExecutiveSummary
from broker_agents.deals.investor_interest_response import InvestorInterestResponse

INVESTOR_ORDER = ["Buffett", "Munger", "Fisher", "Lynch", "Bogle"]


def _join(values: list[str]) -> str:
    """Render a compact comma-separated value list."""
    return ", ".join(values) if values else "None"


def generate_broker_deal_package_report(
    ticker: str,
    company_name: str,
    enriched_pack_path: Path,
    investor_responses: list[InvestorInterestResponse],
    source_verification_status: str,
    applied_enrichment_sources: list[str],
    skipped_enrichment_sources: list[str],
    warnings: list[str],
    executive_summary: BrokerDealExecutiveSummary,
    investor_response_letter_paths: dict[str, Path] | None = None,
) -> str:
    """Generate a broker-facing package of independent investor responses."""
    lines = [
        f"# Broker Deal Package - {ticker.upper()}",
        "",
        "## 1. Important Disclaimer",
        "",
        "This package is not a recommendation, ranking, vote, average score, consensus, allocation instruction, rebalancing instruction, or trade signal. It summarizes independent investor-agent responses for broker review only.",
        "",
        "## 2. Executive Summary for Broker",
        "",
        f"- Backoffice Readiness Label: {executive_summary.backoffice_readiness_label}",
        f"- Source Verification Status: {executive_summary.source_verification_status}",
        f"- Total Investor Responses: {executive_summary.total_investor_responses}",
        (
            "- Conditional Interest Investors: "
            f"{_join(executive_summary.conditional_interest_investors)}"
        ),
        (
            "- Watchlist Interest Investors: "
            f"{_join(executive_summary.watchlist_interest_investors)}"
        ),
        (
            "- Needs Evidence Investors: "
            f"{_join(executive_summary.needs_evidence_investors)}"
        ),
        f"- Low Interest Investors: {_join(executive_summary.low_interest_investors)}",
        (
            "- Index Preferred Investors: "
            f"{_join(executive_summary.index_preferred_investors)}"
        ),
        f"- Pass Investors: {_join(executive_summary.pass_investors)}",
        "",
        "### Key Positive Themes",
        "",
        *[
            f"- {theme}"
            for theme in executive_summary.strongest_positive_themes
        ],
        "",
        "### Main Blockers",
        "",
        *[f"- {blocker}" for blocker in executive_summary.main_blockers],
        "",
        "### Backoffice Next Actions",
        "",
        *[
            f"- {action}"
            for action in executive_summary.backoffice_next_actions
        ],
        "",
        "## 3. Deal Context",
        "",
        "| Ticker | Company | Enriched Pack | Source Verification Status |",
        "| --- | --- | --- | --- |",
        f"| {ticker.upper()} | {company_name} | {enriched_pack_path} | {source_verification_status} |",
        "",
        "## 4. Backoffice Preparation Summary",
        "",
        f"- Enriched pack path: {enriched_pack_path}",
        f"- Applied enrichment sources: {_join(applied_enrichment_sources)}",
        f"- Skipped enrichment sources: {_join(skipped_enrichment_sources)}",
        f"- Source verification status: {source_verification_status}",
        f"- Warnings: {_join(warnings)}",
        "",
        "## 5. Independent Investor Responses",
        "",
        "| Investor | Final Decision | Candidate Decision | Interest Level | Interest Type | Confidence | Main Concern |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for response in investor_responses:
        lines.append(
            f"| {response.investor} | {response.broker_facing_final_decision} | "
            f"{response.candidate_decision} | {response.interest_level} | "
            f"{response.interest_type} | {response.confidence} | "
            f"{response.main_concern} |"
        )

    letter_paths = investor_response_letter_paths or {}
    lines.extend(
        [
            "",
            "## 6. Investor Response Letters",
            "",
            "| Investor | Response Letter Path | Interest Level | Interest Type |",
            "| --- | --- | --- | --- |",
        ]
    )
    for response in investor_responses:
        letter_path = letter_paths.get(response.investor, Path("Not available"))
        lines.append(
            f"| {response.investor} | {letter_path} | "
            f"{response.interest_level} | {response.interest_type} |"
        )
    lines.extend(
        [
            "",
            (
                "Each response letter is independent. The broker should not treat "
                "these letters as a vote, ranking, or consensus."
            ),
            "",
            "## 7. Investor Response Details",
            "",
        ]
    )
    for investor in INVESTOR_ORDER:
        response = next(
            (item for item in investor_responses if item.investor == investor),
            None,
        )
        lines.extend([f"### {investor}", ""])
        if response is None:
            lines.extend(["- Response unavailable.", ""])
            continue
        lines.extend(
            [
                f"- Response Label: {response.response_label}",
                f"- Interest Level: {response.interest_level}",
                f"- Interest Type: {response.interest_type}",
                (
                    "- Final Decision: "
                    f"{response.broker_facing_final_decision}"
                ),
                f"- Main Positive Reason: {response.main_positive_reason}",
                f"- Main Concern: {response.main_concern}",
                (
                    "- Required Evidence Before Serious Interest: "
                    f"{response.required_evidence_before_serious_interest}"
                ),
                (
                    "- Company-Specific Follow-Up: "
                    f"{'; '.join(response.broker_follow_up_items)}"
                ),
                f"- Safety Note: {response.safety_note}",
                "",
            ]
        )

    conditional = [
        item.investor
        for item in investor_responses
        if item.interest_level == "Conditional Interest"
    ]
    watchlist = [
        item.investor
        for item in investor_responses
        if item.interest_level == "Watchlist Interest"
    ]
    needs_evidence = [
        item.investor
        for item in investor_responses
        if item.interest_level == "Needs More Evidence"
    ]
    index_preferred = [
        item.investor
        for item in investor_responses
        if item.interest_type == "Index Preferred"
    ]
    lines.extend(
        [
            "## 8. Broker Interpretation",
            "",
            f"- Conditional interest: {_join(conditional)}.",
            f"- Watchlist or research interest: {_join(watchlist)}.",
            f"- Needs more evidence: {_join(needs_evidence)}.",
            f"- Prefers index exposure: {_join(index_preferred)}.",
            (
                "- Stronger interest remains blocked by investor-specific valuation, "
                "owner earnings, incentives, scuttlebutt, growth methodology, or "
                "benchmark evidence."
            ),
            "- These independent responses are not averaged, ranked, or combined.",
            "",
            "## 9. Next Backoffice Actions",
            "",
            "- Collect missing investor-specific evidence.",
            "- Validate source provenance and methodology.",
            "- Refresh the enriched company pack.",
            "- Rerun the five investor agents independently.",
            "- Prepare investor-specific follow-up memos.",
            "",
            "## 10. Safety Check",
            "",
            "- No recommendation.",
            "- No ranking.",
            "- No consensus.",
            "- No portfolio allocation.",
            "- No trade signal.",
            "- Final investor decisions unchanged.",
            "- Auto-promotion disabled.",
            "",
        ]
    )
    return "\n".join(lines)
