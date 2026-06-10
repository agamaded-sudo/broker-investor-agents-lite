"""Deterministic Peter Lynch category scoring by business model."""

from typing import Any

from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.calculators.valuation_guardrails import (
    calculate_valuation_guardrails,
)

CATEGORIES = (
    "Slow Grower",
    "Stalwart",
    "Fast Grower",
    "Cyclical",
    "Turnaround",
    "Asset Play",
    "Hybrid",
    "Unclear",
)


def _to_float(value: Any) -> float | None:
    """Convert a value to a number when possible."""
    if value in (None, "", "unavailable", "placeholder_unavailable"):
        return None
    if isinstance(value, str):
        value = value.strip().rstrip("%")
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number / 100 if number > 1 and number <= 100 else number


def _to_multiple(value: Any) -> float | None:
    """Convert valuation multiples without percentage normalization."""
    if value in (None, "", "unavailable", "placeholder_unavailable"):
        return None
    if isinstance(value, str):
        value = value.strip().rstrip("x")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _growth_values(value: Any, key: str = "") -> list[float]:
    """Collect numeric values whose field names describe growth."""
    values: list[float] = []
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            values.extend(_growth_values(child_value, str(child_key).lower()))
    elif isinstance(value, list):
        for item in value:
            values.extend(_growth_values(item, key))
    elif "growth" in key or "cagr" in key:
        number = _to_float(value)
        if number is not None:
            values.append(number)
    return values


def _annual_financials(pack: dict) -> dict:
    """Return the latest annual financial record."""
    financials = pack.get("financial_statements_summary", {})
    annual = financials.get("annual", {})
    if isinstance(annual, dict):
        return annual
    income_rows = financials.get("income_statement", [])
    return income_rows[0] if isinstance(income_rows, list) and income_rows else {}


def _growth_peg_evidence(pack: dict) -> dict:
    """Return normalized growth and PEG evidence with conservative gaps."""
    data = pack.get("growth_peg_analysis", {})
    if not isinstance(data, dict):
        data = {}
    fields = {
        key: _to_float(data.get(key))
        for key in (
            "revenue_cagr_3y",
            "revenue_cagr_5y",
            "eps_cagr_3y",
            "eps_cagr_5y",
            "fcf_cagr_3y",
            "fcf_cagr_5y",
            "forward_revenue_growth",
            "forward_eps_growth",
        )
    }
    fields["current_pe"] = _to_multiple(data.get("current_pe"))
    fields["peg_ratio"] = _to_multiple(data.get("peg_ratio"))
    gaps = [
        f"{field} is missing."
        for field, value in fields.items()
        if value is None
    ]
    confidence = str(data.get("growth_data_confidence") or "not established")
    if "fixture" in confidence.lower():
        gaps.extend(
            [
                "Growth and PEG provider source validation.",
                "Revenue, EPS, and FCF CAGR methodology validation.",
                "Forward estimate source validation.",
            ]
        )
    return {
        **fields,
        "growth_quality_label": str(
            data.get("growth_quality_label") or "not established"
        ),
        "growth_data_confidence": confidence,
        "evidence_gaps": gaps,
    }


def _growth_score(pack: dict, model: str) -> tuple[int, list[str]]:
    """Score reported growth evidence and return related evidence gaps."""
    growth_peg = _growth_peg_evidence(pack)
    cagr_values = [
        growth_peg[key]
        for key in (
            "revenue_cagr_3y",
            "revenue_cagr_5y",
            "eps_cagr_3y",
            "eps_cagr_5y",
            "fcf_cagr_3y",
            "fcf_cagr_5y",
        )
        if growth_peg[key] is not None
    ]
    if cagr_values:
        maximum = max(cagr_values)
        if maximum >= 0.25:
            return 5, growth_peg["evidence_gaps"]
        if maximum >= 0.12:
            return 4, growth_peg["evidence_gaps"]
        if maximum >= 0.05:
            return 3, growth_peg["evidence_gaps"]
        return 2, growth_peg["evidence_gaps"]

    values = _growth_values(
        {
            "quarterly": pack.get("financial_statements_summary", {}).get("quarterly", {}),
            "kpis": pack.get("sector_specific_operating_kpis", {}),
            "growth_drivers": pack.get("growth_drivers", {}),
        }
    )
    gaps: list[str] = []
    if values:
        maximum = max(values)
        if maximum >= 0.25:
            return 5, gaps
        if maximum >= 0.12:
            return 4, gaps
        if maximum >= 0.05:
            return 3, gaps
        return 2, gaps
    gaps.append("Category-specific historical revenue, EPS, and operating-income growth proof.")
    if model in {"software_cloud", "consumer_ecosystem", "semiconductor"}:
        return 3, gaps
    return 2, gaps


