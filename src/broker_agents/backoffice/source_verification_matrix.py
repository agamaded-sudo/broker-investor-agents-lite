"""Broker-facing evidence verification matrix built from field-level provenance."""

from dataclasses import asdict, dataclass

from broker_agents.backoffice.source_verification import verify_sources

VERIFICATION_STATUSES = {
    "verified",
    "partially_verified",
    "missing",
    "placeholder_heavy",
    "not_applicable",
}

CATEGORY_SPECS = {
    "official_financials": {
        "sections": {"financial_statements_summary"},
        "action": "Validate remaining filing fields and calculation provenance.",
        "critical": True,
    },
    "market_data": {
        "sections": {"valuation_snapshot"},
        "action": "Validate the timestamp, provider, and market snapshot methodology.",
        "critical": True,
    },
    "historical_valuation": {
        "sections": {"historical_valuation"},
        "action": "Validate the provider and 5Y/10Y median and percentile methodology.",
        "critical": True,
    },
    "growth_peg": {
        "sections": {"growth_peg_analysis"},
        "action": "Validate growth histories, forward estimates, and PEG methodology.",
        "critical": True,
    },
    "scuttlebutt": {
        "sections": {"scuttlebutt"},
        "action": "Collect Fisher-style customer, product, partner, and competitive evidence.",
        "critical": True,
    },
    "management_incentives": {
        "sections": {"management_ownership_incentives"},
        "action": "Validate management incentives, ownership, and compensation evidence.",
        "critical": True,
    },
    "index_overlap": {
        "sections": {"index_benchmark_alternative"},
        "action": "Validate index and ETF holdings, indirect exposure, and benchmark risk.",
        "critical": True,
    },
}

STATUS_LABELS = {
    "official_verified": "verified",
    "market_data_verified": "verified",
    "manual_placeholder": "placeholder",
    "calculated": "calculated",
    "missing": "missing",
    "needs_verification": "unverified",
    "not_applicable": "not applicable",
}


@dataclass(frozen=True)
class EvidenceVerificationCategory:
    """Verification status for one broker-facing evidence category."""

    category: str
    status: str
    available_evidence: list[str]
    missing_evidence: list[str]
    limitation: str
    broker_action: str
    blocks_promotion: bool

    def to_dict(self) -> dict:
        """Serialize this category to a plain dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class SourceVerificationMatrixSummary:
    """Aggregate broker-facing source verification summary."""

    overall_status: str
    verified_categories_count: int
    partial_categories_count: int
    missing_or_placeholder_categories_count: int
    promotion_blocking_categories: list[str]
    concise_broker_summary: str
    categories: list[EvidenceVerificationCategory]

    def to_dict(self) -> dict:
        """Serialize this summary and its categories."""
        return {
            **asdict(self),
            "categories": [item.to_dict() for item in self.categories],
        }


def _field_label(record: dict) -> str:
    """Render a compact evidence label from one verification record."""
    return str(record.get("field") or record.get("field_path") or "unknown field")


def _dedupe(values: list[str]) -> list[str]:
    """Preserve order while removing duplicate evidence labels."""
    return list(dict.fromkeys(value for value in values if value))


def _status_for_records(records: list[dict]) -> str:
    """Aggregate field-level statuses into an allowed category status."""
    if not records:
        return "missing"
    statuses = [record.get("status") for record in records]
    verified = sum(
        status in {"official_verified", "market_data_verified"} for status in statuses
    )
    placeholders = statuses.count("manual_placeholder")
    missing = statuses.count("missing")
    unverified = statuses.count("needs_verification")
    applicable = len(statuses) - statuses.count("not_applicable")

    if applicable == 0:
        return "not_applicable"
    if verified == applicable:
        return "verified"
    if verified:
        return "partially_verified"
    if placeholders:
        return "placeholder_heavy"
    if missing == applicable:
        return "missing"
    if unverified:
        return "partially_verified"
    return "missing"


def _portfolio_overlap_placeholder(pack: dict) -> bool:
    """Return whether user-provided indirect exposure estimates exist."""
    context = pack.get("portfolio_context_form", {})
    estimates = context.get("indirect_exposure_estimates", {})
    return bool(context.get("provided") and isinstance(estimates, dict) and estimates)


def build_source_verification_matrix(pack: dict) -> list[EvidenceVerificationCategory]:
    """Build the seven-category source verification matrix."""
    verification = verify_sources(pack)
    all_records = verification.get("source_verification_records", [])
    categories: list[EvidenceVerificationCategory] = []

    for category, spec in CATEGORY_SPECS.items():
        records = [
            record
            for record in all_records
            if record.get("section") in spec["sections"]
        ]
        status = _status_for_records(records)
        available = [
            f"{_field_label(record)} ({STATUS_LABELS.get(record.get('status'), record.get('status'))})"
            for record in records
            if record.get("status")
            in {
                "official_verified",
                "market_data_verified",
                "manual_placeholder",
                "calculated",
                "needs_verification",
            }
        ]
        missing = [
            _field_label(record)
            for record in records
            if record.get("status") in {"missing", "needs_verification"}
        ]

        if category == "index_overlap" and _portfolio_overlap_placeholder(pack):
            available.append("user-provided indirect exposure estimates (placeholder)")
            if status == "missing":
                status = "placeholder_heavy"

        available = _dedupe(available)
        missing = _dedupe(missing)
        if status == "verified":
            limitation = "No critical source limitation identified in the current pack."
        elif status == "partially_verified":
            limitation = "Some evidence is sourced, but coverage or methodology remains incomplete."
        elif status == "placeholder_heavy":
            limitation = "Evidence is primarily manual or user-provided and needs source validation."
        elif status == "not_applicable":
            limitation = "This evidence category is not applicable to the current analysis."
        else:
            limitation = "Critical evidence is not present in the current pack."
        blocks = bool(spec["critical"] and status != "verified")
        categories.append(
            EvidenceVerificationCategory(
                category=category,
                status=status,
                available_evidence=available or ["None established"],
                missing_evidence=missing or ["None identified"],
                limitation=limitation,
                broker_action=str(spec["action"]),
                blocks_promotion=blocks,
            )
        )

    return categories


def summarize_source_verification_matrix(
    pack: dict,
) -> SourceVerificationMatrixSummary:
    """Aggregate category verification into a concise broker summary."""
    categories = build_source_verification_matrix(pack)
    verified = sum(item.status == "verified" for item in categories)
    partial = sum(item.status == "partially_verified" for item in categories)
    missing_or_placeholder = sum(
        item.status in {"missing", "placeholder_heavy"} for item in categories
    )
    blocking = [item.category for item in categories if item.blocks_promotion]
    if verified == len(categories):
        overall = "verified"
    elif verified or partial:
        overall = "partially verified"
    else:
        overall = "verification required"
    concise = (
        f"{verified} verified, {partial} partially verified, and "
        f"{missing_or_placeholder} missing or placeholder-heavy categories. "
        f"Promotion blockers: {', '.join(blocking) if blocking else 'none'}."
    )
    return SourceVerificationMatrixSummary(
        overall_status=overall,
        verified_categories_count=verified,
        partial_categories_count=partial,
        missing_or_placeholder_categories_count=missing_or_placeholder,
        promotion_blocking_categories=blocking,
        concise_broker_summary=concise,
        categories=categories,
    )
