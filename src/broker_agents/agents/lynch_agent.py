"""Deterministic Lynch-style investor agent."""

from pathlib import Path

from broker_agents.agents.base_investor_agent import BaseInvestorAgent
from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.calculators.decision_candidates import (
    build_decision_candidate,
    render_decision_candidate_section,
)
from broker_agents.calculators.lynch_category_scoring import score_lynch_category
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
    render_promotion_eligibility_section,
)
from broker_agents.reports.formatting import format_multiple, format_ratio_as_percent

LYNCH_STORY_CHECKS = {
    "software_cloud": "Cloud/software growth story: retention, recurring revenue, EPS/FCF growth, and valuation versus growth.",
    "consumer_ecosystem": "Ecosystem and services monetization story: product cycle, installed base, growth durability, and PEG.",
    "semiconductor": "Semiconductor cycle and AI/data-center demand story: inventory, capacity, and valuation versus cycle.",
    "retail": "Retail story: same-store sales, store growth, margins, and inventory discipline.",
    "payments_network": "Payments story: payment volume, take rate, network effects, and cross-border growth.",
    "industrial": "Industrial story: backlog, utilization, cycle position, margins, and orders.",
    "financial": "Financial story: credit cycle, book value, earnings quality, and funding costs.",
    "generic": "Clarify the investment story and test it against earnings and cash flow.",
}


