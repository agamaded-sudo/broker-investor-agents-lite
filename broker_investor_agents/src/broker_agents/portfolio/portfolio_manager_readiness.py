"""Deterministic Portfolio Manager Readiness Agent."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import yaml

from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.backoffice.portfolio_context import (
    load_portfolio_context,
    merge_portfolio_context_into_pack,
)
from broker_agents.backoffice.source_verification import verify_sources
from broker_agents.calculators.bogle_index_overlap import (
    calculate_bogle_index_overlap,
)
from broker_agents.calculators.decision_candidates import (
    CURRENT_DECISIONS,
    build_decision_candidate,
)
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
)
from broker_agents.review.human_review_queue import generate_human_review_queue

PORTFOLIO_STATUSES = {
    "Not Eligible",
    "Watchlist Only",
    "Research Queue",
    "Human Review Required",
    "Eligible for Portfolio Consideration",
}
READINESS_LABELS = {
    "Blocked",
    "Needs Review",
    "Needs Evidence",
    "Watchlist Ready",
    "Consideration Ready",
}
INVESTORS = ("buffett", "munger", "fisher", "lynch", "bogle")


@dataclass(frozen=True)
class PortfolioReadinessItem:
    """One company's portfolio governance readiness assessment."""

    ticker: str
    company_name: str
    portfolio_status: str
    readiness_label: str
    primary_blocker: str
    source_quality_summary: str
    human_review_status: str
    promotion_status_summary: str
    investor_candidate_summary: str
    final_decision_summary: str
    portfolio_fit_notes: str
    cross_portfolio_risk_flags: list[str]
    manual_trigger_required: bool
    manual_trigger_reason: list[str]
    not_ready_for_execution_reasons: list[str]
    safety_flags: list[str]

    def to_dict(self) -> dict:
        """Serialize this readiness item to a plain dictionary."""
        return asdict(self)


def _load_yaml(path: Path) -> dict:
    """Load a YAML mapping, returning an empty mapping on failure."""
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _load_portfolio_context(examples_root: Path) -> dict:
    """Load shared portfolio context when available."""
    path = Path(examples_root) / "portfolio_context.yaml"
    if not path.is_file():
        return {}
    try:
        return load_portfolio_context(path)
    except (OSError, ValueError, yaml.YAMLError):
        return {}


def _load_review_records(
    tickers: list[str],
    outputs_root: Path,
    examples_root: Path,
) -> list[dict]:
    """Load structured review records, regenerating them when unavailable."""
    path = Path(outputs_root) / "human_review_queue.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
    except (OSError, json.JSONDecodeError):
        pass
    return [
        item.to_dict()
        for item in generate_human_review_queue(
            tickers,
            outputs_root,
            examples_root,
        )
    ]


def _summary(values: dict[str, str]) -> str:
    """Render investor-keyed values as a compact deterministic summary."""
    return "; ".join(f"{key.title()}: {value}" for key, value in values.items())


def _risk_flags(signals: dict, open_review: bool) -> list[str]:
    """Build company and cross-portfolio risk flags."""
    model = signals.get("business_model_type", "generic")
    flags = [
        "Index overlap concentration",
        "Valuation risk concentration",
        "Evidence gap concentration",
    ]
    if model in {"software_cloud", "consumer_ecosystem", "semiconductor"}:
        flags.append("Big Tech concentration")
        flags.append("AI / technology theme concentration")
    if model == "software_cloud":
        flags.extend(["Big Tech exposure", "AI/cloud capex valuation sensitivity"])
    elif model == "consumer_ecosystem":
        flags.extend(["Big Tech exposure", "Consumer ecosystem concentration"])
    elif model == "semiconductor":
        flags.extend(["AI/semiconductor cycle risk", "Valuation sensitivity"])
    if open_review:
        flags.extend(
            [
                "Human review dependency concentration",
                "Open human review dependency",
            ]
        )
    return list(dict.fromkeys(flags))


