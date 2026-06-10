"""Markdown rendering for the Human Review Queue."""

from collections import Counter

from broker_agents.review.human_review_queue import HumanReviewItem

INVESTOR_ORDER = ["Buffett", "Munger", "Fisher", "Lynch", "Bogle"]


def _count(items: list[HumanReviewItem], field: str, value: str) -> int:
    """Count review items by field value."""
    return sum(getattr(item, field) == value for item in items)


def _join(values: list[str]) -> str:
    """Render a list in a compact Markdown-friendly form."""
    return "; ".join(values) if values else "None"


def generate_human_review_queue_report(items: list[HumanReviewItem]) -> str:
    """Render a deterministic Human Review Queue report."""
    priority_counts = Counter(item.priority for item in items)
    lines = [
        "# Human Review Queue",
        "",
        "## 1. Important Disclaimer",
        "",
        "This queue is not a recommendation, ranking, vote, average score, consensus, allocation instruction, or trade signal. It only identifies questions requiring human judgment.",
        "",
        "## 2. Queue Summary",
        "",
        "| Total Items | Open | In Review | Reviewed | Deferred | Closed | High Priority | Medium Priority | Low Priority |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        (
            f"| {len(items)} | {_count(items, 'status', 'Open')} | "
            f"{_count(items, 'status', 'In Review')} | "
            f"{_count(items, 'status', 'Reviewed')} | "
            f"{_count(items, 'status', 'Deferred')} | "
            f"{_count(items, 'status', 'Closed')} | "
            f"{priority_counts['High']} | {priority_counts['Medium']} | "
            f"{priority_counts['Low']} |"
        ),
        "",
        "## 3. Review Items",
        "",
        "| Review ID | Priority | Ticker | Investor | Category | Review Question | Blocks Promotion | Status |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in items:
        lines.append(
            f"| {item.review_id} | {item.priority} | {item.ticker} | {item.investor} | "
            f"{item.review_category} | {item.review_question} | "
            f"{'Yes' if item.blocks_promotion else 'No'} | {item.status} |"
        )

    lines.extend(["", "## 4. Review Details by Investor", ""])
    for investor in INVESTOR_ORDER:
        investor_items = [item for item in items if item.investor == investor]
        lines.extend([f"### {investor}", ""])
        if not investor_items:
            lines.append("- No review items.")
            lines.append("")
            continue
        for item in investor_items:
            lines.extend(
                [
                    f"- Review ID: {item.review_id}",
                    f"  - Ticker: {item.ticker}",
                    f"  - Review Question: {item.review_question}",
                    f"  - Why Human Review Is Needed: {item.why_human_review_is_needed}",
                    f"  - Required Evidence: {_join(item.required_evidence)}",
                    f"  - Related Gap: {_join(item.related_gap)}",
                    f"  - Candidate Decision: {item.candidate_decision}",
                    f"  - Final Decision: {item.final_decision}",
                    f"  - Status: {item.status}",
                    f"  - Reviewer Notes: {item.reviewer_notes or 'None'}",
                ]
            )
        lines.append("")

    lines.extend(
        [
            "## 5. Promotion Safety Gate",
            "",
            "- No item can promote a candidate automatically.",
            "- Human review does not change final decisions by itself.",
            "- Promotion remains disabled until explicitly implemented in a later governed task.",
            "- Any reviewed item must still pass source verification and promotion eligibility.",
            "",
            "## 6. Suggested Review Order",
            "",
            "1. Fisher scuttlebutt review",
            "2. Munger incentives review",
            "3. Buffett owner earnings review",
            "4. Lynch growth story review",
            "5. Bogle portfolio fit review",
            "",
            "Fisher and Munger are most qualitative. Buffett needs judgment on durability and normalization. Lynch needs story/category clarity. Bogle depends on portfolio/user-specific fit.",
            "",
            "## 7. Safety Check",
            "",
            "- Final decisions unchanged.",
            "- Auto-promotion disabled.",
            "- No ranking.",
            "- No consensus.",
            "- No allocation recommendation.",
            "- No trade or execution signal.",
            "- Human review is required but not sufficient for promotion.",
            "",
        ]
    )
    return "\n".join(lines)
