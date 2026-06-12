# Market Data Provider Selection

## Purpose

This document is a provider-selection checklist for future market-data
integration. It is not final vendor due diligence and does not add live API
integration, API keys, network requests, or web scraping.

## Candidate Provider Categories

| Provider / Category | Likely Use Case | Strengths | Limitations | API Key | Cost Consideration | Backtesting | Financial Statements | Market Prices | Implementation Complexity | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| Local CSV data | First real-data trial and controlled imports | Auditable, offline, provider-neutral, easy to reproduce | User must acquire, normalize, and refresh data | No | Depends on the upstream source | Strong for controlled trials | Possible if separately structured | Strong for historical prices | Low | Current recommended path |
| Yahoo Finance style data source, unofficial / not primary dependency | Exploration and manual comparison | Broad symbol coverage and familiar formats | Unofficial access patterns may change; provenance may be unclear | Usually no, depending on access method | Often free or unknown | Useful for exploratory work | Limited and not a primary filing source | Generally useful | Medium | Should not become a critical production dependency without review |
| Alpha Vantage | Retail-friendly API evaluation | Accessible documentation and multiple data categories | Rate limits and adjusted-history details require validation | Yes | Free / freemium | Potentially suitable | Some coverage; verify source lineage | Suitable in principle | Medium | Validate limits, adjustment methodology, and licensing |
| Financial Modeling Prep | Combined market and financial-data evaluation | Broad financial and valuation-oriented dataset | Coverage, methodology, and licensing require due diligence | Yes | Freemium / paid | Potentially suitable | Potentially suitable | Suitable in principle | Medium | Could reduce provider count if quality meets requirements |
| Polygon | Market-price and market-structure data evaluation | Market-data focus and potentially detailed time series | Historical depth and entitlement tier may affect use | Yes | Paid / freemium | Potentially strong | Not the primary reason to select it | Strong in principle | Medium to high | Review exchange entitlements and adjustment methodology |
| Tiingo | Historical-price research evaluation | Research-oriented pricing data and adjusted series | Coverage and plan constraints require validation | Yes | Freemium / paid | Potentially strong | Limited compared with filing specialists | Strong in principle | Medium | Review corporate-action handling and redistribution terms |
| Twelve Data | Multi-market price-data evaluation | Broad API surface and multiple intervals | Rate limits, exchange coverage, and plan differences | Yes | Freemium / paid | Potentially suitable | Limited compared with filing specialists | Suitable in principle | Medium | Validate historical depth and adjusted-price conventions |
| Nasdaq Data Link | Curated dataset evaluation | Dataset catalog can support specialized research | Availability, licensing, and schemas vary by dataset | Usually yes | Free / paid / dataset-specific | Dataset-dependent | Dataset-dependent | Dataset-dependent | Medium to high | Selection must be made at the individual dataset level |
| IBKR data, future advanced option | Broker-connected advanced research environment | Potential alignment with brokerage market data and entitlements | Operational complexity, subscriptions, and broker coupling | Credentials and entitlements | Paid / subscription-dependent | Potentially suitable | Not a filing-data replacement | Strong in principle | High | Future option only; not appropriate for the current offline build |

## Selection Checklist

Before selecting a live provider, confirm:

- Historical depth for the required lookback and forward-return windows.
- Corporate-action and adjusted-price methodology.
- Exchange and ticker coverage.
- Rate limits and batch-download behavior.
- Data licensing, storage, caching, and redistribution rights.
- Point-in-time behavior and revision policy.
- Benchmark coverage, including SPY or an approved alternative.
- Financial-statement provenance if the provider supplies fundamentals.
- Stable identifiers, delisted-security handling, and symbol changes.
- Cost at trial, internal-demo, and hosted-operation scale.
- Failure behavior, support expectations, and provider exit strategy.

## Recommended Current Path

1. Use local real CSV import first.
2. Keep fixture data for tests.
3. Select one live market data provider later.
4. Do not build a live provider until the provider choice is fixed.

## Required Local CSV Fields

| Field | Requirement |
|---|---|
| `date` | Required |
| `open` | Optional |
| `high` | Optional |
| `low` | Optional |
| `close` | Required when adjusted close is unavailable |
| `adjusted_close` | Optional but preferred |
| `volume` | Optional |

Adjusted close is preferred for backtesting because it may reflect corporate
actions supplied by the data source. If `adjusted_close` exists, the CSV
provider uses it. Otherwise it falls back to `close`.

All live/API work remains future scope. This task adds no live API integration.

## Governance Boundary

Provider selection changes data provenance, not investor philosophy. Any future
integration must preserve source verification, auditability, controlled missing
data, and the existing research-only safety language. It must not create a
recommendation, ranking, allocation instruction, or trade signal.
