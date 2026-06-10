"""Deterministic Fisher-style investor agent."""

from pathlib import Path

from broker_agents.agents.base_investor_agent import BaseInvestorAgent
from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.calculators.decision_candidates import (
    build_decision_candidate,
    render_decision_candidate_section,
)
from broker_agents.calculators.fisher_scuttlebutt import (
    build_fisher_scuttlebutt_checklist,
)
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
    render_promotion_eligibility_section,
)

class FisherAgent(BaseInvestorAgent):
    """Generate a simple Philip Fisher-style report from a backoffice pack."""

    def __init__(self, pack: dict, method_path: Path) -> None:
        super().__init__(pack=pack, method_path=method_path)

    def _business_text(self) -> str:
        business_model = self.get_section("business_model", {})
        segments = self.get_section("products_customers_revenue_segments", {}).get("segments", [])
        segment_text = " ".join(
            " ".join(str(item) for item in segment.get("examples", []))
            for segment in segments
            if isinstance(segment, dict)
        )
        return " ".join(
            [
                str(business_model.get("business_summary", "")),
                str(business_model.get("summary", "")),
                segment_text,
            ]
        )

    def _long_term_growth_runway(self, signals: dict) -> str:
        if signals["primary_growth_engine"] != "Not established from current pack":
            return (
                "Preliminary strong runway: the detected primary growth engine is "
                f"{signals['primary_growth_engine'].lower()}."
            )
        return "Not established: the current pack does not identify a durable growth engine."

    def _product_service_quality(self, signals: dict) -> str:
        if self._business_text().strip():
            return (
                "Strong, pending deeper scuttlebutt: the pack describes a "
                f"{signals['business_model_type'].replace('_', ' ')} model with "
                f"{signals['dominant_revenue_stream'].lower()}."
            )
        return "Not established: product and service detail is too thin."

    def _innovation_rd(self, signals: dict) -> str:
        growth_drivers = self.get_section("growth_drivers", {}).get("drivers", [])
        if growth_drivers:
            return (
                "Potentially effective: reported growth drivers support "
                f"{signals['primary_growth_engine'].lower()}, but long-term innovation "
                "productivity still needs evidence."
            )
        return "Not established: innovation and R&D evidence is incomplete."

    def _quality_of_growth(self, signals: dict) -> str:
        kpis = self.get_section("sector_specific_operating_kpis", {})
        if kpis:
            return (
                "Preliminary: operating KPIs support the detected "
                f"{signals['business_model_type'].replace('_', ' ')} growth story, "
                f"with {signals['major_capex_issue'].lower()} requiring continued review."
            )
        return "Not established: business-model operating KPIs are incomplete."

    def _scuttlebutt_evidence(self) -> str:
        scuttlebutt = self.get_section("scuttlebutt", {})
        if scuttlebutt.get("status") in ("weak_unavailable", "unavailable", "missing"):
            return "Unavailable / weak in current pack: no direct customer, developer, partner, employee, or channel checks are included."
        return "Partially available: qualitative evidence exists but should still be reviewed."

    def _valuation_vs_growth(self) -> str:
        valuation = self.get_section("valuation_snapshot", {})
        if valuation.get("status") in ("market_data_placeholder", "missing", None):
            return "Not fully established: growth quality is visible, but current valuation and expectations need stronger data."
        return "Preliminary: valuation data is available but should be tested against durable growth."

    def _missing_backoffice_data(self, signals: dict, checklist: dict) -> list[str]:
        peer = self.get_section("peer_comparison", {})
        missing = [
            f"{item['evidence_area']}: {item['evidence_needed']}"
            for item in checklist["evidence_gaps"]
        ]
        missing.extend(
            [
            "R&D history and R&D intensity.",
            "Customer/developer/partner scuttlebutt.",
            "Employee/culture indicators.",
            ]
        )
        if peer.get("status") == "incomplete":
            missing.append("Business-model peer comparison.")
        missing.extend(str(gap) for gap in signals["major_data_gaps"] if str(gap) not in missing)
        return list(dict.fromkeys(missing))

    def generate_report(self) -> str:
        """Generate a deterministic Fisher-style Markdown report."""
        growth_drivers = self.get_section("growth_drivers", {}).get("drivers", [])
        segments = self.get_section("products_customers_revenue_segments", {}).get("segments", [])
        risks = self.get_section("risk_register", {}).get("risks", [])
        risk_names = [str(risk.get("name")) for risk in risks if isinstance(risk, dict)]
        company_signals = extract_company_signals(self.pack)
        scuttlebutt_checklist = build_fisher_scuttlebutt_checklist(self.pack)
        decision_candidate = build_decision_candidate(self.pack, "fisher")
        promotion_eligibility = evaluate_promotion_eligibility(self.pack, "fisher")

        lines = [
            self.build_common_header(),
            "## Investor Identity",
            "Philip Fisher-style growth analysis focused on long runway, product quality, management depth, and scuttlebutt evidence.",
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
            f"- Fisher Angle: {company_signals['investor_specific_angles']['fisher']}",
            "",
            "## Core Question",
            "Can this company compound for many years because customers, products, innovation, and management quality are unusually strong?",
            "",
            "## Long-Term Growth Runway",
            self._long_term_growth_runway(company_signals),
            "",
            "## Product or Service Quality",
            self._product_service_quality(company_signals),
            *[
                f"- {segment.get('name')}: {', '.join(segment.get('examples', []))}"
                for segment in segments
                if isinstance(segment, dict)
            ],
            "",
            "## Innovation and R&D",
            self._innovation_rd(company_signals),
            "",
            "## Sales and Distribution",
            f"Distribution evidence for the {company_signals['business_model_type'].replace('_', ' ')} model is incomplete and does not yet quantify sales efficiency or channel quality.",
            "",
            "## Management and Culture",
            "Management and culture evidence is incomplete; Fisher-style assessment needs deeper employee, customer, and partner checks.",
            "",
            "## Quality of Growth",
            self._quality_of_growth(company_signals),
            "",
            "## Scuttlebutt Evidence",
            self._scuttlebutt_evidence(),
            "",
            "## Fisher Scuttlebutt Checklist",
            f"- Business Model Type: {scuttlebutt_checklist['business_model_type']}",
            f"- Readiness Label: {scuttlebutt_checklist['readiness_label']}",
            "- Priority Evidence Needed:",
            *[
                f"  - {item['evidence_area']}: {item['evidence_needed']}"
                for item in scuttlebutt_checklist["priority_items"]
            ],
            "",
            "| Evidence Area | Evidence Needed | Priority | Suggested Sources | Blocks Upgrade |",
            "| --- | --- | --- | --- | --- |",
            *[
                f"| {item['evidence_area']} | {item['evidence_needed']} | "
                f"{item['priority']} | {', '.join(item['suggested_sources'])} | "
                f"{'Yes' if item['blocks_fisher_upgrade'] else 'No'} |"
                for item in scuttlebutt_checklist["checklist_items"]
            ],
            "",
            "## Valuation vs Growth Potential",
            self._valuation_vs_growth(),
            "",
            "## Completed Investor Analysis",
            "- Initial growth runway screen.",
            "- Initial product and platform quality review.",
            "- Initial cloud KPI review.",
            "- Initial scuttlebutt gap review.",
            "",
            "## Missing Backoffice Data",
            *[
                f"- {item}"
                for item in self._missing_backoffice_data(
                    company_signals,
                    scuttlebutt_checklist,
                )
            ],
            "",
            "## Pending Investor Analysis",
            "- Stronger scuttlebutt judgment.",
            f"- Validate this evidence need: {company_signals['investor_specific_angles']['fisher']}.",
            "- Innovation productivity assessment.",
            "- Culture and talent assessment.",
            "- Stronger valuation vs growth judgment.",
            "",
            "## Evidence Map",
            "- Business-model operating evidence: sector_specific_operating_kpis",
            "- Financial growth evidence: financial_statements_summary",
            "- Growth drivers: growth_drivers",
            "- Scuttlebutt gap: scuttlebutt",
            "- Peer context gap: peer_comparison",
            "",
            "## Key Supporting Evidence",
            f"- Primary growth engine: {company_signals['primary_growth_engine']}",
            f"- Dominant revenue stream: {company_signals['dominant_revenue_stream']}",
            *[f"- Growth driver: {driver}" for driver in growth_drivers],
            "",
            "## Key Objections",
            *[f"- {name}" for name in risk_names],
            "- Scuttlebutt evidence is unavailable or weak.",
            f"- {company_signals['major_capex_issue']} needs more return evidence.",
            "- Product-level profitability is incomplete.",
            "",
            "## Decision Rationale",
            company_signals["decision_rationales"]["fisher"],
            "",
            *render_decision_candidate_section(decision_candidate),
            *render_promotion_eligibility_section(promotion_eligibility),
            "## Decision",
            "Needs More Scuttlebutt / Watch Closely",
            "",
            "## Confidence Level",
            "Medium",
            "",
            "## Final Fisher Statement",
            f"{self.get_company_name()} shows a preliminary Fisher-style runway around {company_signals['primary_growth_engine'].lower()}, but the report remains provisional because scuttlebutt, product economics, and customer evidence are not yet strong enough.",
            "",
        ]

        return "\n".join(lines)
