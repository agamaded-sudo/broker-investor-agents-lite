# Task 146-1B - Candidate Selection Record Schema

## Status

Completed.

## Purpose

This document defines the safe output schema for the Company Selection Agent.

The schema is called the Candidate Selection Record.

It is used to route one selected company into the Single-Company Pipeline.

## Architectural Position

The Candidate Selection Record sits between:

1. Company Selection Agent
2. Single-Company Pipeline

The Company Selection Agent may produce the record.

The Single-Company Pipeline may consume the single-company intake payload inside the record.

## Core Rule

Each Candidate Selection Record represents one company only.

It must not represent a market universe, batch, ranked list, portfolio, or recommendation set.

## Required Fields

The Candidate Selection Record should include:

- record_id
- as_of_date
- company_name
- ticker
- exchange
- listing_country
- selection_reason
- pipeline_ready_intake_payload
- safety_boundary

## Optional Fields

The Candidate Selection Record may include:

- sector
- industry
- source_universe
- selection_signals
- source_references
- eligibility_filter_results
- attention_filter_results
- notes
- created_by
- created_at

## Field Definitions

### record_id

A unique identifier for the candidate selection record.

Example:

- candidate_msft_20260624

### as_of_date

The date the candidate was selected or evaluated.

Example:

- 2026-06-24

### company_name

The legal or common company name.

Example:

- Microsoft Corporation

### ticker

The market ticker symbol.

Example:

- MSFT

### exchange

The listing exchange.

Example:

- NASDAQ

### listing_country

The country of the main listing.

Example:

- United States

### sector

Optional sector classification.

Example:

- Information Technology

### industry

Optional industry classification.

Example:

- Software

### source_universe

The discovery universe or source list that produced the candidate.

Examples:

- S&P 500
- Saudi Listed Market
- Manual Watchlist
- User Supplied Candidate

### selection_reason

A short explanation of why the company was selected for Pipeline preparation.

This must be a routing reason, not an investment recommendation.

Allowed example:

- Selected for Pipeline preparation because it passed initial eligibility filters and matched user watchlist interest.

Disallowed example:

- Selected because it is a buy.

### selection_signals

Non-decisional discovery signals that explain attention.

Examples:

- passed_initial_eligibility
- user_watchlist_match
- sector_relevance
- financials_available
- operating_revenue_visible

These signals are not buy signals.

### source_references

Optional source references used during discovery.

These may include official exchange pages, company investor relations pages, filings pages, or other source metadata.

### eligibility_filter_results

Results of initial kill-filter checks.

Required checks should align with:

1. listed and traded on an organized financial market
2. official, recent, and reliable financial statements available
3. real operating revenues from a clear operating activity

These are discovery checks only.

They do not replace Pipeline evidence validation.

### attention_filter_results

Optional positive or attention filters used to prioritize candidate routing.

These are not investment rankings.

### pipeline_ready_intake_payload

A single-company payload that can be passed to the Single-Company Pipeline.

It should include only one company.

Expected fields:

- company_name
- ticker
- exchange
- listing_country
- as_of_date
- requested_output

Optional fields may include:

- sector
- industry
- source_references

### safety_boundary

A required statement confirming that the record is discovery and routing only.

It must state that the record does not contain:

- buy recommendation
- sell recommendation
- ranking
- allocation
- trade signal
- execution instruction
- investor-agent decision
- auto-promotion

## Example Candidate Selection Record

```json
{
  "record_id": "candidate_msft_20260624",
  "as_of_date": "2026-06-24",
  "company_name": "Microsoft Corporation",
  "ticker": "MSFT",
  "exchange": "NASDAQ",
  "listing_country": "United States",
  "sector": "Information Technology",
  "industry": "Software",
  "source_universe": "Manual Watchlist",
  "selection_reason": "Selected for Pipeline preparation because it passed initial eligibility filters and matched user watchlist interest.",
  "selection_signals": [
    "passed_initial_eligibility",
    "user_watchlist_match",
    "financials_available",
    "operating_revenue_visible"
  ],
  "eligibility_filter_results": {
    "listed_on_organized_market": true,
    "official_financials_available": true,
    "real_operating_revenue_visible": true
  },
  "pipeline_ready_intake_payload": {
    "company_name": "Microsoft Corporation",
    "ticker": "MSFT",
    "exchange": "NASDAQ",
    "listing_country": "United States",
    "as_of_date": "2026-06-24",
    "requested_output": ["package_readiness"]
  },
  "safety_boundary": {
    "discovery_and_routing_only": true,
    "no_buy_recommendation": true,
    "no_sell_recommendation": true,
    "no_ranking": true,
    "no_allocation": true,
    "no_trade_signal": true,
    "no_execution_instruction": true,
    "no_investor_agent_decision": true,
    "no_auto_promotion": true
  }
}
```

## Validation Expectations

Future validation should ensure:

- one record represents one company only
- required fields are present
- pipeline_ready_intake_payload contains one company only
- requested_output remains preparation-only
- safety_boundary is present
- no recommendation or trade instruction fields are allowed

## Explicitly Forbidden Fields

The Candidate Selection Record must not include:

- recommendation
- buy_recommendation
- sell_recommendation
- rating
- rank
- target_price
- position_size
- allocation
- portfolio_weight
- trade_signal
- entry_price
- exit_price
- stop_loss
- execution_instruction
- investor_decision
- auto_promotion

## Safety Boundary

The Candidate Selection Record is discovery and routing only.

It does not replace the Pipeline.

It does not replace the Aggregator or Decision Agent.

It does not authorize investor-agent execution.

It only identifies one company candidate that may be sent into the Single-Company Pipeline.

## Recommended Next Task

Task 146-1C should document a minimal Company Selection Agent MVP path.

The MVP should start from a manually supplied candidate list and emit one Candidate Selection Record without live market scanning.