def _portfolio_fit_notes(pack: dict, signals: dict) -> str:
    """Describe portfolio fit without assigning a position or weight."""
    overlap = calculate_bogle_index_overlap(pack)
    model = signals.get("business_model_type", "generic")
    return (
        f"Business model is {model}. Index overlap is {overlap['overlap_label']}; "
        f"concentration risk is {overlap['concentration_risk_label']}. "
        "Any separate position remains subject to benchmark evidence, portfolio context, "
        "and human review."
    )


def _manual_trigger_reasons(
    open_reviews: list[dict],
    source_quality: str,
    candidates: dict[str, str],
    manual_candidates: dict[str, str],
    promotions: dict[str, str],
) -> list[str]:
    """Build deterministic reasons requiring a manual governance trigger."""
    reasons: list[str] = []
    if open_reviews:
        reasons.append("Open human review items.")
    if source_quality != "strong":
        reasons.append(f"Enriched source quality is {source_quality}, not strong.")
    if candidates != manual_candidates:
        reasons.append("At least one candidate decision changed after enrichment.")
    if any(status in {"Needs More Evidence", "Conditionally Eligible"} for status in promotions.values()):
        reasons.append("Promotion eligibility remains conditional or evidence-blocked.")
    reasons.extend(
        [
            "Benchmark risk still missing.",
            "Fisher scuttlebutt missing.",
            "Munger incentives missing.",
            "Buffett capex normalization missing.",
            "Lynch growth methodology validation pending.",
        ]
    )
    if any(
        marker in candidate
        for candidate in candidates.values()
        for marker in ("Needs", "Watch", "Wait")
    ):
        reasons.append("One or more investor candidates remain Needs Evidence, Watch, or Wait oriented.")
    return list(dict.fromkeys(reasons))


def _classify(
    pack_exists: bool,
    source_quality: str,
    open_blocking_reviews: list[dict],
    promotions: dict[str, str],
    final_decisions_stable: bool,
) -> tuple[str, str, str]:
    """Apply conservative portfolio readiness rules in priority order."""
    if not pack_exists or source_quality == "weak":
        return (
            "Not Eligible",
            "Blocked",
            "Severe source quality or enriched-pack availability issues block readiness.",
        )
    if open_blocking_reviews:
        return (
            "Human Review Required",
            "Needs Review",
            "Open human review items block promotion.",
        )
    if any(status == "Needs More Evidence" for status in promotions.values()):
        return (
            "Research Queue",
            "Needs Evidence",
            "Promotion eligibility remains blocked by unresolved evidence.",
        )
    if any(
        term in decision
        for decision in CURRENT_DECISIONS.values()
        for term in ("Wait", "Watch", "Prefer Broad Index", "Needs More")
    ):
        return (
            "Watchlist Only",
            "Watchlist Ready",
            "Investor final decisions remain cautious.",
        )
    if final_decisions_stable:
        return (
            "Eligible for Portfolio Consideration",
            "Consideration Ready",
            "Governance prerequisites are satisfied for human portfolio consideration.",
        )
    return (
        "Research Queue",
        "Needs Evidence",
        "Final decision stability is not established.",
    )


