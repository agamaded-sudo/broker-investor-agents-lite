"""Cautious eligibility checks for candidate-to-final decision promotion."""

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
from broker_agents.calculators.owner_earnings import calculate_owner_earnings_snapshot
from broker_agents.calculators.normalized_owner_earnings import (
    calculate_normalized_owner_earnings,
)
from broker_agents.calculators.valuation_guardrails import calculate_valuation_guardrails
from broker_agents.calculators.valuation_history import analyze_valuation_history


def _result(
    investor: str,
    candidate: dict,
    eligibility: str,
    reasons: list[str],
    required_evidence: list[str],
    blocking_conditions: list[str],
    human_review_notes: list[str],
) -> dict:
    """Build a consistent promotion eligibility result."""
    return {
        "investor": investor,
        "current_final_decision": candidate["current_decision"],
        "decision_candidate": candidate["candidate_decision"],
        "promotion_eligibility": eligibility,
        "auto_promotion_allowed": False,
        "eligibility_reasons": list(dict.fromkeys(reasons)),
        "required_evidence": list(dict.fromkeys(required_evidence)),
        "blocking_conditions": list(dict.fromkeys(blocking_conditions)),
        "human_review_notes": list(dict.fromkeys(human_review_notes)),
    }


def _buffett_eligibility(pack: dict, candidate: dict) -> dict:
    owner = calculate_owner_earnings_snapshot(pack)
    valuation = calculate_valuation_guardrails(pack)
    intrinsic_value = calculate_buffett_intrinsic_value_range(pack)
    history = analyze_valuation_history(pack)
    normalized = calculate_normalized_owner_earnings(pack)
    status = valuation["valuation_status"]
    quality = owner["owner_earnings_quality_label"]
    gap_label = intrinsic_value["valuation_gap_label"]
    reasons = [
        f"Owner earnings quality is {quality}.",
        f"Valuation status is {status}.",
        f"Preliminary intrinsic value gap is {gap_label}.",
    ]
    blockers = list(candidate["decision_blockers"])

    if (
        candidate["candidate_decision"] == "Buy Gradually Candidate"
        and quality == "strong"
        and gap_label in {"moderately undervalued", "materially undervalued"}
    ):
        eligibility = "Conditionally Eligible"
        required = [
            "Intrinsic value range validation.",
            "Margin of safety validation.",
            "Valuation history.",
            "Owner earnings durability.",
        ]
        notes = [
            "Human review should confirm that intrinsic value supports gradual accumulation.",
            "The candidate must not replace the official final decision automatically.",
        ]
    elif gap_label == "overvalued":
        eligibility = "Needs More Evidence"
        required = [
            "Lower market valuation or higher validated intrinsic value.",
            "Stronger margin of safety.",
            "Normalized owner earnings.",
        ]
        notes = [
            "Human review should wait for improved valuation or stronger normalized cash evidence."
        ]
    else:
        eligibility = "Needs More Evidence"
        required = [
            "Established valuation guardrails.",
            "Intrinsic value range validation.",
            "Normalized owner earnings.",
        ]
        notes = ["Human review requires a more complete valuation record."]
    if "placeholder" in history["valuation_history_confidence"].lower():
        required.extend(
            [
                "Valuation history source verification.",
                "5Y/10Y valuation data validation.",
            ]
        )
    if normalized["normalized_owner_earnings_confidence"] in {"Low", "Medium"}:
        required.append("5-10 year free cash flow history.")
    required.extend(normalized["evidence_gaps"])
    return _result("buffett", candidate, eligibility, reasons, required, blockers, notes)


def _munger_eligibility(pack: dict, candidate: dict) -> dict:
    matrix = build_munger_inversion_matrix(pack)
    scoring = score_munger_incentives_and_stupidity(pack)
    top_risk = next(
        (row for row in matrix if str(row.get("severity", "")).lower() == "high"),
        matrix[0],
    )
    reasons = [
        f"Top inversion risk is {top_risk['failure_mode']}.",
        f"Top inversion risk severity is {top_risk['severity']}.",
        f"Hidden-stupidity protection score is {scoring['hidden_stupidity_risk_score']}/5.",
    ]
    required = list(scoring["required_evidence"])
    if scoring["incentives_score"] == 3:
        required.extend(
            [
                "Management incentives.",
                "Insider ownership.",
                "Compensation structure.",
                "Capital allocation rationality.",
            ]
        )
    if (
        "Buy Gradually" in candidate["candidate_decision"]
        and scoring["hidden_stupidity_risk_score"] >= 3
    ):
        eligibility = "Conditionally Eligible"
        notes = [
            "Human review should confirm that high-severity inversion risks are adequately reduced."
        ]
    else:
        eligibility = "Needs More Evidence"
        notes = [
            "Human review should not consider promotion while the candidate remains wait-oriented."
        ]
    return _result(
        "munger",
        candidate,
        eligibility,
        reasons,
        required,
        candidate["decision_blockers"],
        notes,
    )


