"""Deterministic provisional decision candidates for investor agents."""

from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.calculators.bogle_benchmark_risk import (
    calculate_bogle_benchmark_risk,
)
from broker_agents.calculators.bogle_index_overlap import (
    calculate_bogle_index_overlap,
)
from broker_agents.calculators.munger_inversion import build_munger_inversion_matrix
from broker_agents.calculators.munger_incentives import (
    score_munger_incentives_and_stupidity,
)
from broker_agents.calculators.fisher_scuttlebutt import (
    build_fisher_scuttlebutt_checklist,
)
from broker_agents.calculators.intrinsic_value import (
    calculate_buffett_intrinsic_value_range,
)
from broker_agents.calculators.lynch_category_scoring import score_lynch_category
from broker_agents.calculators.normalized_owner_earnings import (
    calculate_normalized_owner_earnings,
)
from broker_agents.calculators.owner_earnings import calculate_owner_earnings_snapshot
from broker_agents.calculators.valuation_guardrails import calculate_valuation_guardrails
from broker_agents.calculators.valuation_history import analyze_valuation_history

CURRENT_DECISIONS = {
    "buffett": "Wait for Better Price / Complete Intrinsic Value Work",
    "munger": "Buy Gradually / Wait for Better Evidence on AI Capex Returns",
    "fisher": "Needs More Scuttlebutt / Watch Closely",
    "lynch": "Follow / Watch",
    "bogle": "Prefer Broad Index",
}


def _result(
    investor: str,
    candidate_decision: str,
    candidate_confidence: str,
    blockers: list[str],
    positive: list[str],
    negative: list[str],
    rationale: str,
) -> dict:
    """Build a consistent candidate result."""
    return {
        "investor": investor,
        "current_decision": CURRENT_DECISIONS[investor],
        "candidate_decision": candidate_decision,
        "candidate_confidence": candidate_confidence,
        "decision_blockers": list(dict.fromkeys(blockers)),
        "positive_drivers": list(dict.fromkeys(positive)),
        "negative_drivers": list(dict.fromkeys(negative)),
        "rationale": rationale,
    }


def _buffett_candidate(pack: dict, signals: dict, valuation: dict) -> dict:
    owner = calculate_owner_earnings_snapshot(pack)
    intrinsic_value = calculate_buffett_intrinsic_value_range(pack)
    history = analyze_valuation_history(pack)
    normalized = calculate_normalized_owner_earnings(pack)
    capex_intensity = owner["capex_intensity_label"]
    gap_label = intrinsic_value["valuation_gap_label"]
    blockers = [
        "Preliminary intrinsic value range requires validation.",
        "Historical valuation ranges are missing.",
    ]
    positive = [f"Detected business model: {signals['business_model_type']}."]
    negative: list[str] = []

    history_label = history["valuation_history_label"]
    durability = normalized["owner_earnings_durability_label"]
    if (
        history_label == "below historical range"
        and durability == "durable / evidence-backed"
        and gap_label in {"moderately undervalued", "materially undervalued"}
    ):
        candidate = "Buy Gradually Candidate"
        positive.extend(
            [
                "Owner earnings quality is strong.",
                f"Preliminary intrinsic value indicates {gap_label}.",
            ]
        )
        rationale = (
            "The candidate improves on the current decision because preliminary owner earnings "
            "and intrinsic value indicate a positive valuation gap, while validation remains open."
        )
    elif history_label == "above historical range" or gap_label == "overvalued":
        candidate = "Wait Candidate"
        negative.append(
            f"Valuation history is {history_label}; intrinsic value gap is {gap_label}."
        )
        blockers.append("Margin of safety is not established.")
        rationale = (
            "The candidate remains cautious because historical valuation evidence and/or "
            "the preliminary intrinsic value midpoint do not establish a margin of safety."
        )
    elif history_label == "near historical range" and gap_label == "near fair value":
        candidate = "Watch / Fair Value Candidate"
        blockers.append("A clear margin of safety is not established.")
        rationale = (
            "The preliminary midpoint is near fair value, so the candidate remains watch-oriented "
            "until a larger validated margin of safety appears."
        )
    else:
        candidate = "Complete Valuation Work Candidate"
        blockers.append("Intrinsic value is not established.")
        rationale = "The candidate remains provisional because valuation evidence is insufficient."

    if capex_intensity == "high":
        blockers.append(
            "Capex intensity requires normalization before owner earnings confidence improves."
        )
        negative.append(f"Capex profile is {signals['capex_profile']}.")
    if signals["business_model_type"] == "semiconductor":
        blockers.append("Cycle-normalized earnings are not established.")
        negative.append("Semiconductor cycle risk may distort current owner earnings.")
    blockers.extend(str(gap) for gap in signals["major_data_gaps"][:2])
    blockers.extend(history["evidence_gaps"])
    blockers.extend(normalized["evidence_gaps"])
    return _result("buffett", candidate, "Medium", blockers, positive, negative, rationale)