def generate_portfolio_readiness_items(
    tickers: list[str],
    outputs_root: Path,
    examples_root: Path,
) -> list[PortfolioReadinessItem]:
    """Generate portfolio governance readiness items for enriched companies."""
    outputs_root = Path(outputs_root)
    examples_root = Path(examples_root)
    normalized_tickers = [ticker.strip().upper() for ticker in tickers if ticker.strip()]
    review_records = _load_review_records(
        normalized_tickers,
        outputs_root,
        examples_root,
    )
    portfolio_context = _load_portfolio_context(examples_root)
    items: list[PortfolioReadinessItem] = []

    for ticker in normalized_tickers:
        lower = ticker.lower()
        enriched_path = outputs_root / ticker / f"{lower}_enriched_input.yaml"
        enriched_pack = _load_yaml(enriched_path)
        manual_pack = _load_yaml(examples_root / f"{lower}_input.yaml")
        analysis_pack = merge_portfolio_context_into_pack(
            enriched_pack,
            portfolio_context,
        )
        manual_analysis_pack = merge_portfolio_context_into_pack(
            manual_pack,
            portfolio_context,
        )
        signals = extract_company_signals(analysis_pack) if analysis_pack else {}
        verification = verify_sources(enriched_pack) if enriched_pack else {}
        source_quality = verification.get("overall_source_quality", "weak")
        candidates = {
            investor: build_decision_candidate(analysis_pack, investor)[
                "candidate_decision"
            ]
            for investor in INVESTORS
        } if analysis_pack else {}
        manual_candidates = {
            investor: build_decision_candidate(manual_analysis_pack, investor)[
                "candidate_decision"
            ]
            for investor in INVESTORS
        } if manual_analysis_pack else {}
        promotions = {
            investor: evaluate_promotion_eligibility(analysis_pack, investor)[
                "promotion_eligibility"
            ]
            for investor in INVESTORS
        } if analysis_pack else {}
        ticker_reviews = [
            record
            for record in review_records
            if str(record.get("ticker", "")).upper() == ticker
        ]
        open_blocking_reviews = [
            record
            for record in ticker_reviews
            if record.get("status") in {"Open", "In Review"}
            and record.get("blocks_promotion") is True
        ]
        final_decisions = dict(CURRENT_DECISIONS)
        status, readiness, blocker = _classify(
            bool(enriched_pack),
            source_quality,
            open_blocking_reviews,
            promotions,
            True,
        )
        trigger_reasons = _manual_trigger_reasons(
            open_blocking_reviews,
            source_quality,
            candidates,
            manual_candidates,
            promotions,
        )
        review_status = (
            f"{len(open_blocking_reviews)} open blocking review item(s)"
            if open_blocking_reviews
            else "No open blocking review items"
        )
        not_ready = [
            "Buy/sell decisions are not authorized.",
            "Position sizing and final allocation are not authorized.",
            "Rebalancing is not authorized.",
            "Auto-promotion remains disabled.",
            "Human review items remain open.",
            "Live trading or execution is not supported.",
        ]
        safety_flags = [
            "no_trade_execution",
            "no_buy_sell_signal",
            "no_final_weights",
            "no_rebalancing",
            "no_auto_promotion",
            "human_review_required",
            "final_decisions_unchanged",
            "not_a_recommendation",
        ]
        item = PortfolioReadinessItem(
            ticker=ticker,
            company_name=str(
                signals.get("company_name")
                or enriched_pack.get("company_identity", {}).get("company_name")
                or "Unknown company"
            ),
            portfolio_status=status,
            readiness_label=readiness,
            primary_blocker=blocker,
            source_quality_summary=(
                f"Overall source quality: {source_quality}; "
                f"verification status: {verification.get('source_verification_status', 'not available')}."
            ),
            human_review_status=review_status,
            promotion_status_summary=_summary(promotions),
            investor_candidate_summary=_summary(candidates),
            final_decision_summary=_summary(final_decisions),
            portfolio_fit_notes=_portfolio_fit_notes(analysis_pack, signals),
            cross_portfolio_risk_flags=_risk_flags(
                signals,
                bool(open_blocking_reviews),
            ),
            manual_trigger_required=bool(trigger_reasons),
            manual_trigger_reason=trigger_reasons,
            not_ready_for_execution_reasons=not_ready,
            safety_flags=safety_flags,
        )
        if item.portfolio_status not in PORTFOLIO_STATUSES:
            raise ValueError(f"Unsupported portfolio status: {item.portfolio_status}")
        if item.readiness_label not in READINESS_LABELS:
            raise ValueError(f"Unsupported readiness label: {item.readiness_label}")
        items.append(item)
    return items
