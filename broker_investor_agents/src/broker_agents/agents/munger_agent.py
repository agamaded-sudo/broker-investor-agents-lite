"""Deterministic Munger-style investor agent."""

from pathlib import Path

from broker_agents.agents.base_investor_agent import BaseInvestorAgent
from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.calculators.decision_candidates import (
    build_decision_candidate,
    render_decision_candidate_section,
)
from broker_agents.calculators.munger_inversion import build_munger_inversion_matrix
from broker_agents.calculators.munger_incentives import (
    score_munger_incentives_and_stupidity,
)
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
    render_promotion_eligibility_section,
)


class MungerAgent(BaseInvestorAgent):
    """Generate a simple Charlie Munger-style report from a backoffice pack."""

    def __init__(self, pack: dict, method_path: Path) -> None:
        super().__init__(pack=pack, method_path=method_path)

    def _business_summary(self) -> str:
        business_model = self.get_section("business_model", {})
        return str(
            business_model.get("business_summary")
            or business_model.get("summary")
            or "No business model summary provided."
        )

    def _business_understanding(self, company_signals: dict) -> str:
        business_model = self.get_section("business_model", {})
        if business_model.get("business_summary") or business_model.get("summary"):
            model = company_signals["business_model_type"].replace("_", " ")
            return (
                "Clear / complex but understandable: the pack describes the "
                f"{model} economics and dominant revenue stream in usable terms."
            )
        return "Not clear: the business summary is missing from the current pack."

    def _business_quality(self) -> str:
        annual = self.get_section("financial_statements_summary", {}).get("annual", {})
        required = ["revenue", "operating_income", "net_income", "operating_cash_flow"]
        if all(annual.get(key) is not None for key in required):
            return "Strong to exceptional: core profitability and cash generation fields are present."
        return "Not established: one or more core financial fields are missing."

    def _incentives(self) -> str:
        management = self.get_section("management_ownership_incentives", {})
        gaps = " ".join(self.get_data_gaps()).lower()
        if management.get("gaps") or "management compensation details missing" in gaps:
            return "Mostly unclear from current pack: compensation detail and ownership alignment need deeper review."
        return "Partially supported: current pack includes some management incentive data."

    def _quality_of_earnings(self) -> str:
        annual = self.get_section("financial_statements_summary", {}).get("annual", {})
        operating_cash_flow = annual.get("operating_cash_flow")
        net_income = annual.get("net_income")
        if operating_cash_flow is not None and net_income is not None and operating_cash_flow > net_income:
            return "High, with capex interpretation needed: operating cash flow is greater than net income, but capex split is still unresolved."
        return "Not established: operating cash flow and net income relationship needs more complete data."

    def _hidden_stupidity_risk(self, company_signals: dict) -> str:
        return (
            "Hidden Stupidity Risk: "
            f"{company_signals['major_capex_issue']} requires evidence of rational returns; "
            f"the current capex profile is {company_signals['capex_profile']}."
        )

    def _price_vs_quality(self) -> str:
        historical = self.get_section("historical_valuation", {})
        gaps = " ".join(self.get_data_gaps()).lower()
        if historical.get("current_snapshot_only") or "historical valuation ranges missing" in gaps:
            return "Reasonable to demanding / not fully established: quality is evident, but valuation history and price discipline are incomplete."
        return "Partially established: valuation data is present but still needs a quality-adjusted price judgment."

    def _missing_backoffice_data(self) -> list[str]:
        peer = self.get_section("peer_comparison", {})
        sector_kpis = self.get_section("sector_specific_operating_kpis", {})
        historical = self.get_section("historical_valuation", {})
        gaps = " ".join(self.get_data_gaps()).lower()

        missing = [
            "Management compensation metrics.",
            "Insider ownership.",
            "Stock-based compensation trend.",
            "Maintenance versus growth capex.",
        ]

        cloud = sector_kpis.get("cloud", {}) if isinstance(sector_kpis, dict) else {}
        if "azure_profitability_trend" not in cloud:
            missing.append("Azure/cloud profitability trend.")
        if peer.get("status") == "incomplete" or "peer comparison incomplete" in gaps:
            missing.append("Peer comparison details.")
        if historical.get("current_snapshot_only") or "historical valuation ranges missing" in gaps:
            missing.append("Historical valuation ranges.")
        software = sector_kpis.get("software", {}) if isinstance(sector_kpis, dict) else {}
        if software.get("retention_churn") in (None, "", "unavailable"):
            missing.append("Customer retention indicators.")

        return missing

    def generate_report(self) -> str:
        """Generate a deterministic Munger-style Markdown report."""
        annual = self.get_section("financial_statements_summary", {}).get("annual", {})
        metrics = self.get_section("calculated_financial_metrics", {})
        risks = self.get_section("risk_register", {}).get("risks", [])
        moat = self.get_section("competitive_position_moat_indicators", {})
        growth = self.get_section("growth_drivers", {}).get("drivers", [])
        risk_names = [str(risk.get("name")) for risk in risks if isinstance(risk, dict)]
        company_signals = extract_company_signals(self.pack)
        inversion_matrix = build_munger_inversion_matrix(self.pack)
        incentive_scoring = score_munger_incentives_and_stupidity(self.pack)
        decision_candidate = build_decision_candidate(self.pack, "munger")
        promotion_eligibility = evaluate_promotion_eligibility(self.pack, "munger")
        top_failure_mode = next(
            (row for row in inversion_matrix if row["severity"] == "high"),
            inversion_matrix[0],
        )

        lines = [
            self.build_common_header(),
            "## Investor Identity",
            "Charlie Munger-style analysis focused on business quality, incentives, simplicity, and error avoidance.",
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
            f"- Major Capex Issue: {company_signals['major_capex_issue']}",
            f"- Munger Angle: {company_signals['investor_specific_angles']['munger']}",
            "",
            "## Core Question",
            "Is this a great business that can compound without obvious incentive, valuation, or stupidity traps?",
            "",
            "## Business Understanding",
            self._business_understanding(company_signals),
            f"Business summary: {self._business_summary()}",
            "",
            "## Business Quality",
            self._business_quality(),
            f"- Revenue: {annual.get('revenue', 'not provided')}",
            f"- Operating income: {annual.get('operating_income', 'not provided')}",
            f"- Net income: {annual.get('net_income', 'not provided')}",
            f"- Operating cash flow: {annual.get('operating_cash_flow', 'not provided')}",
            "",
            "## Incentives and Management Rationality",
            self._incentives(),
            "",
            "## Munger Incentives & Hidden-Stupidity Score",
            f"- Business Model Type: {incentive_scoring['business_model_type']}",
            (
                f"- Incentives Score / Label: {incentive_scoring['incentives_score']}/5 "
                f"/ {incentive_scoring['incentives_label']}"
            ),
            (
                f"- Capital Allocation Score / Label: "
                f"{incentive_scoring['capital_allocation_score']}/5 / "
                f"{incentive_scoring['capital_allocation_label']}"
            ),
            f"- Buyback Discipline Score: {incentive_scoring['buyback_discipline_score']}/5",
            (
                f"- Balance Sheet Discipline Score: "
                f"{incentive_scoring['balance_sheet_discipline_score']}/5"
            ),
            (
                f"- Acquisition Discipline Score: "
                f"{incentive_scoring['acquisition_discipline_score']}/5"
            ),
            (
                f"- Hidden-Stupidity Risk Score / Label: "
                f"{incentive_scoring['hidden_stupidity_risk_score']}/5 / "
                f"{incentive_scoring['hidden_stupidity_label']}"
            ),
            (
                f"- Overall Munger Quality Score: "
                f"{incentive_scoring['overall_munger_quality_score']}/5"
            ),
            "- Key Positive Evidence:",
            *[
                f"  - {item}"
                for item in (
                    incentive_scoring["key_positive_evidence"]
                    or ["No strong positive evidence established."]
                )
            ],
            "- Key Negative Evidence:",
            *[
                f"  - {item}"
                for item in (
                    incentive_scoring["key_negative_evidence"]
                    or ["No explicit negative evidence established."]
                )
            ],
            "- Evidence Gaps:",
            *[f"  - {item}" for item in incentive_scoring["evidence_gaps"]],
            f"- Munger Interpretation: {incentive_scoring['munger_interpretation']}",
            "- Required Evidence:",
            *[f"  - {item}" for item in incentive_scoring["required_evidence"]],
            "",
            "## Quality of Earnings",
            self._quality_of_earnings(),
            f"- Free cash flow margin: {metrics.get('free_cash_flow_margin', 'not provided')}",
            "",
            "## Ordinary Business Risk",
            *[f"- {name}" for name in risk_names],
            "",
            "## Hidden Stupidity Risk",
            self._hidden_stupidity_risk(company_signals),
            "",
            "## Inversion Analysis",
            *[f"- {row['failure_mode']}." for row in inversion_matrix],
            "",
            "## Munger Inversion Risk Matrix",
            "| Failure Mode | Evidence | Severity | What Would Reduce the Risk |",
            "| --- | --- | --- | --- |",
            *[
                f"| {row['failure_mode']} | {row['evidence']} | {row['severity']} | {row['what_would_reduce_the_risk']} |"
                for row in inversion_matrix
            ],
            "",
            "## Long-Term Compounding",
            f"The current pack identifies {company_signals['primary_growth_engine'].lower()} as the primary growth engine, with durability still requiring method-specific evidence.",
            *[f"- {driver}" for driver in growth],
            "",
            "## Price vs Quality",
            self._price_vs_quality(),
            "",
            "## Completed Investor Analysis",
            "- Business understandability review.",
            "- Initial quality and cash-generation screen.",
            "- Initial hidden-risk and inversion review.",
            "- Preliminary compounding driver map.",
            "",
            "## Missing Backoffice Data",
            *[f"- {item}" for item in self._missing_backoffice_data()],
            *[f"- Scoring gap: {item}" for item in incentive_scoring["evidence_gaps"]],
            "",
            "## Pending Investor Analysis",
            "- Deeper incentive quality judgment.",
            "- AI capex rationality assessment.",
            "- Stronger price vs quality judgment.",
            "- Final hidden stupidity risk assessment after more data.",
            "",
            "## Evidence Map",
            "- Business quality: financial_statements_summary",
            "- Capex rationality: capex_owner_earnings_proxy",
            "- Incentive uncertainty: management_ownership_incentives",
            "- Risk inversion: risk_register",
            "- Valuation uncertainty: historical_valuation",
            "",
            "## Key Supporting Evidence",
            f"- Latest annual revenue: {annual.get('revenue', 'not provided')}",
            f"- Latest annual operating income: {annual.get('operating_income', 'not provided')}",
            f"- Latest annual net income: {annual.get('net_income', 'not provided')}",
            f"- Latest annual operating cash flow: {annual.get('operating_cash_flow', 'not provided')}",
            *[f"- Moat indicator: {item}" for item in moat.get("moat_sources", [])],
            "",
            "## Key Objections",
            "- Valuation history is incomplete.",
            "- Maintenance versus growth capex is not disclosed.",
            f"- Returns from {company_signals['major_capex_issue'].lower()} are not yet fully proven in the pack.",
            "- Management compensation and ownership details need review.",
            "",
            "## Decision Rationale",
            f"{company_signals['decision_rationales']['munger']} Top inversion risk: {top_failure_mode['failure_mode']}.",
            "",
            *render_decision_candidate_section(decision_candidate),
            *render_promotion_eligibility_section(promotion_eligibility),
            "## Decision",
            "Buy Gradually / Wait for Better Evidence on AI Capex Returns",
            "",
            "## Confidence Level",
            "Medium",
            "",
            "## Final Munger Statement",
            f"{self.get_company_name()} looks like a high-quality, understandable business from the current pack, but the Munger-style answer remains provisional until incentives, capital allocation rationality, and price versus quality are better evidenced.",
            "",
        ]

        return "\n".join(lines)
