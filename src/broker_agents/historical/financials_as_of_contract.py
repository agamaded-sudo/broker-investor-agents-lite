"""Point-in-time readiness contract for official financial statements."""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path

from broker_agents.historical.as_of_context import build_as_of_context

REQUIRED_DATE_FIELDS = (
    "fiscal_period_end_date",
    "filing_date",
    "accepted_date",
    "source_url_or_accession_number",
    "statement_type",
    "period_type",
    "data_as_of_date_or_ingestion_date",
)


@dataclass(frozen=True)
class FinancialsProviderCapability:
    """Declared date capabilities of one official-financials provider."""

    provider_name: str
    supports_filing_date: bool
    supports_period_end_date: bool
    supports_accepted_date: bool
    supports_as_of_filtering: bool
    enforcement_level: str
    leakage_risk: str
    notes: str

    def to_dict(self) -> dict:
        """Serialize the provider capability."""
        return asdict(self)


@dataclass(frozen=True)
class FinancialsAsOfContract:
    """Availability and leakage contract for official financial facts."""

    as_of_date: str | None
    historical_mode: bool
    provider_name: str
    section: str
    supports_as_of_date: bool
    enforcement_level: str
    leakage_risk: str
    required_date_fields: list[str] = field(default_factory=list)
    available_date_fields: list[str] = field(default_factory=list)
    missing_date_fields: list[str] = field(default_factory=list)
    allowed_filing_cutoff: str | None = None
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    status: str = "readiness_only"
    provider_capability: FinancialsProviderCapability | None = None

    def to_dict(self) -> dict:
        """Serialize the complete financials as-of contract."""
        data = asdict(self)
        return data


def _load_fixture_fields(
    fixtures_root: Path | None,
    ticker: str | None,
) -> tuple[set[str], list[str]]:
    """Read top-level fixture metadata without changing financial mapping."""
    if fixtures_root is None or not ticker:
        return set(), []
    path = Path(fixtures_root) / f"sec_company_facts_{ticker.lower()}.json"
    if not path.is_file():
        return set(), [f"Official financials fixture not found: {path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return set(), [f"Official financials fixture could not be inspected: {exc}"]
    if not isinstance(payload, dict):
        return set(), [f"Official financials fixture is not an object: {path}"]
    return set(payload), []


def _available_contract_fields(raw_fields: set[str]) -> list[str]:
    """Map fixture aliases onto the future point-in-time contract fields."""
    available = []
    for field_name in (
        "fiscal_period_end_date",
        "filing_date",
        "accepted_date",
        "statement_type",
        "period_type",
    ):
        if field_name in raw_fields:
            available.append(field_name)
    if {"source_url", "accession_number"} & raw_fields:
        available.append("source_url_or_accession_number")
    if {"data_as_of_date", "ingestion_date"} & raw_fields:
        available.append("data_as_of_date_or_ingestion_date")
    return available


def build_financials_as_of_contract(
    as_of_date: str | None,
    *,
    fixtures_root: Path | None = None,
    ticker: str | None = None,
    provider_name: str = "sec_fixture",
) -> FinancialsAsOfContract:
    """Build a deterministic point-in-time readiness contract."""
    context = build_as_of_context(as_of_date)
    raw_fields, inspection_warnings = _load_fixture_fields(fixtures_root, ticker)
    available = _available_contract_fields(raw_fields)
    missing = [field for field in REQUIRED_DATE_FIELDS if field not in available]
    supports_period_end = "fiscal_period_end_date" in available
    supports_filing = "filing_date" in available
    supports_accepted = "accepted_date" in available
    supports_filtering = supports_period_end and (
        supports_filing or supports_accepted
    )
    enforcement_level = "partial" if supports_filtering else "readiness_only"
    leakage_risk = "medium" if supports_filtering else "high"
    capability = FinancialsProviderCapability(
        provider_name=provider_name,
        supports_filing_date=supports_filing,
        supports_period_end_date=supports_period_end,
        supports_accepted_date=supports_accepted,
        supports_as_of_filtering=supports_filtering,
        enforcement_level=enforcement_level,
        leakage_risk=leakage_risk,
        notes=(
            "Point-in-time financial statement enforcement requires "
            "filing-date or accepted-date filtering."
        ),
    )
    if not context.historical_mode:
        return FinancialsAsOfContract(
            as_of_date=None,
            historical_mode=False,
            provider_name=provider_name,
            section="official_financials",
            supports_as_of_date=supports_filtering,
            enforcement_level=enforcement_level,
            leakage_risk=leakage_risk,
            required_date_fields=list(REQUIRED_DATE_FIELDS),
            available_date_fields=available,
            missing_date_fields=missing,
            warnings=inspection_warnings,
            notes=[capability.notes],
            status="current_analysis",
            provider_capability=capability,
        )

    warnings = list(inspection_warnings)
    if not supports_filtering:
        warnings.append(
            "Official financials are not yet guaranteed point-in-time safe. "
            "Fixtures or manual inputs may contain facts filed after the "
            "as_of_date."
        )
    return FinancialsAsOfContract(
        as_of_date=context.as_of_date.isoformat(),
        historical_mode=True,
        provider_name=provider_name,
        section="official_financials",
        supports_as_of_date=supports_filtering,
        enforcement_level=enforcement_level,
        leakage_risk=leakage_risk,
        required_date_fields=list(REQUIRED_DATE_FIELDS),
        available_date_fields=available,
        missing_date_fields=missing,
        allowed_filing_cutoff=context.as_of_date.isoformat(),
        warnings=warnings,
        notes=[capability.notes],
        status=("partial" if supports_filtering else "readiness_only"),
        provider_capability=capability,
    )
