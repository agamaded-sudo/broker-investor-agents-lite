"""Deterministic Human Review Queue generation."""

from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from broker_agents.backoffice.portfolio_context import (
    load_portfolio_context,
    merge_portfolio_context_into_pack,
)
from broker_agents.backoffice.source_verification_matrix import (
    build_source_verification_matrix,
)
from broker_agents.calculators.decision_candidates import (
    CURRENT_DECISIONS,
    build_decision_candidate,
)

PRIORITIES = {"High", "Medium", "Low"}
REVIEW_CATEGORIES = {
    "Buffett Owner Earnings Review",
    "Munger Incentives Review",
    "Fisher Scuttlebutt Review",
    "Lynch Growth Story Review",
    "Bogle Portfolio Fit Review",
    "General Evidence Review",
}
STATUSES = {"Open", "In Review", "Reviewed", "Deferred", "Closed"}

INVESTORS = {
    "buffett": "Buffett",
    "munger": "Munger",
    "fisher": "Fisher",
    "lynch": "Lynch",
    "bogle": "Bogle",
}


@dataclass(frozen=True)
class HumanReviewItem:
    """One deterministic human-review work item."""

    review_id: str
    ticker: str
    investor: str
    priority: str
    review_category: str
    review_question: str
    why_human_review_is_needed: str
    required_evidence: list[str]
    related_gap: list[str]
    blocks_promotion: bool
    candidate_decision: str
    final_decision: str
    status: str
    reviewer_notes: str
    created_from: str
    safety_flags: list[str]

    def to_dict(self) -> dict:
        """Serialize the review item to a plain dictionary."""
        return asdict(self)


def _load_pack(path: Path) -> dict:
    """Load a YAML pack, returning an empty mapping when unavailable."""
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _load_optional_portfolio_context(examples_root: Path) -> dict:
    """Load shared portfolio context when the example exists."""
    path = Path(examples_root) / "portfolio_context.yaml"
    if not path.is_file():
        return {}
    try:
        return load_portfolio_context(path)
    except (OSError, ValueError, yaml.YAMLError):
        return {}


def _review_id(ticker: str, investor: str) -> str:
    """Build a stable review item ID."""
    return f"HRQ-{ticker.upper()}-{investor.upper()}-001"


def _safety_flags() -> list[str]:
    """Return the fixed safety flags for every review item."""
    return [
        "not_a_recommendation",
        "no_auto_promotion",
        "human_review_required",
        "final_decision_unchanged",
    ]


def _buffett_priority(candidate: str) -> str:
    """Priority rule for Buffett owner earnings review."""
    if "Buy Gradually" in candidate or "Watch / Fair Value" in candidate:
        return "High"
    return "Medium"


def _munger_priority(candidate: str) -> str:
    """Priority rule for Munger incentives review."""
    if "Buy Gradually" in candidate:
        return "High"
    return "Medium"


def _item(
    ticker: str,
    investor_key: str,
    priority: str,
    category: str,
    question: str,
    why: str,
    required_evidence: list[str],
    related_gap: list[str],
    candidate_decision: str,
) -> HumanReviewItem:
    """Build one normalized review item."""
    if priority not in PRIORITIES:
        raise ValueError(f"Unsupported priority: {priority}")
    if category not in REVIEW_CATEGORIES:
        raise ValueError(f"Unsupported review category: {category}")
    return HumanReviewItem(
        review_id=_review_id(ticker, investor_key),
        ticker=ticker.upper(),
        investor=INVESTORS[investor_key],
        priority=priority,
        review_category=category,
        review_question=question,
        why_human_review_is_needed=why,
        required_evidence=required_evidence,
        related_gap=related_gap,
        blocks_promotion=True,
        candidate_decision=candidate_decision,
        final_decision=CURRENT_DECISIONS[investor_key],
        status="Open",
        reviewer_notes="",
        created_from="post_enrichment_evidence_gap_report",
        safety_flags=_safety_flags(),
    )


