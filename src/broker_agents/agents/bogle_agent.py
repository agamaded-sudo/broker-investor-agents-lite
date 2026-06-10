"""Deterministic Bogle-style investor agent."""

from pathlib import Path

from broker_agents.agents.base_investor_agent import BaseInvestorAgent
from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.calculators.bogle_benchmark_risk import (
    calculate_bogle_benchmark_risk,
)
from broker_agents.calculators.bogle_index_overlap import (
    calculate_bogle_index_overlap,
)
from broker_agents.calculators.decision_candidates import (
    build_decision_candidate,
    render_decision_candidate_section,
)
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
    render_promotion_eligibility_section,
)


class BogleAgent(BaseInvestorAgent):
    """Generate a simple John Bogle-style report from a backoffice pack."""

    def __init__(self, pack: dict, method_path: Path) -> None:
        super().__init__(pack=pack, method_path=method_path)

    def _benchmark_alternative(self) -> str:
        return (
            "Benchmark alternatives: S&P 500 / VOO, Total US Market / VTI, "
            "and Nasdaq 100 / QQQ."
        )

    def _stock_vs_index_status(self) -> str:
        benchmark = self.get_section("index_benchmark_alternative", {})
        gaps = " ".join(benchmark.get("gaps", [])).lower() if isinstance(benchmark, dict) else ""
        if benchmark and "index weights missing" in gaps:
            return "Incomplete: benchmark alternatives are listed, but index weights are missing."
        if benchmark:
            return "Partially documented: benchmark alternatives are present but still require return and risk comparison."
        return "Incomplete: benchmark alternative data is missing."

    def _portfolio_context(self) -> str:
        portfolio_context = self.get_section("portfolio_context_form", {})
        if portfolio_context.get("provided") is False or portfolio_context.get("status") == "missing":
            return "Missing: no investor-specific portfolio context is provided."
        return "Partially provided: portfolio context exists but should be checked before sizing."

    def _portfolio_analysis(self) -> dict:
        """Return deterministic portfolio context metrics for the reviewed ticker."""
        context = self.get_section("portfolio_context_form", {})
        provided = context.get("provided") is True
        holdings = context.get("current_holdings", {})
        index_funds = holdings.get("index_funds", []) if isinstance(holdings, dict) else []
        index_core_weight = sum(
            float(item.get("weight", 0))
            for item in index_funds
            if isinstance(item, dict)
        )
        constraints = context.get("constraints", {})
        maximum_weight = constraints.get("maximum_single_stock_weight")
        satellites_allowed = constraints.get("satellite_positions_allowed")
        exposure = context.get("indirect_exposure_estimates", {}).get(
            self.get_ticker(),
            {},
        )
        return {
            "provided": provided,
            "index_core_weight": index_core_weight if provided else None,
            "maximum_single_stock_weight": maximum_weight,
            "current_indirect_exposure": exposure.get("via_index_funds"),
            "current_total_exposure": exposure.get("current_total"),
            "satellite_positions_allowed": satellites_allowed,
        }

    def _diversification_impact(self, signals: dict) -> str:
        base = signals["investor_specific_angles"]["bogle"]
        model = signals["business_model_type"]
        if model in {"semiconductor", "industrial", "financial"}:
            return (
                f"{base}. This {model.replace('_', ' ')} business may carry greater "
                "cyclical or balance-sheet risk than broad index exposure."
            )
        if model in {"software_cloud", "consumer_ecosystem"}:
            return (
                f"{base}. Business quality does not automatically justify separate ownership "
                "when the company is already heavily represented in broad indexes."
            )
        return f"{base}. Portfolio concentration and index overlap still require measurement."

    def _missing_backoffice_data(self) -> list[str]:
        return [
            "Weight in S&P 500.",
            "Weight in Nasdaq 100.",
            "Total return vs benchmark over 1Y/3Y/5Y/10Y.",
            "Volatility vs benchmark.",
            "Max drawdown vs benchmark.",
            "Beta and correlation.",
            "Valuation vs index.",
            "Benchmark ETF expense ratios.",
        ]

    def _missing_portfolio_context(self) -> list[str]:
        return [
            "Whether investor owns VOO/VTI/QQQ.",
            f"Current indirect {self.get_ticker()} exposure via index funds.",
            "Current technology sector weight.",
            "Maximum allowed single-stock weight.",
            "Investment horizon and drawdown tolerance.",
        ]

    def _pending_analysis(self) -> list[str]:
        return [
            f"Whether {self.get_ticker()} has outperformed the benchmark after risk.",
            f"Whether owning {self.get_ticker()} separately adds value beyond index exposure.",
            "Whether a limited weight is acceptable.",
            "What weight range is reasonable if portfolio context is provided.",
        ]

    def generate_report(self) -> str:
        """Generate a deterministic Bogle-style Markdown report."""
        annual = self.get_section("financial_statements_summary", {}).get("annual", {})
        benchmark = self.get_section("index_benchmark_alternative", {})
        market_awareness = self.get_section("market_awareness", {})
        company_signals = extract_company_signals(self.pack)
        overlap = calculate_bogle_index_overlap(self.pack)
        benchmark_risk = calculate_bogle_benchmark_risk(self.pack)
        decision_candidate = build_decision_candidate(self.pack, "bogle")
        promotion_eligibility = evaluate_promotion_eligibility(self.pack, "bogle")
        portfolio_analysis = self._portfolio_analysis()
        context_provided = portfolio_analysis["provided"]
        missing_context = self._missing_portfolio_context() if not context_provided else []
        suggested_range = overlap["suggested_weight_range"]
        if isinstance(suggested_range, dict):
            suggested_range_text = (
                f"Conservative {suggested_range['conservative']}; "
                f"moderate {suggested_range['moderate']}; maximum guardrail "
                f"{suggested_range['maximum_guardrail']:.1%}"
            )
        else:
            suggested_range_text = suggested_range

        lines = [
            self.build_common_header(),
            "## Investor Identity",
            "John Bogle-style analysis focused on broad diversification, benchmark opportunity cost, low costs, and investor behavior.",
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
            f"- Bogle Angle: {company_signals['investor_specific_angles']['bogle']}",
            "",
            "## Core Question",
            "Does owning the individual stock add enough value over a low-cost broad index fund to justify concentration and behavior risk?",
            "",
            "## Benchmark Alternative",
            self._benchmark_alternative(),
            "",
            "## Stock vs Index Performance",
            self._stock_vs_index_status(),
            "",
            "## Stock vs Index Risk",
            benchmark_risk["benchmark_risk_label"],
            "",
            "## Valuation vs Market",
            "Incomplete: valuation versus the broad market and Nasdaq-heavy benchmarks is not established.",
            "",
            "## Diversification Impact",
            self._diversification_impact(company_signals),
            "",
            "## Cost and Behavior Check",
            f"Broad index funds are usually simpler and cheaper to hold. A separate {self.get_ticker()} position adds tracking, sizing, tax, and behavior decisions.",
            "",
            "## Case for Owning Stock Instead of Index",
            "Moderate, not strong enough without benchmark and portfolio context.",
            "",
            "## Portfolio Context",
            self._portfolio_context(),
            "",
            "## Portfolio Context Analysis",
            f"- Portfolio context provided: {'Yes' if context_provided else 'No'}",
            f"- Index core weight: {portfolio_analysis['index_core_weight']:.1%}" if context_provided else "- Index core weight: Not available",
            f"- Maximum single-stock weight: {portfolio_analysis['maximum_single_stock_weight']:.1%}" if portfolio_analysis["maximum_single_stock_weight"] is not None else "- Maximum single-stock weight: Not available",
            f"- Current indirect exposure: {portfolio_analysis['current_indirect_exposure']:.1%}" if portfolio_analysis["current_indirect_exposure"] is not None else "- Current indirect exposure: Not available",
            f"- Current total exposure: {portfolio_analysis['current_total_exposure']:.1%}" if portfolio_analysis["current_total_exposure"] is not None else "- Current total exposure: Not available",
            f"- Satellite positions allowed: {'Yes' if portfolio_analysis['satellite_positions_allowed'] is True else 'No' if portfolio_analysis['satellite_positions_allowed'] is False else 'Not available'}",
            f"- Bogle candidate interpretation: {decision_candidate['candidate_decision']}",
            "",
            "## Bogle Index Overlap & Benchmark Risk",
            (
                f"- Index funds owned: {', '.join(overlap['index_funds_owned'])}"
                if overlap["index_funds_owned"]
                else "- Index funds owned: Not available"
            ),
            (
                f"- Estimated indirect exposure: "
                f"{overlap['estimated_indirect_exposure']:.1%}"
                if overlap["estimated_indirect_exposure"] is not None
                else "- Estimated indirect exposure: Not available"
            ),
            (
                f"- Current total exposure: {overlap['current_total_exposure']:.1%}"
                if overlap["current_total_exposure"] is not None
                else "- Current total exposure: Not available"
            ),
            (
                f"- Maximum single-stock weight: "
                f"{overlap['maximum_single_stock_weight']:.1%}"
                if overlap["maximum_single_stock_weight"] is not None
                else "- Maximum single-stock weight: Not available"
            ),
            (
                f"- Remaining allowed capacity: "
                f"{overlap['remaining_allowed_single_stock_capacity']:.1%}"
                if overlap["remaining_allowed_single_stock_capacity"] is not None
                else "- Remaining allowed capacity: Not available"
            ),
            (
                f"- Index core weight: {overlap['index_core_weight']:.1%}"
                if overlap["index_core_weight"] is not None
                else "- Index core weight: Not available"
            ),
            f"- Overlap label: {overlap['overlap_label']}",
            f"- Concentration risk label: {overlap['concentration_risk_label']}",
            (
                f"- Limited-weight candidate: "
                f"{'Yes' if overlap['limited_weight_candidate'] else 'No'}"
            ),
            f"- Suggested weight range: {suggested_range_text}",
            f"- Benchmark index / ETF: {benchmark_risk['benchmark_index']} / {benchmark_risk['benchmark_etf']}",
            f"- Benchmark risk label: {benchmark_risk['benchmark_risk_label']}",
            "- Missing benchmark evidence:",
            *[
                f"  - {item}"
                for item in (
                    benchmark_risk["missing_benchmark_evidence"]
                    or ["None identified."]
                )
            ],
            "- Warnings:",
            *[f"  - {item}" for item in overlap["warnings"]],
            "",
            "## Suggested Limited Weight if Applicable",
            (
                f"A limited position may be evaluated up to the portfolio constraint of "
                f"{portfolio_analysis['maximum_single_stock_weight']:.1%}, subject to index "
                "overlap, benchmark-relative risk, and human sizing review. The Bogle Agent "
                "does not use a traditional Buy decision."
                if context_provided
                and portfolio_analysis["maximum_single_stock_weight"] is not None
                else "No specific weight is suggested until portfolio context is provided. "
                "The most positive Bogle decision is: Individual Stock Acceptable at Limited "
                "Weight. The Bogle Agent does not use a traditional Buy decision."
            ),
            "",
            "## Completed Investor Analysis",
            "- Identified broad index alternatives.",
            "- Flagged missing benchmark-relative return and risk data.",
            (
                "- Reviewed supplied investor portfolio context."
                if context_provided
                else "- Flagged missing investor portfolio context."
            ),
            "- Assessed likely concentration impact.",
            "",
            "## Missing Backoffice Data",
            *[
                f"- {item}"
                for item in (
                    benchmark_risk["missing_benchmark_evidence"]
                    + [
                        "Index and ETF holdings validation.",
                        "Valuation versus index.",
                        "Benchmark ETF expense ratios.",
                    ]
                )
            ],
            *[f"- Detected gap: {item}" for item in company_signals["major_data_gaps"]],
            "",
            "## Missing Portfolio Context",
            *([f"- {item}" for item in missing_context] or ["- None; portfolio context was provided."]),
            "",
            "## Pending Investor Analysis",
            *[f"- {item}" for item in self._pending_analysis()],
            "",
            "## Evidence Map",
            "- Benchmark gap: index_benchmark_alternative",
            "- Portfolio context: portfolio_context_form",
            "- Market data gap: market_awareness",
            "- Company scale evidence: financial_statements_summary",
            "- Source support: sources_confidence_data_gaps.source_log",
            "",
            "## Key Supporting Evidence",
            f"- Benchmark candidates: {', '.join(benchmark.get('benchmark_candidates', [])) if isinstance(benchmark, dict) else 'not provided'}",
            f"- Primary growth engine: {company_signals['primary_growth_engine']}",
            f"- Latest annual revenue: {annual.get('revenue', 'not provided')}",
            f"- Market awareness missing items: {', '.join(market_awareness.get('missing_items', [])) if isinstance(market_awareness, dict) else 'not provided'}",
            "",
            "## Key Objections",
            "- Benchmark weights are missing.",
            "- Benchmark-relative total return and risk are missing.",
            *([] if context_provided else ["- Portfolio context is missing."]),
            "- Individual ownership may duplicate existing index exposure.",
            "",
            "## Decision Rationale",
            company_signals["decision_rationales"]["bogle"],
            "",
            *render_decision_candidate_section(decision_candidate),
            *render_promotion_eligibility_section(promotion_eligibility),
            "## Decision",
            "Prefer Broad Index",
            "",
            "## Confidence Level",
            "Medium",
            "",
            "## Final Bogle Statement",
            f"{self.get_company_name()} may be an excellent company, but the Bogle-style default is to prefer broad index exposure unless benchmark-relative evidence and portfolio context justify a limited individual position.",
            "",
        ]

        return "\n".join(lines)