def _munger_candidate(pack: dict, signals: dict, valuation: dict) -> dict:
    matrix = build_munger_inversion_matrix(pack)
    scoring = score_munger_incentives_and_stupidity(pack)
    top_risk = next(
        (row for row in matrix if str(row.get("severity", "")).lower() == "high"),
        matrix[0],
    )
    blockers = [
        f"Top inversion risk requires evidence: {top_risk['failure_mode']}.",
        *scoring["evidence_gaps"][:4],
    ]
    positive = [
        f"Primary growth engine: {signals['primary_growth_engine']}.",
        f"Business model is classified as {signals['business_model_type']}.",
        f"Overall Munger quality score is {scoring['overall_munger_quality_score']}/5.",
    ]
    negative = [f"Top inversion risk severity is {top_risk['severity']}."]

    if (
        scoring["hidden_stupidity_risk_score"] <= 2
        or (
            top_risk["severity"] == "high"
            and valuation["valuation_status"] == "demanding"
        )
    ):
        candidate = "Wait / Avoid Overpaying Candidate"
        blockers.append("Demanding valuation leaves little room for inversion risks.")
        rationale = (
            "The candidate is more cautious than the current decision because a high-severity "
            "failure mode coincides with demanding valuation."
        )
    elif (
        scoring["hidden_stupidity_risk_score"] >= 3
        and valuation["valuation_status"] != "demanding"
    ):
        candidate = "Buy Gradually Candidate with Evidence Conditions"
        rationale = (
            "The candidate permits gradual interest only if the identified inversion risks are "
            "reduced by stronger operating and valuation evidence."
        )
    else:
        candidate = "Wait / Avoid Overpaying Candidate"
        rationale = (
            "The candidate remains cautious because incentives, capital allocation, or "
            "hidden-stupidity protection are not sufficiently evidenced."
        )

    if signals["business_model_type"] == "semiconductor":
        blockers.extend(
            [
                "Cycle-normalized earnings evidence is needed.",
                "Customer concentration evidence is needed.",
            ]
        )
    return _result("munger", candidate, "Medium", blockers, positive, negative, rationale)


def _fisher_candidate(pack: dict, signals: dict) -> dict:
    model = signals["business_model_type"]
    checklist = build_fisher_scuttlebutt_checklist(pack)
    blockers = [
        f"{item['evidence_area']}: {item['evidence_needed']}"
        for item in checklist["priority_items"]
        if item["blocks_fisher_upgrade"]
    ]
    blockers.extend(str(gap) for gap in signals["major_data_gaps"][:3])
    positive = [
        f"Primary growth engine: {signals['primary_growth_engine']}.",
        f"Scuttlebutt readiness: {checklist['readiness_label']}.",
    ]
    negative = [
        f"{len(checklist['priority_items'])} high-priority scuttlebutt items remain open."
    ]
    candidate_by_readiness = {
        "Not Ready": "Needs More Scuttlebutt Candidate",
        "Partially Ready": "Watch Closely / Partial Scuttlebutt Candidate",
        "Ready for Fisher Review": "Fisher Review Candidate",
    }
    return _result(
        "fisher",
        candidate_by_readiness[checklist["readiness_label"]],
        "Medium",
        blockers,
        positive,
        negative,
        (
            f"The {checklist['readiness_label']} checklist status determines the provisional "
            f"candidate for the {model} business model; the official Fisher decision is unchanged."
        ),
    )


def _lynch_candidate(pack: dict, signals: dict, valuation: dict) -> dict:
    model = signals["business_model_type"]
    scoring = score_lynch_category(pack)
    blockers = list(scoring["evidence_gaps"])
    positive = [
        f"Investment story centers on {signals['primary_growth_engine'].lower()}.",
        f"Dominant revenue stream: {signals['dominant_revenue_stream']}.",
        f"Lynch category is {scoring['primary_category']} with "
        f"{scoring['secondary_category']} characteristics.",
    ]
    negative: list[str] = []
    growth_peg = scoring["growth_peg_evidence"]
    peg = growth_peg["peg_ratio"]
    growth_values = [
        growth_peg["revenue_cagr_3y"],
        growth_peg["eps_cagr_3y"],
        growth_peg["fcf_cagr_3y"],
    ]
    strong_growth = any(value is not None and value >= 0.12 for value in growth_values)
    if peg is not None:
        if peg <= 1.5 and strong_growth:
            positive.append(
                f"PEG is {peg:.2f}, supported by strong reported growth evidence."
            )
        elif peg <= 2.5:
            positive.append(f"PEG is {peg:.2f}, a moderate valuation-versus-growth signal.")
        else:
            negative.append(
                f"PEG is {peg:.2f}, indicating a demanding valuation relative to growth."
            )
    if "cycle-sensitive" in growth_peg["growth_quality_label"].lower():
        negative.append("Exceptional growth remains cycle-sensitive and requires normalization.")
    if (
        scoring["primary_category"] == "Hybrid"
        and any(
            category in scoring["secondary_category"]
            for category in ("Stalwart", "Fast Grower")
        )
        and valuation["valuation_status"] == "reasonable"
        and scoring["valuation_vs_growth_score"] >= 3
    ):
        candidate = "Buy Gradually Candidate"
        rationale = (
            "The category is a supported hybrid and preliminary valuation-versus-growth "
            "guardrails are acceptable, subject to the listed category evidence gaps."
        )
    else:
        candidate = "Follow / Watch Candidate"
        negative.append(f"Valuation status is {valuation['valuation_status']}.")
        if model in {"semiconductor", "industrial", "financial"}:
            negative.append(
                f"Cyclicality score is {scoring['cyclicality_score']}/5 and requires normalized evidence."
            )
        rationale = (
            "The candidate remains aligned with follow/watch because valuation, category evidence, "
            "or cycle-normalized growth is not strong enough to support an upgrade."
        )
    return _result("lynch", candidate, "Medium", blockers, positive, negative, rationale)