def _build_items_for_ticker(ticker: str, pack: dict) -> list[HumanReviewItem]:
    """Create all review items for one enriched company pack."""
    candidates = {
        investor: build_decision_candidate(pack, investor)["candidate_decision"]
        for investor in INVESTORS
    }
    ticker_upper = ticker.upper()
    matrix = {
        item.category: item for item in build_source_verification_matrix(pack)
    }
    source_actions = {
        category: item.broker_action
        for category, item in matrix.items()
        if item.blocks_promotion
    }
    return [
        _item(
            ticker_upper,
            "buffett",
            _buffett_priority(candidates["buffett"]),
            "Buffett Owner Earnings Review",
            "Are the company's owner earnings durable and conservatively normalized enough to support the Buffett candidate decision?",
            "Maintenance versus growth capex, long-term durability, and margin-of-safety assumptions require judgment beyond fixture data.",
            [
                "Maintenance versus growth capex split.",
                "Normalized owner earnings validation.",
                "Long-term owner earnings durability.",
                "Margin of safety assumption validation.",
                source_actions.get(
                    "historical_valuation",
                    "Validate owner earnings and valuation-history provenance.",
                ),
            ],
            [
                "maintenance vs growth capex split",
                "normalized owner earnings validation",
                "margin of safety assumption validation",
            ],
            candidates["buffett"],
        ),
        _item(
            ticker_upper,
            "munger",
            _munger_priority(candidates["munger"]),
            "Munger Incentives Review",
            "Are management incentives, capital allocation behavior, and hidden-stupidity risks aligned with long-term owners?",
            "Incentives, culture, acquisition discipline, and hidden-stupidity risks require qualitative judgment.",
            [
                "Management incentives.",
                "Insider ownership.",
                "Compensation structure.",
                "Buyback discipline source evidence.",
                "Hidden-stupidity qualitative review.",
                source_actions.get(
                    "management_incentives",
                    "Validate management incentives evidence.",
                ),
            ],
            [
                "management incentives",
                "insider ownership",
                "compensation structure",
                "buyback discipline",
                "hidden-stupidity qualitative review",
            ],
            candidates["munger"],
        ),
        _item(
            ticker_upper,
            "fisher",
            "High",
            "Fisher Scuttlebutt Review",
            "Does customer, product, partner, developer, and competitive evidence support a Fisher-quality growth company?",
            "Scuttlebutt evidence cannot be resolved from financial statements alone.",
            [
                "Customer scuttlebutt.",
                "Product adoption evidence.",
                "Retention/churn evidence.",
                "Partner/developer feedback.",
                "Competitive field checks.",
                source_actions.get(
                    "scuttlebutt",
                    "Collect Fisher-style scuttlebutt evidence.",
                ),
            ],
            [
                "customer scuttlebutt",
                "product adoption",
                "retention/churn",
                "partner/developer feedback",
                "competitive field checks",
            ],
            candidates["fisher"],
        ),
        _item(
            ticker_upper,
            "lynch",
            "High" if ticker_upper == "NVDA" else "Medium",
            "Lynch Growth Story Review",
            "Is the company's growth story simple, durable, understandable, and reasonably priced relative to growth?",
            "Category classification, cyclicality, and story durability require judgment beyond PEG fixtures.",
            [
                "Growth methodology validation.",
                "PEG methodology validation.",
                "Category-specific KPI validation.",
                "Cycle-adjusted growth for semiconductors where applicable.",
                source_actions.get(
                    "growth_peg",
                    "Validate growth/PEG provider methodology.",
                ),
            ],
            [
                "growth methodology validation",
                "PEG methodology validation",
                "category-specific KPI validation",
                "cycle-adjusted growth for semiconductors",
            ],
            candidates["lynch"],
        ),
        _item(
            ticker_upper,
            "bogle",
            "Medium",
            "Bogle Portfolio Fit Review",
            "Is a separate satellite position justified despite broad-index overlap and concentration risk?",
            "Portfolio fit, investor behavior, benchmark risk tolerance, and satellite sizing require user-specific judgment.",
            [
                "Benchmark-relative returns.",
                "Volatility.",
                "Max drawdown.",
                "Beta.",
                "Correlation.",
                "ETF/index holdings validation.",
                "Proposed position size validation.",
                source_actions.get(
                    "index_overlap",
                    "Validate index and ETF overlap evidence.",
                ),
            ],
            [
                "benchmark-relative returns",
                "volatility",
                "max drawdown",
                "beta",
                "correlation",
                "ETF/index holdings validation",
                "proposed position size validation",
            ],
            candidates["bogle"],
        ),
    ]


def generate_human_review_queue(
    tickers: list[str],
    outputs_root: Path,
    examples_root: Path,
) -> list[HumanReviewItem]:
    """Generate deterministic human-review items from enriched packs."""
    outputs_root = Path(outputs_root)
    portfolio_context = _load_optional_portfolio_context(Path(examples_root))
    items: list[HumanReviewItem] = []
    for raw_ticker in tickers:
        ticker = raw_ticker.strip().upper()
        if not ticker:
            continue
        lower = ticker.lower()
        pack = _load_pack(outputs_root / ticker / f"{lower}_enriched_input.yaml")
        if not pack:
            pack = _load_pack(Path(examples_root) / f"{lower}_input.yaml")
        pack = merge_portfolio_context_into_pack(pack, portfolio_context)
        if not pack:
            continue
        items.extend(_build_items_for_ticker(ticker, pack))
    return items
