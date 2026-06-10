"""Deterministic Buffett-style investor agent."""

from pathlib import Path

from broker_agents.agents.base_investor_agent import BaseInvestorAgent
from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.calculators.buffett_decision_conditions import (
    build_buffett_decision_conditions,
)
from broker_agents.calculators.decision_candidates import (
    build_decision_candidate,
    render_decision_candidate_section,
)
from broker_agents.calculators.intrinsic_value import (
    calculate_buffett_intrinsic_value_range,
)
from broker_agents.calculators.normalized_owner_earnings import (
    calculate_normalized_owner_earnings,
)
from broker_agents.calculators.owner_earnings import calculate_owner_earnings_snapshot
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
    render_promotion_eligibility_section,
)
from broker_agents.calculators.valuation_guardrails import calculate_valuation_guardrails
from broker_agents.calculators.valuation_history import analyze_valuation_history
from broker_agents.reports.formatting import (
    format_millions,
    format_multiple,
    format_ratio_as_percent,
    format_yield,
)


class BuffettAgent(BaseInvestorAgent):
    """Generate a simple Warren Buffett-style report from a backoffice pack."""

    def __init__(self, pack: dict, method_path: Path) -> None:
        super().__init__(pack=pack, method_path=method_path)

    def _business_summary(self) -> str:
        business_model = self.get_section("business_model", {})
        return str(
            business_model.get("business_summary")
            or business_model.get("summary")
            or "No business model summary provided."
        )

    def _circle_of_competence(self, company_signals: dict) -> str:
        business_model = self.get_section("business_model", {})
        if business_model.get("business_summary") or business_model.get("summary"):
            model = company_signals["business_model_type"].replace("_", " ")
            return (
                "Inside / partially inside: the pack provides an understandable "
                f"description of the {model} business model and its main economics."
            )
        return "Outside: the business model summary is missing."

    def _business_quality(self) -> str:
        annual = self.get_section("financial_statements_summary", {}).get("annual", {})
        required = ["revenue", "operating_income", "net_income", "operating_cash_flow"]
        if all(annual.get(key) is not None for key in required):
            return "High: revenue, operating income, net income, and operating cash flow are present in the backoffice pack."
        return "Not established: one or more core financial quality fields are missing."

    def _owner_earnings_confidence(self) -> str:
        owner_earnings = self.get_section("capex_owner_earnings_proxy", {})
        caveat = str(owner_earnings.get("caveat", "")).lower()
        gaps = " ".join(self.get_data_gaps()).lower()
        if owner_earnings and ("maintenance" in caveat or "maintenance vs growth capex" in gaps):
            return "Medium: free cash flow is available, but maintenance versus growth capex is not disclosed."
        if owner_earnings:
            return "Medium-high: owner earnings proxy data is present, subject to later normalization."
        return "Low: owner earnings proxy data is missing."

    def _valuation_view(self) -> str:
        history = analyze_valuation_history(self.pack)
        if history["valuation_history_label"] == "not established":
            return "Not established: valuation history and intrinsic value work are incomplete."
        return (
            f"Preliminary: valuation is {history['valuation_history_label']}; "
            "placeholder history still requires source verification."
        )

    def _missing_backoffice_data(self) -> list[str]:
        gaps = " ".join(self.get_data_gaps()).lower()
        missing: list[str] = []

        historical = self.get_section("historical_valuation", {})
        peer = self.get_section("peer_comparison", {})
        sector_kpis = self.get_section("sector_specific_operating_kpis", {})
        management = self.get_section("management_ownership_incentives", {})
        capex = self.get_section("capex_owner_earnings_proxy", {})

        if historical.get("valuation_history_confidence") == "medium_placeholder":
            missing.append("Valuation history source verification.")
            missing.append("5Y/10Y valuation data validation.")
        if "maintenance vs growth capex" in gaps or "maintenance" in str(capex.get("caveat", "")).lower():
            missing.append("Maintenance versus growth capex split.")
        if sector_kpis.get("software", {}).get("retention_churn") in (None, "", "unavailable"):
            missing.append("Customer retention or churn data.")
        if management.get("gaps") or "management compensation details missing" in gaps:
            missing.append("Management compensation details.")
        if peer.get("status") == "incomplete" or "peer comparison incomplete" in gaps:
            missing.append("Peer comparison metrics.")

        return missing

    def _decision(self) -> str:
        return "Wait for Better Price / Complete Intrinsic Value Work"

    def _confidence(self) -> str:
        missing_text = " ".join(self._missing_backoffice_data()).lower()
        if "historical valuation" in missing_text or "maintenance" in missing_text:
            return "Medium"
        return "Medium-high"

    def _buffett_decision_rationale(
        self,
        company_signals: dict,
        snapshot: dict,
        guardrails: dict,
    ) -> str:
        """Return company-specific Buffett rationale with owner earnings context."""
        rationale = company_signals["decision_rationales"]["buffett"]
        capex_label = snapshot.get("capex_intensity_label")
        quality_label = snapshot.get("owner_earnings_quality_label")
        valuation_status = guardrails.get("valuation_status")
        if capex_label == "high":
            rationale = (
                f"{rationale} Owner earnings need caution because capex absorbs a large "
                "share of operating cash flow."
            )
        elif capex_label == "low" and quality_label == "strong":
            rationale = (
                f"{rationale} Cash conversion and the owner earnings proxy appear stronger, "
                "while valuation work remains incomplete."
            )
        if valuation_status == "demanding":
            return (
                f"{rationale} Valuation appears demanding based on FCF yield / P/FCF guardrails."
            )
        if valuation_status == "reasonable":
            return f"{rationale} Valuation appears reasonable but still needs intrinsic value work."
        return rationale

    def generate_report(self) -> str:
        """Generate a deterministic Buffett-style Markdown report."""
        annual = self.get_section("financial_statements_summary", {}).get("annual", {})
        metrics = self.get_section("calculated_financial_metrics", {})
        moat = self.get_section("competitive_position_moat_indicators", {})
        capital_allocation = self.get_section("capital_allocation", {})
        owner_earnings = self.get_section("capex_owner_earnings_proxy", {})
        risks = self.get_section("risk_register", {}).get("risks", [])
        missing = self._missing_backoffice_data()
        decision = self._decision()
        confidence = self._confidence()
        company_signals = extract_company_signals(self.pack)
        owner_earnings_snapshot = calculate_owner_earnings_snapshot(self.pack)
        valuation_guardrails = calculate_valuation_guardrails(self.pack)
        intrinsic_value = calculate_buffett_intrinsic_value_range(self.pack)
        valuation_history = analyze_valuation_history(self.pack)
        normalized_owner_earnings = calculate_normalized_owner_earnings(self.pack)
        decision_conditions = build_buffett_decision_conditions(self.pack)
        decision_candidate = build_decision_candidate(self.pack, "buffett")
        promotion_eligibility = evaluate_promotion_eligibility(self.pack, "buffett")
        decision_rationale = self._buffett_decision_rationale(
            company_signals,
            owner_earnings_snapshot,
            valuation_guardrails,
        )

        moat_sources = moat.get("moat_sources", [])
        risk_names = [str(risk.get("name")) for risk in risks if isinstance(risk, dict)]

        lines = [
            self.build_common_header(),
            "## Investor Identity",
            "Warren Buffett-style business owner analysis using deterministic backoffice rules.",
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
            f"- Capex Profile: {company_signals['capex_profile']}",
            f"- Major Capex Issue: {company_signals['major_capex_issue']}",
            f"- Buffett Angle: {company_signals['investor_specific_angles']['buffett']}",
            "",
            "## Core Question",
            "Is this an understandable, durable business that can be valued conservatively with a clear Margin of Safety?",
            "",
            "## Circle of Competence",
            self._circle_of_competence(company_signals),
            "",
            "## Business Quality",
            self._business_quality(),
            f"Business summary: {self._business_summary()}",
            "",
            "## Economic Moat",
            *[f"- {item}" for item in moat_sources],
            "",
            "## Owner Earnings and Cash Generation",
            f"- Operating cash flow: {annual.get('operating_cash_flow', 'not provided')}",
            f"- Capex: {owner_earnings.get('capex', annual.get('capex', 'not provided'))}",
            f"- Free cash flow: {owner_earnings.get('free_cash_flow', annual.get('free_cash_flow', 'not provided'))}",
            f"- Owner earnings confidence: {self._owner_earnings_confidence()}",
            "",
            "## Preliminary Owner Earnings Snapshot",
            f"- Operating Cash Flow: {format_millions(owner_earnings_snapshot['operating_cash_flow'])}",
            f"- Capex: {format_millions(owner_earnings_snapshot['capex'])}",
            f"- Free Cash Flow / Owner Earnings Proxy: {format_millions(owner_earnings_snapshot['owner_earnings_proxy'])}",
            f"- FCF Margin: {format_ratio_as_percent(owner_earnings_snapshot['fcf_margin'])}",
            f"- Capex / OCF: {format_ratio_as_percent(owner_earnings_snapshot['capex_to_ocf'])}",
            f"- Capex Intensity Label: {owner_earnings_snapshot['capex_intensity_label']}",
            f"- Owner Earnings Quality Label: {owner_earnings_snapshot['owner_earnings_quality_label']}",
            *[f"- Note: {note}" for note in owner_earnings_snapshot["notes"]],
            "",
            "## Preliminary Valuation Guardrails",
            f"- Market Cap: {format_millions(valuation_guardrails['market_cap'])}",
            f"- P/E: {format_multiple(valuation_guardrails['pe'])}",
            f"- P/FCF: {format_multiple(valuation_guardrails['p_fcf'])}",
            f"- Earnings Yield: {format_yield(valuation_guardrails['earnings_yield'])}",
            f"- FCF Yield: {format_yield(valuation_guardrails['fcf_yield'])}",
            f"- Valuation Status: {valuation_guardrails['valuation_status']}",
            f"- Valuation Confidence: {valuation_guardrails['valuation_confidence']}",
            *[f"- Note: {note}" for note in valuation_guardrails["notes"]],
            "",
            "## Valuation History Evidence",
            f"- Current P/FCF: {format_multiple(valuation_history['current_p_fcf'])}",
            f"- 5Y Median P/FCF: {format_multiple(valuation_history['p_fcf_5y_median'])}",
            f"- 10Y Median P/FCF: {format_multiple(valuation_history['p_fcf_10y_median'])}",
            (
                "- Current P/FCF Percentile: "
                f"5Y {format_ratio_as_percent(valuation_history['current_vs_5y_p_fcf_percentile'])}; "
                f"10Y {format_ratio_as_percent(valuation_history['current_vs_10y_p_fcf_percentile'])}"
            ),
            f"- Valuation History Label: {valuation_history['valuation_history_label']}",
            f"- Confidence: {valuation_history['valuation_history_confidence']}",
            *[f"- Note: {note}" for note in valuation_history["notes"]],
            "",
            "## Normalized Owner Earnings Evidence",
            f"- Latest Owner Earnings: {format_millions(normalized_owner_earnings['latest_owner_earnings'])}",
            f"- Normalized Owner Earnings: {format_millions(normalized_owner_earnings['normalized_owner_earnings'])}",
            f"- Method: {normalized_owner_earnings['normalization_method']}",
            f"- FCF History Years: {normalized_owner_earnings['fcf_history_available_years']}",
            f"- Normalized FCF Margin: {format_ratio_as_percent(normalized_owner_earnings['normalized_fcf_margin'])}",
            f"- Durability Label: {normalized_owner_earnings['owner_earnings_durability_label']}",
            f"- Confidence: {normalized_owner_earnings['normalized_owner_earnings_confidence']}",
            "- Evidence Gaps:",
            *[
                f"  - {item}"
                for item in normalized_owner_earnings["evidence_gaps"]
            ],
            "",
            "## Preliminary Intrinsic Value Range",
            f"- Owner Earnings Base: {format_millions(intrinsic_value['owner_earnings_base'])}",
            f"- Intrinsic Value Low: {format_millions(intrinsic_value['intrinsic_value_low'])}",
            f"- Intrinsic Value Mid: {format_millions(intrinsic_value['intrinsic_value_mid'])}",
            f"- Intrinsic Value High: {format_millions(intrinsic_value['intrinsic_value_high'])}",
            f"- Market Cap: {format_millions(intrinsic_value['market_cap'])}",
            f"- Margin of Safety Low: {format_ratio_as_percent(intrinsic_value['margin_of_safety_low'])}",
            f"- Margin of Safety Mid: {format_ratio_as_percent(intrinsic_value['margin_of_safety_mid'])}",
            f"- Margin of Safety High: {format_ratio_as_percent(intrinsic_value['margin_of_safety_high'])}",
            f"- Valuation Gap Label: {intrinsic_value['valuation_gap_label']}",
            f"- Intrinsic Value Confidence: {intrinsic_value['intrinsic_value_confidence']}",
            "- Key Assumptions:",
            *[f"  - {item}" for item in intrinsic_value["assumptions"]],
            "- Warnings:",
            *[f"  - {item}" for item in intrinsic_value["warnings"]],
            "",
            "## Management and Capital Allocation",
            f"- Dividends paid: {capital_allocation.get('dividends_paid', annual.get('dividends_paid', 'not provided'))}",
            f"- Share repurchases: {capital_allocation.get('share_repurchases', annual.get('share_repurchases', 'not provided'))}",
            f"- Capex: {capital_allocation.get('capex', annual.get('capex', 'not provided'))}",
            "- Compensation and ownership details remain a backoffice follow-up item.",
            "",
            "## Balance Sheet Strength",
            f"- Cash and short-term investments: {annual.get('cash_and_short_term_investments', 'not provided')}",
            f"- Long-term debt: {annual.get('long_term_debt', 'not provided')}",
            f"- Debt to equity: {metrics.get('debt_to_equity', 'not provided')}",
            f"- Cash to long-term debt: {metrics.get('cash_to_long_term_debt', 'not provided')}",
            "",
            "## Valuation and Margin of Safety",
            self._valuation_view(),
            (
                "Preliminary midpoint margin of safety: "
                f"{format_ratio_as_percent(intrinsic_value['margin_of_safety_mid'])}. "
                "This remains subject to normalization and validation."
            ),
            "",
            "## Completed Investor Analysis",
            "- Business model review.",
            "- Initial financial quality screen.",
            "- Initial cash generation and balance sheet review.",
            "- Preliminary capital allocation review.",
            "",
            "## Missing Backoffice Data",
            *[f"- {item}" for item in missing],
            "",
            "## Pending Investor Analysis",
            "- Validate the preliminary intrinsic value range.",
            "- Validate the margin of safety estimate.",
            "- Normalized owner earnings.",
            "- Durability of moat assessment.",
            "",
            "## Evidence Map",
            "- Revenue and cash generation: financial_statements_summary",
            "- Capex uncertainty: capex_owner_earnings_proxy",
            "- Valuation uncertainty: historical_valuation",
            "- Management incentives gap: management_ownership_incentives",
            "- Source support: sources_confidence_data_gaps.source_log",
            "",
            "## Key Supporting Evidence",
            f"- Latest annual revenue: {annual.get('revenue', 'not provided')}",
            f"- Latest annual operating income: {annual.get('operating_income', 'not provided')}",
            f"- Latest annual net income: {annual.get('net_income', 'not provided')}",
            f"- Latest annual operating cash flow: {annual.get('operating_cash_flow', 'not provided')}",
            "",
            "## Key Objections",
            *[f"- {name}" for name in risk_names],
            "- Intrinsic value and historical valuation context are not complete.",
            "",
            "## Decision Rationale",
            decision_rationale,
            "",
            "## Decision Upgrade / Downgrade Conditions",
            "Conditions that could improve the decision:",
            *[f"- {item}" for item in decision_conditions["upgrade_conditions"]],
            "",
            "Conditions that could worsen the decision:",
            *[f"- {item}" for item in decision_conditions["downgrade_conditions"]],
            "",
            "Watch items:",
            *[f"- {item}" for item in decision_conditions["watch_items"]],
            "",
            *render_decision_candidate_section(decision_candidate),
            *render_promotion_eligibility_section(promotion_eligibility),
            "## Decision",
            decision,
            "",
            "## Confidence Level",
            confidence,
            "",
            "## Final Buffett Statement",
            f"{self.get_company_name()} appears to be a high-quality business from the available backoffice evidence, but the Buffett-style conclusion remains incomplete until owner earnings normalization, intrinsic value, and a clear Margin of Safety are established.",
            "",
        ]

        return "\n".join(lines)