def _valuation_score(pack: dict) -> tuple[int, list[str]]:
    """Score valuation guardrails in relation to the growth story."""
    growth_peg = _growth_peg_evidence(pack)
    peg = growth_peg["peg_ratio"]
    if peg is not None:
        gaps = growth_peg["evidence_gaps"]
        if peg <= 1.5:
            return 5, gaps
        if peg <= 2.5:
            return 3, gaps
        return 2, gaps
    status = calculate_valuation_guardrails(pack)["valuation_status"]
    if status == "potentially attractive":
        return 5, []
    if status == "reasonable":
        return 4, ["PEG ratio or explicit valuation-versus-growth evidence."]
    if status == "demanding":
        return 2, ["PEG ratio and evidence that growth supports the demanding valuation."]
    return 1, ["PEG ratio, valuation history, and valuation-versus-growth evidence."]


def _balance_sheet_score(pack: dict) -> tuple[int, list[str]]:
    """Score simple cash, debt, operating cash flow, and free cash flow evidence."""
    annual = _annual_financials(pack)
    cash = _to_float(annual.get("cash_and_short_term_investments"))
    debt = _to_float(annual.get("long_term_debt"))
    ocf = _to_float(annual.get("operating_cash_flow"))
    fcf = _to_float(annual.get("free_cash_flow"))
    present = sum(value is not None for value in (cash, debt, ocf, fcf))
    if present == 4 and fcf is not None and fcf > 0:
        return (5 if cash is not None and debt is not None and cash >= debt else 4), []
    if present >= 2:
        return 3, ["Complete cash, debt, operating cash flow, and free cash flow history."]
    return 1, ["Cash, debt, operating cash flow, and free cash flow evidence."]


def _cyclicality_score(model: str) -> int:
    """Return business-model cyclicality on a 0-to-5 scale."""
    return {
        "software_cloud": 1,
        "consumer_ecosystem": 3,
        "semiconductor": 5,
        "retail": 3,
        "payments_network": 1,
        "industrial": 5,
        "financial": 4,
        "generic": 2,
    }[model]


def _category_profile(model: str, growth_score: int) -> tuple[str, str, dict[str, int]]:
    """Build category labels and scores from the detected business model."""
    scores = {category: 0 for category in CATEGORIES}
    profiles = {
        "software_cloud": ("Hybrid", "Stalwart / Fast Grower", {"Hybrid": 5, "Stalwart": 5, "Fast Grower": 4}),
        "consumer_ecosystem": ("Hybrid", "Stalwart / Slow Grower", {"Hybrid": 5, "Stalwart": 5, "Slow Grower": 3}),
        "semiconductor": ("Hybrid", "Fast Grower / Cyclical", {"Hybrid": 5, "Fast Grower": 5, "Cyclical": 5}),
        "retail": ("Hybrid", "Stalwart / Cyclical", {"Hybrid": 4, "Stalwart": 4, "Cyclical": 3}),
        "payments_network": ("Stalwart", "Fast Grower", {"Stalwart": 5, "Fast Grower": 4, "Hybrid": 4}),
        "industrial": ("Cyclical", "Stalwart", {"Cyclical": 5, "Stalwart": 3, "Hybrid": 3}),
        "financial": ("Cyclical", "Stalwart", {"Cyclical": 4, "Stalwart": 3, "Hybrid": 3}),
        "generic": ("Unclear", "Unclear", {"Unclear": 5}),
    }
    primary, secondary, additions = profiles[model]
    scores.update(additions)
    if growth_score <= 2 and model in {"consumer_ecosystem", "retail"}:
        scores["Slow Grower"] = max(scores["Slow Grower"], 4)
    return primary, secondary, scores