class LynchAgent(BaseInvestorAgent):
    """Generate a simple Peter Lynch-style report from a backoffice pack."""

    def __init__(self, pack: dict, method_path: Path) -> None:
        super().__init__(pack=pack, method_path=method_path)

    def _annual(self) -> dict:
        return self.get_section("financial_statements_summary", {}).get("annual", {})

    def _quarterly(self) -> dict:
        return self.get_section("financial_statements_summary", {}).get("quarterly", {})

    def _story_evidence(self, signals: dict) -> str:
        annual = self._annual()
        quarterly = self._quarterly()
        core_financials = [annual.get("revenue"), annual.get("operating_income")]
        if all(value is not None for value in core_financials):
            quarterly_status = " Quarterly evidence is also present." if quarterly else ""
            return (
                f"Partially confirmed: financial evidence supports {signals['primary_growth_engine'].lower()}."
                f"{quarterly_status}"
            )
        return "Incomplete: one or more core story evidence fields are missing."

    def _earnings_growth_quality(self, signals: dict) -> str:
        annual = self._annual()
        quarterly = self._quarterly()
        if annual.get("operating_income") is not None and quarterly.get("operating_income") is not None:
            return (
                "Strong / with capex watch: earnings and operating income data are present, "
                f"while {signals['major_capex_issue'].lower()} still needs trend analysis."
            )
        return "Not established: earnings and operating income trend data are incomplete."

    def _valuation_vs_growth(self) -> str:
        growth_peg = self.get_section("growth_peg_analysis", {})
        if growth_peg.get("peg_ratio") is not None:
            return (
                "Preliminary: PEG and growth data are available, but provider, "
                "methodology, and growth durability still require validation."
            )
        historical = self.get_section("historical_valuation", {})
        valuation = self.get_section("valuation_snapshot", {})
        if historical.get("current_snapshot_only") or not valuation.get("peg_ratio"):
            return "Reasonable to demanding / not fully established: historical valuation and PEG are incomplete."
        return "Preliminary: valuation and PEG data are available but need comparison against growth durability."

    def _balance_sheet_check(self) -> str:
        annual = self._annual()
        if (
            annual.get("cash_and_short_term_investments") is not None
            and annual.get("long_term_debt") is not None
        ):
            return "Strong: cash and short-term investments and long-term debt are present in the pack."
        return "Not established: cash or long-term debt data is missing."

    def _market_awareness(self) -> str:
        market_awareness = self.get_section("market_awareness", {})
        missing = market_awareness.get("missing_items", [])
        if missing:
            return f"{self.get_company_name()} may be well known, but coverage data needs confirmation because market awareness fields are incomplete."
        return "Market awareness appears documented in the current pack."

    def _missing_backoffice_data(self, category_scoring: dict) -> list[str]:
        return list(
            dict.fromkeys(
                category_scoring["evidence_gaps"]
                + [
                    "Historical P/E range.",
                    "Analyst coverage count.",
                    "Institutional ownership.",
                    "Peer growth and valuation comparison.",
                    "Capex and FCF trend over 5-10 years.",
                ]
            )
        )

    def _follow_up_indicators(self, signals: dict, category_scoring: dict) -> list[str]:
        return list(
            dict.fromkeys(
                [
            f"Primary growth engine: {signals['primary_growth_engine']}.",
            f"Business-model story check: {LYNCH_STORY_CHECKS[signals['business_model_type']]}",
                ]
                + category_scoring["follow_up_indicators"]
                + ["Operating margin trend", "Capex as percentage of OCF", "Share count trend"]
            )
        )

    def generate_report(self) -> str:
        """Generate a deterministic Lynch-style Markdown report."""
        annual = self._annual()
        quarterly = self._quarterly()
        metrics = self.get_section("calculated_financial_metrics", {})
        risks = self.get_section("risk_register", {}).get("risks", [])
        risk_names = [str(risk.get("name")) for risk in risks if isinstance(risk, dict)]
        company_signals = extract_company_signals(self.pack)
        category_scoring = score_lynch_category(self.pack)
        growth_peg = category_scoring["growth_peg_evidence"]
        decision_candidate = build_decision_candidate(self.pack, "lynch")
        promotion_eligibility = evaluate_promotion_eligibility(self.pack, "lynch")

        lines = [
            self.build_common_header(),
            "## Investor Identity",
            "Peter Lynch-style analysis focused on a simple story, company category, earnings growth, balance sheet, and price versus growth.",
            "",
            "## Company Under Review",
            f"{self.get_company_name()} ({self.get_ticker()})",
            "",
            "## Data Quality Rating",
            "Medium",
            "Core financial data is available, but valuation history, maintenance capex split, scuttlebutt, and/or portfolio context remain incomplete depending on the investor method.",
            "",
            "## Company-Specific Signal",
            f"- Business Model Type: {company_signals['business_model_type']}",
            f"- Primary Growth Engine: {company_signals['primary_growth_engine']}",
            f"- Dominant Revenue Stream: {company_signals['dominant_revenue_stream']}",
            f"- Lynch Angle: {company_signals['investor_specific_angles']['lynch']}",
            "",
            "## Core Question",
            "Is there a simple, testable growth story supported by earnings, balance sheet strength, and valuation discipline?",
            "",
            "## Investment Story",
            LYNCH_STORY_CHECKS[company_signals["business_model_type"]],
            "",
            "## Company Category",
            category_scoring["primary_category"],
            "",
            "## Company Category Confidence",
            category_scoring["category_confidence"],
            "",
            "## Lynch Category Scoring",
            f"- Business Model Type: {category_scoring['business_model_type']}",
            f"- Primary Category: {category_scoring['primary_category']}",
            f"- Secondary Category: {category_scoring['secondary_category']}",
            f"- Category Confidence: {category_scoring['category_confidence']}",
            "",
            "| Category | Score (0-5) |",
            "| --- | --- |",
            *[
                f"| {category} | {score} |"
                for category, score in category_scoring["category_scores"].items()
            ],
            "",
            f"- Story Score: {category_scoring['story_score']}/5",
            f"- Growth Score: {category_scoring['growth_score']}/5",
            f"- Valuation vs Growth Score: {category_scoring['valuation_vs_growth_score']}/5",
            f"- Balance Sheet Score: {category_scoring['balance_sheet_score']}/5",
            f"- Cyclicality Score: {category_scoring['cyclicality_score']}/5",
            "- Evidence Gaps:",
            *[f"  - {item}" for item in category_scoring["evidence_gaps"]],
            f"- Lynch Interpretation: {category_scoring['lynch_interpretation']}",
            "- Follow-up Indicators:",
            *[f"  - {item}" for item in category_scoring["follow_up_indicators"]],
            "",
            "## Growth & PEG Evidence",
            f"- Revenue CAGR 3Y: {format_ratio_as_percent(growth_peg['revenue_cagr_3y'])}",
            f"- Revenue CAGR 5Y: {format_ratio_as_percent(growth_peg['revenue_cagr_5y'])}",
            f"- EPS CAGR 3Y: {format_ratio_as_percent(growth_peg['eps_cagr_3y'])}",
            f"- EPS CAGR 5Y: {format_ratio_as_percent(growth_peg['eps_cagr_5y'])}",
            f"- FCF CAGR 3Y: {format_ratio_as_percent(growth_peg['fcf_cagr_3y'])}",
            f"- FCF CAGR 5Y: {format_ratio_as_percent(growth_peg['fcf_cagr_5y'])}",
            f"- Forward EPS Growth: {format_ratio_as_percent(growth_peg['forward_eps_growth'])}",
            f"- PEG Ratio: {format_multiple(growth_peg['peg_ratio'])}",
            f"- Growth Quality Label: {growth_peg['growth_quality_label']}",
            f"- Confidence: {growth_peg['growth_data_confidence']}",
            "- Evidence Gaps:",
            *[f"  - {item}" for item in growth_peg["evidence_gaps"]],
            "",
            "## Story Evidence",
            self._story_evidence(company_signals),
            f"- Latest annual revenue: {annual.get('revenue', 'not provided')}",
            f"- Latest annual operating income: {annual.get('operating_income', 'not provided')}",
            f"- Latest quarterly revenue: {quarterly.get('revenue', 'not provided')}",
            "",
            "## Earnings Growth Quality",
            self._earnings_growth_quality(company_signals),
            f"- Latest annual net income: {annual.get('net_income', 'not provided')}",
            f"- Latest quarterly net income: {quarterly.get('net_income', 'not provided')}",
            f"- Operating margin: {metrics.get('operating_margin', 'not provided')}",
            "",
            "## Valuation vs Growth",
            self._valuation_vs_growth(),
            "",
            "## Balance Sheet Check",
            self._balance_sheet_check(),
            f"- Cash and short-term investments: {annual.get('cash_and_short_term_investments', 'not provided')}",
            f"- Long-term debt: {annual.get('long_term_debt', 'not provided')}",
            "",
            "## Market Awareness",
            self._market_awareness(),
            "",
            "## Follow-up Indicators",
            *[
                f"- {item}"
                for item in self._follow_up_indicators(
                    company_signals,
                    category_scoring,
                )
            ],
            "",
            "## Completed Investor Analysis",
            "- Simple investment story defined.",
            "- Company category assigned.",
            "- Initial story evidence check completed.",
            "- Initial balance sheet check completed.",
            "",
            "## Missing Backoffice Data",
            *[
                f"- {item}"
                for item in self._missing_backoffice_data(category_scoring)
            ],
            *[f"- Detected gap: {item}" for item in company_signals["major_data_gaps"]],
            "",
            "## Pending Investor Analysis",
            "- Precise PEG assessment.",
            "- Stronger valuation vs growth judgment.",
            "- Sustainability of EPS growth.",
            "- Whether the stock is fully priced relative to expectations.",
            f"- Whether {self.get_company_name()} can still be a multi-bagger from its current size or mainly a compounder.",
            "",
            "## Evidence Map",
            "- Investment story evidence: financial_statements_summary",
            "- Business-model KPIs: sector_specific_operating_kpis",
            "- Valuation and PEG evidence: historical_valuation / valuation_snapshot / growth_peg_analysis",
            "- Market awareness gap: market_awareness",
            "- Balance sheet check: financial_statements_summary",
            "",
            "## Key Supporting Evidence",
            f"- Revenue: {annual.get('revenue', 'not provided')}",
            f"- Operating income: {annual.get('operating_income', 'not provided')}",
            f"- Latest quarterly revenue: {quarterly.get('revenue', 'not provided')}",
            f"- Primary growth engine: {company_signals['primary_growth_engine']}",
            "",
            "## Key Objections",
            *[f"- {name}" for name in risk_names],
            "- Growth and PEG provider methodology still requires validation.",
            f"- {company_signals['major_capex_issue']} may pressure free cash flow if returns disappoint.",
            "- Current market expectations may already reflect much of the story.",
            "",
            "## Decision Rationale",
            company_signals["decision_rationales"]["lynch"],
            "",
            *render_decision_candidate_section(decision_candidate),
            *render_promotion_eligibility_section(promotion_eligibility),
            "## Decision",
            "Follow / Watch",
            "",
            "## Confidence Level",
            "Medium",
            "",
            "## Final Lynch Statement",
            f"{self.get_company_name()} has a testable Lynch-style story around {company_signals['primary_growth_engine'].lower()}, but the report remains a follow/watch case until PEG, historical valuation, earnings durability, and capex trends are better established.",
            "",
        ]

        return "\n".join(lines)