def _bogle_candidate(pack: dict, signals: dict) -> dict:
    overlap = calculate_bogle_index_overlap(pack)
    benchmark = calculate_bogle_benchmark_risk(pack)
    context_missing = not overlap["portfolio_context_provided"]
    blockers = list(overlap["required_evidence"])
    blockers.extend(benchmark["missing_benchmark_evidence"])
    positive = ["Broad index alternatives remain available at low cost."]
    negative = [
        f"Index overlap is {overlap['overlap_label']}.",
        f"Concentration risk is {overlap['concentration_risk_label']}.",
    ]
    if signals["business_model_type"] in {"semiconductor", "industrial", "financial"}:
        negative.append("Individual-stock volatility and cycle risk may exceed broad index exposure.")
    if context_missing:
        candidate = "Portfolio Context Required Candidate"
        rationale = (
            "The candidate differs from the broad-index final decision by identifying portfolio "
            "context as the immediate prerequisite before any limited individual-stock exception."
        )
    elif overlap["concentration_risk_label"] == "high concentration risk":
        candidate = "Prefer Broad Index Candidate"
        rationale = (
            "Current direct and indirect exposure is at or above the single-stock guardrail, "
            "so no separate limited-weight exception is supported."
        )
    elif overlap["limited_weight_candidate"]:
        candidate = "Individual Stock Acceptable at Limited Weight Candidate"
        positive.extend(
            [
                f"Index core weight is {overlap['index_core_weight']:.1%}.",
                "Satellite positions are allowed.",
                f"Current total exposure is {overlap['current_total_exposure']:.1%}, below the "
                f"{overlap['maximum_single_stock_weight']:.1%} single-stock limit.",
            ]
        )
        rationale = (
            "The supplied portfolio has a sufficient index core, permits satellite positions, "
            "and has current exposure below the single-stock limit; a limited-weight exception "
            "is therefore a candidate, subject to sizing and overlap checks."
        )
    else:
        candidate = "Prefer Broad Index Candidate"
        blockers.append(
            "Portfolio constraints do not currently support a limited-weight exception."
        )
        rationale = (
            "The candidate retains the broad-index default because the supplied portfolio "
            "constraints do not pass the limited-weight conditions."
        )
    confidence = "Low" if benchmark["risk_data_quality"] == "Incomplete" else "Medium"
    return _result("bogle", candidate, confidence, blockers, positive, negative, rationale)


def build_decision_candidate(pack: dict, investor: str) -> dict:
    """Build a provisional, investor-specific decision candidate."""
    investor = investor.lower().strip()
    if investor not in CURRENT_DECISIONS:
        supported = ", ".join(CURRENT_DECISIONS)
        raise ValueError(f"Unsupported investor '{investor}'. Supported investors: {supported}.")

    signals = extract_company_signals(pack)
    valuation = calculate_valuation_guardrails(pack)
    if investor == "buffett":
        return _buffett_candidate(pack, signals, valuation)
    if investor == "munger":
        return _munger_candidate(pack, signals, valuation)
    if investor == "fisher":
        return _fisher_candidate(pack, signals)
    if investor == "lynch":
        return _lynch_candidate(pack, signals, valuation)
    return _bogle_candidate(pack, signals)


def render_decision_candidate_section(candidate: dict) -> list[str]:
    """Render a candidate result as deterministic Markdown lines."""
    positive = candidate["positive_drivers"] or ["None identified."]
    negative = candidate["negative_drivers"] or ["None identified."]
    blockers = candidate["decision_blockers"] or ["None identified."]
    return [
        "## Decision Candidate Layer",
        f"- Current Decision: {candidate['current_decision']}",
        f"- Candidate Decision: {candidate['candidate_decision']}",
        f"- Candidate Confidence: {candidate['candidate_confidence']}",
        "- Positive Drivers:",
        *[f"  - {item}" for item in positive],
        "- Negative Drivers:",
        *[f"  - {item}" for item in negative],
        "- Decision Blockers:",
        *[f"  - {item}" for item in blockers],
        f"- Candidate Rationale: {candidate['rationale']}",
        "",
    ]
