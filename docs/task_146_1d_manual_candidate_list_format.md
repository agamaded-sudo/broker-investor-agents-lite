# Task 146-1D - Manual Candidate List Format

## Status

Completed.

## Purpose

This document defines the initial manual candidate list format for the Company Selection Agent MVP.

The manual candidate list is the first safe input source for the Company Selection Agent.

It allows controlled testing before any live market scanning.

## Design Principle

The manual candidate list may contain multiple company candidates.

However, it is not passed directly into the Single-Company Pipeline.

The Company Selection Agent reads the list and emits one Candidate Selection Record at a time.

The Single-Company Pipeline still receives one company only.

## Position in Architecture

Flow:

1. Manual Candidate List
2. Company Selection Agent
3. Candidate Selection Record
4. Single-Company Pipeline
5. One preparation-only report

## Supported Format

The initial MVP should use JSON.

Reason:

- easy to inspect manually
- consistent with the current single-company JSON intake support
- supports nested source references and filter results
- safer than CSV for structured metadata

## File Shape

The manual candidate list should be one JSON object containing a candidates array.

Example filename:

- data/candidate_lists/manual_candidates.json

## Required Top-Level Fields

The manual candidate list should include:

- list_id
- as_of_date
- source_type
- candidates
- safety_boundary

## Optional Top-Level Fields

The manual candidate list may include:

- description
- created_by
- created_at
- notes

## Candidate Required Fields

Each candidate should include:

- company_name
- ticker
- exchange
- listing_country

## Candidate Optional Fields

Each candidate may include:

- sector
- industry
- source_universe
- user_priority
- user_notes
- source_references
- initial_selection_signals
- initial_eligibility_assumptions

## Field Definitions

### list_id

A unique identifier for the manual candidate list.

Example:

- manual_candidates_20260624

### as_of_date

The date the list is valid or prepared.

Example:

- 2026-06-24

### source_type

The source type should identify this as a manual list.

Expected MVP value:

- manual_candidate_list

### candidates

An array of company candidates.

The list may contain many candidates.

But the Selection Agent must emit one Candidate Selection Record at a time.

### user_priority

Optional user-supplied priority for routing order.

Allowed values may include:

- high
- medium
- low

This is not an investment ranking.

It only helps decide routing order for Pipeline preparation.

### initial_selection_signals

Optional non-decisional signals that explain why the user included the company.

Examples:

- user_watchlist_match
- sector_interest
- known_large_cap
- manual_test_candidate
- financials_expected_available

These are not buy signals.

### initial_eligibility_assumptions

Optional preliminary assumptions about eligibility.

These do not replace Pipeline evidence validation.

Examples:

- listed_on_organized_market
- financials_expected_available
- operating_revenue_expected_visible

### source_references

Optional source references supplied by the user or future discovery process.

These may include official investor relations pages, exchange pages, filings pages, or manually recorded source notes.

### safety_boundary

A required top-level statement confirming that the manual candidate list is discovery input only.

It must confirm the list does not contain:

- buy recommendation
- sell recommendation
- ranking for investment action
- allocation
- portfolio weight
- trade signal
- execution instruction
- investor-agent decision
- auto-promotion

## Example Manual Candidate List

```json
{
  "list_id": "manual_candidates_20260624",
  "as_of_date": "2026-06-24",
  "source_type": "manual_candidate_list",
  "description": "Small manually supplied candidate list for Selection Agent MVP testing.",
  "candidates": [
    {
      "company_name": "Microsoft Corporation",
      "ticker": "MSFT",
      "exchange": "NASDAQ",
      "listing_country": "United States",
      "sector": "Information Technology",
      "industry": "Software",
      "source_universe": "Manual Watchlist",
      "user_priority": "high",
      "initial_selection_signals": [
        "manual_test_candidate",
        "user_watchlist_match",
        "financials_expected_available"
      ],
      "initial_eligibility_assumptions": {
        "listed_on_organized_market": true,
        "official_financials_expected_available": true,
        "operating_revenue_expected_visible": true
      }
    },
    {
      "company_name": "Apple Inc.",
      "ticker": "AAPL",
      "exchange": "NASDAQ",
      "listing_country": "United States",
      "sector": "Information Technology",
      "industry": "Consumer Electronics",
      "source_universe": "Manual Watchlist",
      "user_priority": "medium",
      "initial_selection_signals": [
        "manual_test_candidate",
        "user_watchlist_match"
      ]
    }
  ],
  "safety_boundary": {
    "manual_discovery_input_only": true,
    "no_buy_recommendation": true,
    "no_sell_recommendation": true,
    "no_investment_ranking": true,
    "no_allocation": true,
    "no_portfolio_weight": true,
    "no_trade_signal": true,
    "no_execution_instruction": true,
    "no_investor_agent_decision": true,
    "no_auto_promotion": true
  }
}
```

## Validation Expectations

Future validation should ensure:

- the top-level object contains candidates
- candidates is an array
- each candidate has required identity fields
- no forbidden investment decision fields are present
- safety_boundary is present
- user_priority is treated as routing priority only
- the list is never passed directly into the Single-Company Pipeline

## Explicitly Forbidden Fields

The manual candidate list and candidate objects must not include:

- recommendation
- buy_recommendation
- sell_recommendation
- rating
- investment_rank
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

## Correct Usage

Correct pattern:

- manual list contains MSFT, AAPL, NVDA
- Selection Agent reads the list
- Selection Agent chooses one candidate for routing
- Selection Agent emits one Candidate Selection Record
- Pipeline receives one company payload

Incorrect pattern:

- manual list is passed directly into the Pipeline
- Pipeline processes all candidates
- Pipeline compares candidates
- Pipeline recommends the best candidate

## MVP Scope

The first implementation should support:

- reading one manual JSON candidate list
- validating safe structure
- selecting one candidate by simple routing rule
- emitting one Candidate Selection Record

The first implementation should not support:

- live market scanning
- investment ranking
- buy or sell recommendations
- investor-agent execution
- report aggregation

## Recommended Next Task

Task 146-1E should define the first simple routing rule for the manual-list MVP.

The routing rule should select one candidate for Pipeline preparation without ranking investment attractiveness.
