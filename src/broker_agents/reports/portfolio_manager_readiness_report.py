"""Markdown rendering for Portfolio Manager Readiness items."""

from collections import defaultdict

from broker_agents.portfolio.portfolio_manager_readiness import PortfolioReadinessItem

RISK_ORDER = [
    "Big Tech concentration",
    "AI / technology theme concentration",
    "Index overlap concentration",
    "Valuation risk concentration",
    "Human review dependency concentration",
    "Evidence gap concentration",
]

RISK_DETAILS = {
    "Big Tech concentration": (
        "Multiple companies share mega-cap technology exposure.",
        "Review aggregate sector and company overlap before any later allocation work.",
    ),
    "AI / technology theme concentration": (
        "Cloud, AI, semiconductor, and ecosystem exposures may move together.",
        "Keep thematic concentration visible during human review.",
    ),
    "Index overlap concentration": (
        "Broad index funds already provide indirect exposure.",
        "Validate ETF/index holdings and indirect exposure before portfolio consideration.",
    ),
    "Valuation risk concentration": (
        "Multiple candidates retain valuation or margin-of-safety uncertainty.",
        "Require validated valuation methodology and human review.",
    ),
    "Human review dependency concentration": (
        "Every company depends on unresolved qualitative review items.",
        "Complete blocking review items before portfolio consideration.",
    ),
    "Evidence gap concentration": (
        "Several companies share missing benchmark, incentives, scuttlebutt, and normalization evidence.",
        "Prioritize shared evidence workflows before expanding the portfolio process.",
    ),
}


def _join(values: list[str]) -> str:
    """Render a list as compact Markdown text."""
    return "; ".join(values) if values else "None"


def generate_portfolio_manager_readiness_report(
    items: list[PortfolioReadinessItem],
) -> str:
    """Generate a governance-only portfolio readiness report."""
    lines = [
        "# Portfolio Manager Readiness Report",
        "",
        "## 1. Important Disclaimer",
        "",
        "This report is not a recommendation, ranking, vote, average score, consensus, allocation instruction, rebalancing instruction, or trade signal. It evaluates portfolio readiness and governance only.",
        "",
        "## 2. Portfolio Manager Role Boundary",
        "",
        "- This agent does not buy or sell.",
        "- This agent does not assign final weights.",
        "- This agent does not rebalance.",
        "- This agent does not override investor agents.",
        "- This agent does not close human review items.",
        "- This agent does not enable auto-promotion.",
        "",
        "## 3. Companies Reviewed",
        "",
        "| Ticker | Company | Portfolio Status | Readiness Label | Primary Blocker | Manual Trigger Required |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in items:
        lines.append(
            f"| {item.ticker} | {item.company_name} | {item.portfolio_status} | "
            f"{item.readiness_label} | {item.primary_blocker} | "
            f"{'Yes' if item.manual_trigger_required else 'No'} |"
        )

    lines.extend(
        [
            "",
            "## 4. Portfolio Readiness Assessment",
            "",
            "| Ticker | Source Quality | Human Review Status | Promotion Status | Candidate Summary | Final Decision Summary | Portfolio Status |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in items:
        lines.append(
            f"| {item.ticker} | {item.source_quality_summary} | "
            f"{item.human_review_status} | {item.promotion_status_summary} | "
            f"{item.investor_candidate_summary} | {item.final_decision_summary} | "
            f"{item.portfolio_status} |"
        )

    lines.extend(
        [
            "",
            "## 5. Portfolio Fit Notes",
            "",
            "| Ticker | Portfolio Fit Notes | Not Ready For Execution Reasons |",
            "| --- | --- | --- |",
        ]
    )
    for item in items:
        lines.append(
            f"| {item.ticker} | {item.portfolio_fit_notes} | "
            f"{_join(item.not_ready_for_execution_reasons)} |"
        )

    affected: dict[str, list[str]] = defaultdict(list)
    for item in items:
        for flag in item.cross_portfolio_risk_flags:
            if flag in RISK_ORDER:
                affected[flag].append(item.ticker)
    lines.extend(
        [
            "",
            "## 6. Cross-Portfolio Risk Summary",
            "",
            "| Risk Flag | Affected Tickers | Why It Matters | Governance Response |",
            "| --- | --- | --- | --- |",
        ]
    )
    for risk in RISK_ORDER:
        why, response = RISK_DETAILS[risk]
        lines.append(
            f"| {risk} | {', '.join(affected.get(risk, [])) or 'None'} | "
            f"{why} | {response} |"
        )

    lines.extend(
        [
            "",
            "## 7. Manual Trigger List",
            "",
            "| Ticker | Trigger Required | Trigger Reason | Suggested Manual Action |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in items:
        lines.append(
            f"| {item.ticker} | {'Yes' if item.manual_trigger_required else 'No'} | "
            f"{_join(item.manual_trigger_reason)} | "
            "Complete human review items; validate source methodology; add benchmark, "
            "incentives, scuttlebutt, or normalization evidence; then re-run the enriched pipeline. |"
        )

    lines.extend(
        [
            "",
            "## 8. Human Review Dependencies",
            "",
            "| Ticker | Open Review Dependency | Blocks Portfolio Consideration | Next Governance Step |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in items:
        lines.append(
            f"| {item.ticker} | {item.human_review_status} | "
            f"{'Yes' if 'open blocking' in item.human_review_status.lower() else 'No'} | "
            "Complete and document the blocking Human Review Queue items without changing final decisions automatically. |"
        )

    lines.extend(
        [
            "",
            "## 9. Not Ready For Execution",
            "",
            "- Buy/sell decisions",
            "- Position sizing",
            "- Final allocation",
            "- Rebalancing",
            "- Auto-promotion",
            "- Closing review items",
            "- Live trading",
            "",
            "## 10. Suggested Next System Step",
            "",
            "The next system task should either add a Human Review Status Updater or add benchmark/incentives/scuttlebutt evidence workflows. Portfolio execution should not be implemented yet.",
            "",
            "## 11. Safety Check",
            "",
            "- Final decisions unchanged.",
            "- Auto-promotion disabled.",
            "- No ranking.",
            "- No consensus.",
            "- No allocation recommendation.",
            "- No trade or execution signal.",
            "- Human review required before portfolio consideration.",
            "",
        ]
    )
    return "\n".join(lines)
