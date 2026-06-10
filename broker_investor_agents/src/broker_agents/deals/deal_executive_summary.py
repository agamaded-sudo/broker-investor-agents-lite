"""Deterministic broker deal executive summary construction."""

from dataclasses import asdict, dataclass

from broker_agents.deals.investor_interest_response import InvestorInterestResponse


@dataclass(frozen=True)
class BrokerDealExecutiveSummary:
    """Broker-facing grouping of independent investor responses."""

    ticker: str
    company_name: str
    backoffice_readiness_label: str
    source_verification_status: str
    total_investor_responses: int
    conditional_interest_investors: list[str]
    watchlist_interest_investors: list[str]
    needs_evidence_investors: list[str]
    low_interest_investors: list[str]
    index_preferred_investors: list[str]
    pass_investors: list[str]
    strongest_positive_themes: list[str]
    main_blockers: list[str]
    backoffice_next_actions: list[str]
    safety_flags: list[str]

    def to_dict(self) -> dict:
        """Serialize this executive summary to a plain dictionary."""
        return asdict(self)


def _readiness_label(
    source_verification_status: str,
    skipped_sources: list[str],
    warnings: list[str],
) -> str:
    """Classify whether the Backoffice file is ready for independent review."""
    status = source_verification_status.lower()
    critical_warnings = [
        warning
        for warning in warnings
        if any(term in warning.lower() for term in ("failed", "invalid", "missing input"))
    ]
    if "weak" in status or len(critical_warnings) >= 2:
        return "Backoffice File Needs Work"
    if skipped_sources or warnings:
        return "Investor Review Possible with Evidence Gaps"
    if "strong" in status or "mixed" in status:
        return "Ready for Investor Review"
    return "Investor Review Possible with Evidence Gaps"


def _investors_by(
    responses: list[InvestorInterestResponse],
    field: str,
    value: str,
) -> list[str]:
    """Return investors whose response field matches the requested value."""
    return [
        response.investor
        for response in responses
        if getattr(response, field) == value
    ]


def _positive_themes(
    responses: list[InvestorInterestResponse],
) -> list[str]:
    """Build transparent positive themes from investor response categories."""
    themes: list[str] = []
    by_investor = {response.investor: response for response in responses}
    buffett = by_investor.get("Buffett")
    if buffett and buffett.interest_level in {
        "Conditional Interest",
        "Watchlist Interest",
    }:
        themes.append("Owner earnings / quality business interest")
    munger = by_investor.get("Munger")
    if munger and munger.interest_level in {
        "Conditional Interest",
        "Watchlist Interest",
    }:
        themes.append("Quality and rationality interest")
    fisher = by_investor.get("Fisher")
    if fisher and fisher.interest_level in {
        "Watchlist Interest",
        "Needs More Evidence",
    }:
        themes.append("Long-term growth requires scuttlebutt validation")
    lynch = by_investor.get("Lynch")
    if lynch and lynch.interest_level in {
        "Conditional Interest",
        "Watchlist Interest",
    }:
        themes.append("Growth story / category interest")
    bogle = by_investor.get("Bogle")
    if bogle and (
        bogle.interest_level == "Low Interest"
        or bogle.interest_type == "Index Preferred"
    ):
        themes.append("Broad index exposure may already capture the company")
    return themes


def _main_blockers(
    responses: list[InvestorInterestResponse],
) -> list[str]:
    """Collect concise, deduplicated concerns and evidence requirements."""
    blockers: list[str] = []
    for response in responses:
        for value in (
            response.main_concern,
            response.required_evidence_before_serious_interest,
        ):
            cleaned = value.strip()
            if cleaned and cleaned not in blockers:
                blockers.append(cleaned)
    return blockers


def _next_actions(
    responses: list[InvestorInterestResponse],
) -> list[str]:
    """Build non-execution Backoffice next actions."""
    actions = [
        "Validate remaining source methodology.",
        "Collect missing evidence required by interested investors.",
        "Refresh enriched company file after evidence update.",
        "Re-run investor agents independently.",
        "Prepare investor-specific follow-up memos if needed.",
    ]
    by_investor = {response.investor: response for response in responses}
    fisher = by_investor.get("Fisher")
    if fisher and fisher.interest_level == "Needs More Evidence":
        actions.append("Collect Fisher-style scuttlebutt evidence.")
    if by_investor.get("Munger"):
        actions.append(
            "Validate management incentives, ownership, and capital allocation evidence."
        )
    if by_investor.get("Buffett"):
        actions.append(
            "Validate normalized owner earnings and maintenance vs growth capex."
        )
    bogle = by_investor.get("Bogle")
    if bogle and bogle.interest_type == "Index Preferred":
        actions.append(
            "Validate index overlap and benchmark-relative risk before any "
            "individual-position discussion."
        )
    return list(dict.fromkeys(actions))


def build_broker_deal_executive_summary(
    ticker: str,
    company_name: str,
    investor_responses: list[InvestorInterestResponse],
    source_verification_status: str,
    applied_enrichment_sources: list[str],
    skipped_enrichment_sources: list[str],
    warnings: list[str],
) -> BrokerDealExecutiveSummary:
    """Build a broker-facing executive summary without combining decisions."""
    _ = applied_enrichment_sources
    return BrokerDealExecutiveSummary(
        ticker=ticker.upper(),
        company_name=company_name,
        backoffice_readiness_label=_readiness_label(
            source_verification_status,
            skipped_enrichment_sources,
            warnings,
        ),
        source_verification_status=source_verification_status,
        total_investor_responses=len(investor_responses),
        conditional_interest_investors=_investors_by(
            investor_responses,
            "interest_level",
            "Conditional Interest",
        ),
        watchlist_interest_investors=_investors_by(
            investor_responses,
            "interest_level",
            "Watchlist Interest",
        ),
        needs_evidence_investors=_investors_by(
            investor_responses,
            "interest_level",
            "Needs More Evidence",
        ),
        low_interest_investors=_investors_by(
            investor_responses,
            "interest_level",
            "Low Interest",
        ),
        index_preferred_investors=_investors_by(
            investor_responses,
            "interest_type",
            "Index Preferred",
        ),
        pass_investors=_investors_by(
            investor_responses,
            "interest_type",
            "Pass",
        ),
        strongest_positive_themes=_positive_themes(investor_responses),
        main_blockers=_main_blockers(investor_responses),
        backoffice_next_actions=_next_actions(investor_responses),
        safety_flags=[
            "no_recommendation",
            "no_ranking",
            "no_consensus",
            "no_allocation",
            "no_trade_signal",
            "final_decisions_unchanged",
            "auto_promotion_disabled",
        ],
    )
