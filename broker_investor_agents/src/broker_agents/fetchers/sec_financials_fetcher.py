"""Offline-safe SEC financial facts fetcher skeleton and fixture mapping."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SecCompanyIdentity:
    """Deterministic company identity used by the SEC fetcher skeleton."""

    ticker: str
    company_name: str
    cik: str
    exchange: str
    source: str
    confidence: str


@dataclass(frozen=True)
class SecFinancialFacts:
    """Normalized annual financial facts from an official filing source."""

    ticker: str
    cik: str
    fiscal_year: str
    period: str
    revenue: float | int | None
    gross_profit: float | int | None
    operating_income: float | int | None
    net_income: float | int | None
    operating_cash_flow: float | int | None
    capital_expenditure: float | int | None
    free_cash_flow: float | int | None
    cash_and_equivalents: float | int | None
    long_term_debt: float | int | None
    shareholders_equity: float | int | None
    source_url: str
    source_name: str
    confidence: str

    def to_dict(self) -> dict:
        """Return the normalized facts as a plain dictionary."""
        return asdict(self)


COMPANY_IDENTITIES = {
    "MSFT": SecCompanyIdentity(
        ticker="MSFT",
        company_name="Microsoft Corporation",
        cik="0000789019",
        exchange="NASDAQ",
        source="SEC company ticker mapping fixture",
        confidence="high",
    ),
    "AAPL": SecCompanyIdentity(
        ticker="AAPL",
        company_name="Apple Inc.",
        cik="0000320193",
        exchange="NASDAQ",
        source="SEC company ticker mapping fixture",
        confidence="high",
    ),
    "NVDA": SecCompanyIdentity(
        ticker="NVDA",
        company_name="NVIDIA Corporation",
        cik="0001045810",
        exchange="NASDAQ",
        source="SEC company ticker mapping fixture",
        confidence="high",
    ),
    "COST": SecCompanyIdentity(
        ticker="COST",
        company_name="Costco Wholesale Corporation",
        cik="0000909832",
        exchange="NASDAQ",
        source="local_mapping",
        confidence="high",
    ),
}


def load_sec_fixture(path: Path) -> dict:
    """Load a compact SEC fixture from disk."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"SEC fixture not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid SEC fixture JSON in {path}: {exc}") from exc
    except OSError as exc:
        raise OSError(f"Could not read SEC fixture {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"SEC fixture must contain a JSON object: {path}")
    return data


def _number(value: Any) -> float | int | None:
    """Return a numeric fixture value or None."""
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class SecFinancialsFetcher:
    """Prepare SEC identity, mapping, and provenance without live requests."""

    def resolve_company_identity(self, ticker: str) -> SecCompanyIdentity:
        """Resolve a supported ticker through a deterministic local mapping."""
        normalized = ticker.strip().upper()
        try:
            return COMPANY_IDENTITIES[normalized]
        except KeyError as exc:
            supported = ", ".join(COMPANY_IDENTITIES)
            raise ValueError(
                f"Unsupported SEC identity ticker: {normalized}. "
                f"Supported fixture identities: {supported}."
            ) from exc

    def fetch_company_facts(self, ticker: str) -> dict:
        """Reserve the live SEC fetch interface without performing network I/O."""
        self.resolve_company_identity(ticker)
        raise NotImplementedError(
            "Live SEC fetching is not implemented yet. Use fixture data or manual inputs."
        )

    def map_company_facts_to_financials(
        self,
        raw_facts: dict,
        ticker: str,
        cik: str,
    ) -> SecFinancialFacts:
        """Map a compact raw-facts dictionary into normalized financial facts."""
        if not isinstance(raw_facts, dict):
            raise ValueError("SEC company facts must be a dictionary.")
        facts = raw_facts.get("facts", raw_facts)
        if not isinstance(facts, dict):
            raise ValueError("SEC fixture facts must be a dictionary.")

        operating_cash_flow = _number(facts.get("operating_cash_flow"))
        capital_expenditure = _number(facts.get("capital_expenditure"))
        free_cash_flow = _number(facts.get("free_cash_flow"))
        if (
            free_cash_flow is None
            and operating_cash_flow is not None
            and capital_expenditure is not None
        ):
            free_cash_flow = operating_cash_flow - capital_expenditure

        return SecFinancialFacts(
            ticker=ticker.strip().upper(),
            cik=str(cik).zfill(10),
            fiscal_year=str(raw_facts.get("fiscal_year") or facts.get("fiscal_year") or ""),
            period=str(raw_facts.get("period") or facts.get("period") or ""),
            revenue=_number(facts.get("revenue")),
            gross_profit=_number(facts.get("gross_profit")),
            operating_income=_number(facts.get("operating_income")),
            net_income=_number(facts.get("net_income")),
            operating_cash_flow=operating_cash_flow,
            capital_expenditure=capital_expenditure,
            free_cash_flow=free_cash_flow,
            cash_and_equivalents=_number(facts.get("cash_and_equivalents")),
            long_term_debt=_number(facts.get("long_term_debt")),
            shareholders_equity=_number(facts.get("shareholders_equity")),
            source_url=str(raw_facts.get("source_url") or ""),
            source_name=str(raw_facts.get("source_name") or "SEC company facts fixture"),
            confidence=str(raw_facts.get("confidence") or "high"),
        )

    def build_source_log(self, financials: SecFinancialFacts) -> list[dict]:
        """Build a source-log record for normalized official financials."""
        source_id = (
            f"sec_company_facts_{financials.ticker.lower()}_"
            f"{financials.fiscal_year}"
        )
        return [
            {
                "source_id": source_id,
                "source_name": financials.source_name,
                "source_type": "company",
                "source_url": financials.source_url,
                "confidence": financials.confidence,
                "confidence_score": 0.95,
                "freshness": "fixture",
                "notes": "Official financials mapped from SEC fixture/source.",
            }
        ]


def map_fixture_to_financials(raw_facts: dict) -> SecFinancialFacts:
    """Map a compact fixture using its embedded ticker and CIK."""
    ticker = str(raw_facts.get("ticker") or "").strip().upper()
    if not ticker:
        raise ValueError("SEC fixture is missing ticker.")
    fetcher = SecFinancialsFetcher()
    identity = fetcher.resolve_company_identity(ticker)
    cik = str(raw_facts.get("cik") or identity.cik)
    return fetcher.map_company_facts_to_financials(raw_facts, ticker, cik)
