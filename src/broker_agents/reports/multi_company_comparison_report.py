"""Multi-company comparison of independent investor-agent outputs."""

from pathlib import Path

import yaml

from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.backoffice.portfolio_context import merge_portfolio_context_into_pack
from broker_agents.calculators.bogle_benchmark_risk import (
    calculate_bogle_benchmark_risk,
)
from broker_agents.calculators.bogle_index_overlap import (
    calculate_bogle_index_overlap,
)
from broker_agents.calculators.decision_candidates import build_decision_candidate
from broker_agents.calculators.fisher_scuttlebutt import (
    build_fisher_scuttlebutt_checklist,
)
from broker_agents.calculators.intrinsic_value import (
    calculate_buffett_intrinsic_value_range,
)
from broker_agents.calculators.lynch_category_scoring import score_lynch_category
from broker_agents.calculators.munger_inversion import build_munger_inversion_matrix
from broker_agents.calculators.munger_incentives import (
    score_munger_incentives_and_stupidity,
)
from broker_agents.calculators.normalized_owner_earnings import (
    calculate_normalized_owner_earnings,
)
from broker_agents.calculators.owner_earnings import calculate_owner_earnings_snapshot
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
)
from broker_agents.calculators.valuation_guardrails import calculate_valuation_guardrails
from broker_agents.calculators.valuation_history import analyze_valuation_history
from broker_agents.reports.formatting import (
    format_millions,
    format_multiple,
    format_ratio_as_percent,
    format_yield,
)

INVESTORS = [
    "Warren Buffett",
    "Charlie Munger",
    "Philip Fisher",
    "Peter Lynch",
    "John Bogle",
]


