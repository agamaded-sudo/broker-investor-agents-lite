"""Broker-facing interpretation of independent investor-agent responses."""

from dataclasses import asdict, dataclass

from broker_agents.deals.company_response_language import (
    build_polished_response_language,
    clean_mismatched_investor_language,
)

INTEREST_LEVELS = {
    "High Interest",
    "Conditional Interest",
    "Watchlist Interest",
    "Low Interest",
    "Not Interested",
    "Needs More Evidence",
}
INTEREST_TYPES = {
    "Buy Interest",
    "Buy Gradually Interest",
    "Watchlist",
    "Research Only",
    "Pass",
    "Index Preferred",
    "Needs Evidence",
}


@dataclass(frozen=True)
class InvestorInterestResponse:
    """One independent investor response translated for broker review."""

    ticker: str
    investor: str
    final_decision: str
    candidate_decision: str
    interest_level: str
    interest_type: str
    confidence: str
    main_positive_reason: str
    main_concern: str
    required_evidence_before_serious_interest: str
    response_label: str
    safety_note: str
    broker_facing_final_decision: str
    broker_follow_up_items: list[str]

    def to_dict(self) -> dict:
        """Serialize the response to a plain dictionary."""
        return asdict(self)


def _extract_heading_value(text: str, heading: str) -> str | None:
    """Extract the first non-empty value after a Markdown heading."""
    lines = text.splitlines()
    target = f"## {heading}"
    for index, line in enumerate(lines):
        if line.strip() != target:
            continue
        for following in lines[index + 1 :]:
            value = following.strip()
            if value:
                return value
    return None


def _extract_inline(text: str, field: str) -> str | None:
    """Extract a dash-prefixed or plain inline field."""
    prefix = f"{field}:"
    for line in text.splitlines():
        stripped = line.strip().lstrip("-").strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip() or None
    return None


def _first_nested_bullet(text: str, field: str) -> str | None:
    """Extract the first nested bullet after an inline list label."""
    lines = text.splitlines()
    marker = f"- {field}:"
    for index, line in enumerate(lines):
        if line.strip() != marker:
            continue
        for following in lines[index + 1 :]:
            stripped = following.strip()
            if stripped.startswith("- "):
                return stripped[2:].strip() or None
            if stripped.startswith("## ") or (
                stripped.startswith("- ") and not following.startswith("  ")
            ):
                break
    return None


def _interest_mapping(final_decision: str, candidate_decision: str) -> tuple[str, str]:
    """Map deterministic decisions to broker-facing interest language."""
    combined = f"{candidate_decision} {final_decision}".lower()
    if "buy gradually" in combined:
        return "Conditional Interest", "Buy Gradually Interest"
    if "buy" in combined:
        return "High Interest", "Buy Interest"
    if "prefer broad index" in combined:
        return "Low Interest", "Index Preferred"
    if "needs more evidence" in combined or "needs more" in combined:
        return "Needs More Evidence", "Needs Evidence"
    if "watch" in combined or "follow" in combined:
        return "Watchlist Interest", "Watchlist"
    if "wait" in combined:
        return "Watchlist Interest", "Research Only"
    if "avoid" in combined or "reject" in combined:
        return "Not Interested", "Pass"
    return "Needs More Evidence", "Research Only"


def derive_investor_interest_response(
    ticker: str,
    investor: str,
    final_decision: str,
    candidate_decision: str,
    report_text: str | None = None,
    pack: dict | None = None,
) -> InvestorInterestResponse:
    """Derive a transparent broker-facing response from one investor report."""
    text = report_text or ""
    interest_level, interest_type = _interest_mapping(
        final_decision,
        candidate_decision,
    )
    confidence = (
        _extract_heading_value(text, "Confidence Level")
        or _extract_inline(text, "Candidate Confidence")
        or "Not established"
    )
    positive = (
        _first_nested_bullet(text, "Positive Drivers")
        or _extract_heading_value(text, "Key Supporting Evidence")
        or "No positive reason extracted from the current report."
    )
    concern = (
        _first_nested_bullet(text, "Negative Drivers")
        or _first_nested_bullet(text, "Decision Blockers")
        or _extract_heading_value(text, "Key Objections")
        or "No main concern extracted from the current report."
    )
    required = (
        _first_nested_bullet(text, "Required Evidence")
        or _first_nested_bullet(text, "Decision Blockers")
        or "Additional verified evidence is required before stronger interest."
    )
    broker_facing_final_decision = final_decision
    follow_up_items = [required]
    if pack is not None:
        polished = build_polished_response_language(pack, investor)
        positive = polished["main_positive_reason"]
        concern = polished["main_concern"]
        required = polished["required_evidence_before_serious_interest"]
        follow_up_items = polished["broker_follow_up_items"]
        broker_facing_final_decision = clean_mismatched_investor_language(
            final_decision,
            pack,
        )
    response = InvestorInterestResponse(
        ticker=ticker.upper(),
        investor=investor,
        final_decision=final_decision,
        candidate_decision=candidate_decision,
        interest_level=interest_level,
        interest_type=interest_type,
        confidence=confidence,
        main_positive_reason=positive,
        main_concern=concern,
        required_evidence_before_serious_interest=required,
        response_label=f"{investor}: {interest_level} / {interest_type}",
        safety_note=(
            "Broker-facing interpretation only; not a recommendation, vote, "
            "consensus, allocation instruction, or trade signal."
        ),
        broker_facing_final_decision=broker_facing_final_decision,
        broker_follow_up_items=follow_up_items,
    )
    if response.interest_level not in INTEREST_LEVELS:
        raise ValueError(f"Unsupported interest level: {response.interest_level}")
    if response.interest_type not in INTEREST_TYPES:
        raise ValueError(f"Unsupported interest type: {response.interest_type}")
    return response