def _model_evidence_gaps(model: str) -> list[str]:
    """Return category-specific evidence gaps."""
    return {
        "software_cloud": [
            "Recurring revenue, retention, and cloud or AI margin durability.",
            "EPS and free-cash-flow growth over 3, 5, and 10 years.",
        ],
        "consumer_ecosystem": [
            "Services growth durability, installed-base trends, and product replacement cycle.",
            "EPS CAGR and PEG confirmation.",
        ],
        "semiconductor": [
            "Cycle-normalized earnings and valuation versus the semiconductor cycle.",
            "Customer concentration, inventory, capacity, and demand durability.",
        ],
        "retail": ["Same-store sales, customer traffic, store economics, and inventory discipline."],
        "payments_network": ["Payment volume, cross-border volume, take rate, and network growth."],
        "industrial": ["Backlog, orders, utilization, margins, and cycle-normalized earnings."],
        "financial": ["Credit quality, book value quality, funding costs, and cycle-normalized earnings."],
        "generic": ["A clear investment story, category-specific growth proof, and valuation evidence."],
    }[model]


def _follow_up_indicators(model: str) -> list[str]:
    """Return business-model-specific Lynch follow-up indicators."""
    return {
        "software_cloud": ["Recurring revenue growth", "Retention", "Cloud or AI margins", "EPS growth", "FCF growth", "PEG"],
        "consumer_ecosystem": ["Installed base", "Services growth", "Replacement cycle", "EPS growth", "FCF growth", "PEG"],
        "semiconductor": ["Data-center demand", "Inventory and capacity", "Customer concentration", "Normalized earnings", "FCF growth", "Valuation versus cycle"],
        "retail": ["Same-store sales", "Customer traffic", "Store count", "Inventory turns", "Operating margin"],
        "payments_network": ["Payment volume", "Cross-border volume", "Take rate", "EPS growth", "Network acceptance"],
        "industrial": ["Orders", "Backlog", "Utilization", "Operating margin", "Cycle position"],
        "financial": ["Credit quality", "Book value", "Funding costs", "Capital strength", "Earnings quality"],
        "generic": ["Revenue growth", "EPS growth", "FCF growth", "Valuation versus growth"],
    }[model]


def score_lynch_category(pack: dict) -> dict:
    """Score a company against Peter Lynch-style category evidence."""
    signals = extract_company_signals(pack)
    model = signals["business_model_type"]
    story_score = (
        5
        if model != "generic"
        and "not established" not in signals["primary_growth_engine"].lower()
        else 1
    )
    growth_score, growth_gaps = _growth_score(pack, model)
    valuation_score, valuation_gaps = _valuation_score(pack)
    balance_score, balance_gaps = _balance_sheet_score(pack)
    cyclicality_score = _cyclicality_score(model)
    growth_peg = _growth_peg_evidence(pack)
    primary, secondary, category_scores = _category_profile(model, growth_score)
    evidence_gaps = list(
        dict.fromkeys(
            growth_gaps
            + valuation_gaps
            + balance_gaps
            + _model_evidence_gaps(model)
        )
    )
    confidence = "Medium-High" if story_score == 5 and growth_score >= 4 else "Medium"
    interpretation = {
        "software_cloud": "A Stalwart/Fast Grower hybrid story, with recurring growth and valuation discipline both required.",
        "consumer_ecosystem": "A Stalwart-led hybrid whose category depends on services growth and the product replacement cycle.",
        "semiconductor": "A Fast Grower/Cyclical hybrid that requires cycle-normalized earnings and valuation discipline.",
        "retail": "Category fit depends on same-store sales, unit economics, and inventory control.",
        "payments_network": "A network Stalwart with Fast Grower potential if volume and earnings remain durable.",
        "industrial": "A Cyclical profile whose Stalwart qualities depend on backlog and normalized margins.",
        "financial": "A Cyclical/Stalwart profile governed by credit quality, capital strength, and book value.",
        "generic": "The current pack does not establish a reliable Lynch category.",
    }[model]

    return {
        "business_model_type": model,
        "primary_category": primary,
        "secondary_category": secondary,
        "category_confidence": confidence,
        "category_scores": category_scores,
        "story_score": story_score,
        "growth_score": growth_score,
        "valuation_vs_growth_score": valuation_score,
        "balance_sheet_score": balance_score,
        "cyclicality_score": cyclicality_score,
        "evidence_gaps": evidence_gaps,
        "lynch_interpretation": interpretation,
        "follow_up_indicators": _follow_up_indicators(model),
        "growth_peg_evidence": growth_peg,
    }