def _load_pack(path: Path) -> dict:
    """Load a YAML pack, returning an empty dictionary when unavailable."""
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _read_text(path: Path) -> str:
    """Read text, returning an empty string when unavailable."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""


def _extract_summary_rows(summary_text: str) -> dict[str, dict[str, str]]:
    """Extract decisions and confidence from an agents-summary table."""
    rows: dict[str, dict[str, str]] = {}
    in_decision_table = False
    for line in summary_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("| Investor | Decision | Confidence |"):
            in_decision_table = True
            continue
        if in_decision_table and stripped.startswith("## "):
            break
        if not in_decision_table:
            continue
        if not stripped.startswith("|"):
            continue
        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if len(parts) < 4 or parts[0] == "---":
            continue
        if parts[0] in INVESTORS:
            rows[parts[0]] = {
                "decision": parts[1] or "Not found",
                "confidence": parts[2] or "Not found",
            }
    return rows


def _top_inversion_risk(pack: dict) -> dict[str, str]:
    """Return the first high-severity inversion risk, or the first risk."""
    matrix = build_munger_inversion_matrix(pack)
    if not matrix:
        return {
            "failure_mode": "Not found",
            "severity": "Not found",
            "what_would_reduce_the_risk": "Not found",
        }
    return next(
        (row for row in matrix if str(row.get("severity", "")).lower() == "high"),
        matrix[0],
    )


def _human_join(values: list[str]) -> str:
    """Join values for readable report prose."""
    if not values:
        return "No companies"
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return f"{', '.join(values[:-1])}, and {values[-1]}"


def generate_multi_company_comparison(
    tickers: list[str],
    outputs_root: Path,
    examples_root: Path,
    portfolio_context: dict | None = None,
) -> str:
    """Generate a non-ranking comparison across multiple company packs."""
    normalized_tickers = [ticker.strip().upper() for ticker in tickers if ticker.strip()]
    ticker_list_text = _human_join(normalized_tickers)
    companies: list[dict] = []

    for ticker in normalized_tickers:
        input_path = Path(examples_root) / f"{ticker.lower()}_input.yaml"
        output_dir = Path(outputs_root) / ticker
        summary_path = output_dir / f"{ticker.lower()}_agents_summary.md"
        pack = merge_portfolio_context_into_pack(
            _load_pack(input_path),
            portfolio_context or {},
        )
        identity = pack.get("company_identity", {})
        metadata = pack.get("metadata", {})
        company_name = str(
            identity.get("company_name")
            or metadata.get("company_name")
            or "Not found"
        )
        companies.append(
            {
                "ticker": ticker,
                "company_name": company_name,
                "input_path": input_path,
                "output_dir": output_dir,
                "exists": input_path.exists() and output_dir.exists(),
                "signals": extract_company_signals(pack),
                "owner_earnings": calculate_owner_earnings_snapshot(pack),
                "valuation": calculate_valuation_guardrails(pack),
                "intrinsic_value": calculate_buffett_intrinsic_value_range(pack),
                "valuation_history": analyze_valuation_history(pack),
                "normalized_owner_earnings": calculate_normalized_owner_earnings(pack),
                "inversion": _top_inversion_risk(pack),
                "munger_scoring": score_munger_incentives_and_stupidity(pack),
                "decisions": _extract_summary_rows(_read_text(summary_path)),
                "candidates": {
                    investor: build_decision_candidate(pack, investor)
                    for investor in ("buffett", "munger", "fisher", "lynch", "bogle")
                },
                "eligibility": {
                    investor: evaluate_promotion_eligibility(pack, investor)
                    for investor in ("buffett", "munger", "fisher", "lynch", "bogle")
                },
                "fisher_checklist": build_fisher_scuttlebutt_checklist(pack),
                "lynch_scoring": score_lynch_category(pack),
                "bogle_overlap": calculate_bogle_index_overlap(pack),
                "bogle_risk": calculate_bogle_benchmark_risk(pack),
            }
        )

    lines = [
        "# Multi-Company Independent Investor Agents Comparison",
        "",
        "## 1. Companies Compared",
        "",
        "| Ticker | Company | Input File | Output Directory | Exists |",
        "| --- | --- | --- | --- | --- |",
    ]
    for company in companies:
        lines.append(
            f"| {company['ticker']} | {company['company_name']} | "
            f"{company['input_path']} | {company['output_dir']} | "
            f"{'Yes' if company['exists'] else 'No'} |"
        )

    lines.extend(
        [
            "",
            "## 2. Important Disclaimer",
            "",
            "This is not a ranking, recommendation, vote, average score, or consensus. It compares independent agent outputs and company signals only.",
            "",
            "## 3. Business Model Signal Table",
            "",
            "| Ticker | Company | Business Model Type | Primary Growth Engine | Dominant Revenue Stream | Capex Profile | Major Capex Issue |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        signals = company["signals"]
        lines.append(
            f"| {company['ticker']} | {company['company_name']} | "
            f"{signals['business_model_type']} | {signals['primary_growth_engine']} | "
            f"{signals['dominant_revenue_stream']} | {signals['capex_profile']} | "
            f"{signals['major_capex_issue']} |"
        )

    lines.extend(
        [
            "",
            "## 4. Buffett Owner Earnings Table",
            "",
            "| Ticker | FCF Margin | Capex / OCF | Capex Intensity | Owner Earnings Quality |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        snapshot = company["owner_earnings"]
        lines.append(
            f"| {company['ticker']} | {format_ratio_as_percent(snapshot['fcf_margin'])} | "
            f"{format_ratio_as_percent(snapshot['capex_to_ocf'])} | "
            f"{snapshot['capex_intensity_label']} | "
            f"{snapshot['owner_earnings_quality_label']} |"
        )

    lines.extend(
        [
            "",
            "## 5. Buffett Valuation Guardrails Table",
            "",
            "| Ticker | P/FCF | FCF Yield | Valuation Status | Valuation Confidence |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        valuation = company["valuation"]
        lines.append(
            f"| {company['ticker']} | {format_multiple(valuation['p_fcf'])} | "
            f"{format_yield(valuation['fcf_yield'])} | "
            f"{valuation['valuation_status']} | {valuation['valuation_confidence']} |"
        )

    lines.extend(
        [
            "",
            "## 6. Buffett Intrinsic Value Range Comparison",
            "",
            "| Ticker | Intrinsic Value Low | Intrinsic Value Mid | Intrinsic Value High | Market Cap | Mid Margin of Safety | Valuation Gap Label | Confidence |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        intrinsic = company["intrinsic_value"]
        lines.append(
            f"| {company['ticker']} | "
            f"{format_millions(intrinsic['intrinsic_value_low'])} | "
            f"{format_millions(intrinsic['intrinsic_value_mid'])} | "
            f"{format_millions(intrinsic['intrinsic_value_high'])} | "
            f"{format_millions(intrinsic['market_cap'])} | "
            f"{format_ratio_as_percent(intrinsic['margin_of_safety_mid'])} | "
            f"{intrinsic['valuation_gap_label']} | "
            f"{intrinsic['intrinsic_value_confidence']} |"
        )

    lines.extend(
        [
            "",
            "## 7. Buffett Valuation History & Normalized Owner Earnings Comparison",
            "",
            "| Ticker | Current P/FCF | 5Y Median P/FCF | 10Y Median P/FCF | Valuation History Label | Normalized Owner Earnings | Durability Label | Confidence |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        history = company["valuation_history"]
        normalized = company["normalized_owner_earnings"]
        lines.append(
            f"| {company['ticker']} | {format_multiple(history['current_p_fcf'])} | "
            f"{format_multiple(history['p_fcf_5y_median'])} | "
            f"{format_multiple(history['p_fcf_10y_median'])} | "
            f"{history['valuation_history_label']} | "
            f"{format_millions(normalized['normalized_owner_earnings'])} | "
            f"{normalized['owner_earnings_durability_label']} | "
            f"{normalized['normalized_owner_earnings_confidence']} |"
        )

    lines.extend(
        [
            "",
            "## 8. Munger Top Inversion Risk Table",
            "",
            "| Ticker | Top Failure Mode | Severity | Risk-Reduction Evidence Needed |",
            "| --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        inversion = company["inversion"]
        lines.append(
            f"| {company['ticker']} | {inversion['failure_mode']} | "
            f"{inversion['severity']} | {inversion['what_would_reduce_the_risk']} |"
        )

    lines.extend(
        [
            "",
            "## 9. Munger Incentives & Hidden-Stupidity Comparison",
            "",
            "| Ticker | Business Model Type | Incentives Label | Capital Allocation Label | Hidden-Stupidity Label | Overall Munger Quality Score | Main Evidence Gap | Munger Candidate |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        scoring = company["munger_scoring"]
        main_gap = (
            scoring["evidence_gaps"][0]
            if scoring["evidence_gaps"]
            else "No material evidence gap recorded."
        )
        lines.append(
            f"| {company['ticker']} | {scoring['business_model_type']} | "
            f"{scoring['incentives_label']} | "
            f"{scoring['capital_allocation_label']} | "
            f"{scoring['hidden_stupidity_label']} | "
            f"{scoring['overall_munger_quality_score']}/5 | {main_gap} | "
            f"{company['candidates']['munger']['candidate_decision']} |"
        )

    decision_headers = " | ".join(
        f"{company['ticker']} Decision / Confidence" for company in companies
    )
    lines.extend(
        [
            "",
            "## 10. Investor Decisions Table",
            "",
            f"| Investor | {decision_headers} |",
            f"| --- | {' | '.join('---' for _ in companies)} |",
        ]
    )
    for investor in INVESTORS:
        cells: list[str] = []
        for company in companies:
            result = company["decisions"].get(
                investor,
                {"decision": "Not found", "confidence": "Not found"},
            )
            cells.append(f"{result['decision']} / {result['confidence']}")
        lines.append(f"| {investor} | {' | '.join(cells)} |")

    candidate_headers = " | ".join(
        f"{company['ticker']} Candidate" for company in companies
    )
    investor_keys = {
        "Warren Buffett": "buffett",
        "Charlie Munger": "munger",
        "Philip Fisher": "fisher",
        "Peter Lynch": "lynch",
        "John Bogle": "bogle",
    }
    lines.extend(
        [
            "",
            "## 11. Decision Candidate Comparison",
            "",
            f"| Investor | {candidate_headers} | Key Differentiation |",
            f"| --- | {' | '.join('---' for _ in companies)} | --- |",
        ]
    )
    for investor, investor_key in investor_keys.items():
        candidates = [
            company["candidates"][investor_key]["candidate_decision"]
            for company in companies
        ]
        blockers = [
            company["candidates"][investor_key]["decision_blockers"][0]
            for company in companies
        ]
        differentiation = "; ".join(
            f"{company['ticker']}: {blocker}"
            for company, blocker in zip(companies, blockers)
        )
        lines.append(
            f"| {investor} | {' | '.join(candidates)} | {differentiation} |"
        )

    eligibility_headers = " | ".join(
        f"{company['ticker']} Eligibility" for company in companies
    )
    lines.extend(
        [
            "",
            "## 12. Promotion Eligibility Comparison",
            "",
            f"| Investor | {eligibility_headers} | Key Reason |",
            f"| --- | {' | '.join('---' for _ in companies)} | --- |",
        ]
    )
    for investor, investor_key in investor_keys.items():
        eligibility_values = [
            company["eligibility"][investor_key]["promotion_eligibility"]
            for company in companies
        ]
        reasons = [
            company["eligibility"][investor_key]["eligibility_reasons"][0]
            for company in companies
        ]
        key_reason = "; ".join(
            f"{company['ticker']}: {reason}"
            for company, reason in zip(companies, reasons)
        )
        lines.append(
            f"| {investor} | {' | '.join(eligibility_values)} | {key_reason} |"
        )

    lines.extend(
        [
            "",
            "## 13. Fisher Scuttlebutt Readiness Comparison",
            "",
            "| Ticker | Business Model Type | Readiness Label | Top Priority Evidence | Main Scuttlebutt Gap |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        checklist = company["fisher_checklist"]
        top_item = (
            checklist["priority_items"][0]
            if checklist["priority_items"]
            else None
        )
        lines.append(
            f"| {company['ticker']} | {checklist['business_model_type']} | "
            f"{checklist['readiness_label']} | "
            f"{top_item['evidence_needed'] if top_item else 'No high-priority item'} | "
            f"{top_item['evidence_area'] if top_item else 'No high-priority gap'} |"
        )

    lines.extend(
        [
            "",
            "## 14. Lynch Category Scoring Comparison",
            "",
            "| Ticker | Business Model Type | Primary Category | Secondary Category | Category Confidence | Story Score | Growth Score | Valuation vs Growth Score | Cyclicality Score | Lynch Candidate |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        scoring = company["lynch_scoring"]
        lines.append(
            f"| {company['ticker']} | {scoring['business_model_type']} | "
            f"{scoring['primary_category']} | {scoring['secondary_category']} | "
            f"{scoring['category_confidence']} | {scoring['story_score']}/5 | "
            f"{scoring['growth_score']}/5 | "
            f"{scoring['valuation_vs_growth_score']}/5 | "
            f"{scoring['cyclicality_score']}/5 | "
            f"{company['candidates']['lynch']['candidate_decision']} |"
        )

    lines.extend(
        [
            "",
            "## 15. Lynch Growth & PEG Comparison",
            "",
            "| Ticker | Revenue CAGR 3Y | EPS CAGR 3Y | FCF CAGR 3Y | Forward EPS Growth | PEG Ratio | Growth Quality Label | Confidence | Lynch Candidate |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        growth = company["lynch_scoring"]["growth_peg_evidence"]
        lines.append(
            f"| {company['ticker']} | "
            f"{format_ratio_as_percent(growth['revenue_cagr_3y'])} | "
            f"{format_ratio_as_percent(growth['eps_cagr_3y'])} | "
            f"{format_ratio_as_percent(growth['fcf_cagr_3y'])} | "
            f"{format_ratio_as_percent(growth['forward_eps_growth'])} | "
            f"{format_multiple(growth['peg_ratio'])} | "
            f"{growth['growth_quality_label']} | "
            f"{growth['growth_data_confidence']} | "
            f"{company['candidates']['lynch']['candidate_decision']} |"
        )

    lines.extend(
        [
            "",
            "## 16. Bogle Index Overlap & Benchmark Risk Comparison",
            "",
            "| Ticker | Estimated Indirect Exposure | Current Total Exposure | Max Single-Stock Weight | Remaining Capacity | Overlap Label | Concentration Risk | Limited-Weight Candidate | Benchmark Risk Label | Bogle Candidate |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        overlap = company["bogle_overlap"]
        risk = company["bogle_risk"]
        lines.append(
            f"| {company['ticker']} | "
            f"{format_ratio_as_percent(overlap['estimated_indirect_exposure'])} | "
            f"{format_ratio_as_percent(overlap['current_total_exposure'])} | "
            f"{format_ratio_as_percent(overlap['maximum_single_stock_weight'])} | "
            f"{format_ratio_as_percent(overlap['remaining_allowed_single_stock_capacity'])} | "
            f"{overlap['overlap_label']} | {overlap['concentration_risk_label']} | "
            f"{'Yes' if overlap['limited_weight_candidate'] else 'No'} | "
            f"{risk['benchmark_risk_label']} | "
            f"{company['candidates']['bogle']['candidate_decision']} |"
        )

    lines.extend(
        [
            "",
            "## 17. Interpretation Notes",
            "",
            f"- {ticker_list_text} represent different detected business model types.",
            "- Similar decision labels do not mean similar investment cases.",
            "- Differences in capex profile, valuation guardrails, and inversion risks should be read before comparing decisions.",
            "- The system still uses deterministic rules and manual inputs.",
            "",
            "## 18. Recommended Next Improvements",
            "",
            "- Add more companies from different business models.",
            "- Add real source-driven market data.",
            "- Source-verify valuation history and normalized owner earnings.",
            "- Add peer comparison.",
            "- Add portfolio context for Bogle.",
            "- Collect and verify Fisher scuttlebutt checklist evidence by business model.",
            "- Collect and verify Lynch category evidence by business model.",
            "",
        ]
    )
    return "\n".join(lines)
