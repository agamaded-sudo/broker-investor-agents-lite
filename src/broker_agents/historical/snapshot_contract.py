"""Historical data snapshot capability and leakage-risk contract."""

from dataclasses import asdict, dataclass, field
from pathlib import Path

from broker_agents.historical.as_of_context import build_as_of_context
from broker_agents.historical.financials_as_of_contract import (
    FinancialsAsOfContract,
    build_financials_as_of_contract,
)

SECTIONS = (
    "official_financials",
    "market_prices",
    "historical_valuation",
    "growth_peg",
    "market_snapshot",
    "scuttlebutt",
    "management_incentives",
    "index_overlap",
    "source_verification",
    "investor_outputs",
)


@dataclass(frozen=True)
class HistoricalProviderCapability:
    """Point-in-time capability for one provider and evidence section."""

    provider_name: str
    section: str
    supports_as_of_date: bool
    enforcement_level: str
    leakage_risk: str
    notes: str

    def to_dict(self) -> dict:
        """Serialize one provider capability."""
        return asdict(self)


@dataclass(frozen=True)
class HistoricalDataSnapshotContract:
    """Structured readiness contract for one intended analysis date."""

    as_of_date: str | None
    historical_mode: bool
    point_in_time_enforcement: str
    snapshot_status: str
    supported_sections: list[str] = field(default_factory=list)
    unsupported_sections: list[str] = field(default_factory=list)
    leakage_risk_sections: list[str] = field(default_factory=list)
    provider_capabilities: list[HistoricalProviderCapability] = field(
        default_factory=list
    )
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize the full historical snapshot contract."""
        return {
            "as_of_date": self.as_of_date,
            "historical_mode": self.historical_mode,
            "point_in_time_enforcement": self.point_in_time_enforcement,
            "snapshot_status": self.snapshot_status,
            "supported_sections": list(self.supported_sections),
            "unsupported_sections": list(self.unsupported_sections),
            "leakage_risk_sections": list(self.leakage_risk_sections),
            "provider_capabilities": [
                capability.to_dict()
                for capability in self.provider_capabilities
            ],
            "warnings": list(self.warnings),
            "notes": list(self.notes),
        }


def _price_capability(price_provider: str) -> HistoricalProviderCapability:
    """Return the declared point-in-time capability of one price provider."""
    normalized = str(price_provider or "fixture").strip().lower()
    if normalized == "csv":
        return HistoricalProviderCapability(
            provider_name="csv",
            section="market_prices",
            supports_as_of_date=True,
            enforcement_level="partial",
            leakage_risk="medium",
            notes=(
                "Historical CSV prices support analysis_window_enforced: "
                "prices after as_of_date are excluded from analysis windows, "
                "but provenance and completeness remain user-supplied."
            ),
        )
    if normalized == "live_stub":
        return HistoricalProviderCapability(
            provider_name="live_stub",
            section="market_prices",
            supports_as_of_date=False,
            enforcement_level="unsupported",
            leakage_risk="high",
            notes="Live price data is not implemented in this build.",
        )
    return HistoricalProviderCapability(
        provider_name="fixture",
        section="market_prices",
        supports_as_of_date=False,
        enforcement_level="readiness_only",
        leakage_risk="high",
        notes="Synthetic fixtures may contain information after as_of_date.",
    )


def _default_capabilities(
    price_provider: str,
    financials_contract: FinancialsAsOfContract,
) -> list[HistoricalProviderCapability]:
    """Build deterministic capabilities for every required section."""
    capabilities = [
        HistoricalProviderCapability(
            financials_contract.provider_name,
            "official_financials",
            financials_contract.supports_as_of_date,
            financials_contract.enforcement_level,
            financials_contract.leakage_risk,
            financials_contract.notes[0],
        ),
        _price_capability(price_provider),
        HistoricalProviderCapability(
            "historical_valuation_fixture",
            "historical_valuation",
            False,
            "readiness_only",
            "high",
            "Valuation fixtures may use observations unavailable on as_of_date.",
        ),
        HistoricalProviderCapability(
            "growth_peg_fixture",
            "growth_peg",
            False,
            "readiness_only",
            "high",
            "Growth and forward-estimate fixtures are not point-in-time snapshots.",
        ),
        HistoricalProviderCapability(
            "market_data_fixture",
            "market_snapshot",
            False,
            "readiness_only",
            "high",
            "The current market snapshot may be dated after as_of_date.",
        ),
        HistoricalProviderCapability(
            "manual_input",
            "scuttlebutt",
            False,
            "readiness_only",
            "high",
            "Manual qualitative evidence may include later observations.",
        ),
        HistoricalProviderCapability(
            "manual_input",
            "management_incentives",
            False,
            "readiness_only",
            "high",
            "Ownership and compensation evidence lacks a point-in-time snapshot.",
        ),
        HistoricalProviderCapability(
            "manual_input",
            "index_overlap",
            False,
            "readiness_only",
            "high",
            "Index and ETF holdings may reflect later compositions.",
        ),
        HistoricalProviderCapability(
            "derived_verification",
            "source_verification",
            False,
            "readiness_only",
            "medium",
            "Verification records provenance but cannot enforce historical cutoff.",
        ),
        HistoricalProviderCapability(
            "derived_investor_outputs",
            "investor_outputs",
            False,
            "readiness_only",
            "high",
            "Outputs record as_of_date but inherit all input leakage risks.",
        ),
    ]
    order = {section: index for index, section in enumerate(SECTIONS)}
    return sorted(capabilities, key=lambda item: order[item.section])


def build_historical_snapshot_contract(
    as_of_date: str | None,
    *,
    price_provider: str = "fixture",
    input_mode: str = "ticker",
    fixtures_root: Path | None = None,
    price_data_root: Path | None = None,
    ticker: str | None = None,
    financials_provider: str = "sec_fixture",
    financials_root: Path | None = None,
) -> HistoricalDataSnapshotContract:
    """Build the point-in-time readiness and leakage contract."""
    context = build_as_of_context(as_of_date)
    financials_contract = build_financials_as_of_contract(
        as_of_date,
        fixtures_root=fixtures_root,
        ticker=ticker,
        provider_name=financials_provider,
        financials_root=financials_root,
    )
    capabilities = _default_capabilities(price_provider, financials_contract)
    if not context.historical_mode:
        return HistoricalDataSnapshotContract(
            as_of_date=None,
            historical_mode=False,
            point_in_time_enforcement="readiness_only",
            snapshot_status="current_analysis",
            provider_capabilities=capabilities,
            notes=[
                "No historical as_of_date was supplied.",
                f"Input mode: {input_mode}.",
            ],
        )

    supported = [
        item.section
        for item in capabilities
        if item.supports_as_of_date
        and item.enforcement_level in {"full", "partial"}
    ]
    unsupported = [
        item.section
        for item in capabilities
        if item.enforcement_level == "unsupported"
    ]
    leakage_sections = [
        item.section
        for item in capabilities
        if item.leakage_risk in {"medium", "high"}
    ]
    return HistoricalDataSnapshotContract(
        as_of_date=context.as_of_date.isoformat(),
        historical_mode=True,
        point_in_time_enforcement="readiness_only",
        snapshot_status="readiness_only",
        supported_sections=supported,
        unsupported_sections=unsupported,
        leakage_risk_sections=leakage_sections,
        provider_capabilities=capabilities,
        warnings=[
            "Full point-in-time enforcement is not yet guaranteed.",
            context.leakage_warning or "",
        ],
        notes=[
            f"Input mode: {input_mode}.",
            f"Fixtures root: {fixtures_root or 'Not provided'}.",
            f"Price data root: {price_data_root or 'Not provided'}.",
        ],
    )