def _fisher_eligibility(pack: dict, candidate: dict) -> dict:
    checklist = build_fisher_scuttlebutt_checklist(pack)
    required = [
        item["evidence_needed"] for item in checklist["priority_items"]
    ]
    eligibility_by_readiness = {
        "Not Ready": "Needs More Evidence",
        "Partially Ready": "Conditionally Eligible",
        "Ready for Fisher Review": "Eligible for Human Review",
    }
    return _result(
        "fisher",
        candidate,
        eligibility_by_readiness[checklist["readiness_label"]],
        [
            f"Fisher scuttlebutt readiness is {checklist['readiness_label']}.",
            f"Evidence must fit the {checklist['business_model_type']} business model.",
        ],
        required,
        candidate["decision_blockers"],
        [
            "Human review requires customer, product, and competitive or ecosystem evidence.",
            "Auto-promotion remains disabled.",
        ],
    )


def _lynch_eligibility(pack: dict, candidate: dict) -> dict:
    scoring = score_lynch_category(pack)
    growth_peg = scoring["growth_peg_evidence"]
    if (
        candidate["candidate_decision"] == "Buy Gradually Candidate"
        and scoring["valuation_vs_growth_score"] >= 3
    ):
        eligibility = "Conditionally Eligible"
        reasons = [
            f"The primary Lynch category is {scoring['primary_category']}.",
            "The valuation-versus-growth score is acceptable for conditional review.",
        ]
        notes = [
            "Human review should test category fit and growth durability before any final change."
        ]
    else:
        eligibility = "Needs More Evidence"
        reasons = [
            "The candidate remains follow/watch oriented.",
            "Valuation or growth durability is not established.",
        ]
        notes = ["Human review requires stronger story confirmation and valuation discipline."]
    required = [
        "Growth and PEG provider source and methodology validation.",
        "Category-specific growth proof.",
        "Earnings durability.",
    ]
    if growth_peg["peg_ratio"] is None:
        required.append("PEG calculation.")
    if "fixture" in growth_peg["growth_data_confidence"].lower():
        required.extend(
            [
                "EPS and revenue CAGR methodology validation.",
                "Forward estimate source validation.",
            ]
        )
    if scoring["business_model_type"] in {"semiconductor", "industrial", "financial"}:
        required.append("Normalized cycle earnings.")
    return _result(
        "lynch",
        candidate,
        eligibility,
        reasons,
        required,
        candidate["decision_blockers"],
        notes,
    )


def _bogle_eligibility(pack: dict, candidate: dict) -> dict:
    overlap = calculate_bogle_index_overlap(pack)
    benchmark = calculate_bogle_benchmark_risk(pack)
    context_missing = not overlap["portfolio_context_provided"]
    reasons = [
        "Portfolio context is missing." if context_missing else "Portfolio context is available.",
        f"Index overlap is {overlap['overlap_label']}.",
        f"Concentration risk is {overlap['concentration_risk_label']}.",
        f"Benchmark risk data quality is {benchmark['risk_data_quality']}.",
    ]
    limited_weight_candidate = (
        candidate["candidate_decision"]
        == "Individual Stock Acceptable at Limited Weight Candidate"
    )
    required = [
        *overlap["required_evidence"],
        *benchmark["missing_benchmark_evidence"],
    ] if not context_missing else [
        "Portfolio context.",
        "Index overlap.",
        "Current indirect exposure.",
        "Maximum single-stock weight.",
        "Benchmark-relative risk.",
    ]
    if overlap["concentration_risk_label"] == "high concentration risk":
        eligibility = "Needs More Evidence"
    elif limited_weight_candidate:
        eligibility = "Conditionally Eligible"
    else:
        eligibility = "Needs More Evidence"
    return _result(
        "bogle",
        candidate,
        eligibility,
        reasons,
        required,
        candidate["decision_blockers"],
        [
            "Human review must evaluate the candidate within the investor's complete portfolio.",
            "Broad index exposure remains the final decision and auto-promotion is disabled.",
        ],
    )


def evaluate_promotion_eligibility(pack: dict, investor: str) -> dict:
    """Evaluate whether a candidate is ready for cautious human promotion review."""
    investor = investor.lower().strip()
    candidate = build_decision_candidate(pack, investor)
    if candidate["candidate_decision"] == candidate["current_decision"]:
        return _result(
            investor,
            candidate,
            "Not Eligible",
            ["Candidate and final decision are already the same."],
            [],
            candidate["decision_blockers"],
            ["No promotion is needed; auto-promotion remains disabled."],
        )
    if investor == "buffett":
        return _buffett_eligibility(pack, candidate)
    if investor == "munger":
        return _munger_eligibility(pack, candidate)
    if investor == "fisher":
        return _fisher_eligibility(pack, candidate)
    if investor == "lynch":
        return _lynch_eligibility(pack, candidate)
    if investor == "bogle":
        return _bogle_eligibility(pack, candidate)
    raise ValueError(f"Unsupported investor '{investor}'.")


def render_promotion_eligibility_section(eligibility: dict) -> list[str]:
    """Render promotion eligibility as deterministic Markdown lines."""
    return [
        "## Promotion Eligibility",
        f"- Promotion Eligibility: {eligibility['promotion_eligibility']}",
        f"- Auto-Promotion Allowed: {'Yes' if eligibility['auto_promotion_allowed'] else 'No'}",
        "- Eligibility Reasons:",
        *[f"  - {item}" for item in eligibility["eligibility_reasons"]],
        "- Required Evidence:",
        *[f"  - {item}" for item in eligibility["required_evidence"]],
        "- Blocking Conditions:",
        *[f"  - {item}" for item in eligibility["blocking_conditions"]],
        "- Human Review Notes:",
        *[f"  - {item}" for item in eligibility["human_review_notes"]],
        "",
    ]
