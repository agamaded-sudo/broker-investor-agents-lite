# Task 146-1C - Minimal Company Selection Agent MVP Path

## Status

Completed.

## Purpose

This document defines the minimal MVP path for the Company Selection Agent.

The goal is to start safely with a manually supplied candidate list before any live market scanning.

## MVP Principle

The first Company Selection Agent MVP should be simple, controlled, and non-decisional.

It should not scan live markets.

It should not rank investment attractiveness.

It should not produce buy or sell recommendations.

It should only route one company candidate into the Single-Company Pipeline.

## MVP Input

The MVP should start from a manually supplied candidate list.

Example sources:

- user supplied company names
- user supplied tickers
- manually curated watchlist
- small test list such as MSFT, AAPL, NVDA
- later, exported universe files from external sources

## MVP Processing

The MVP may:

- read a small manually supplied candidate list
- validate that each candidate has basic required fields
- apply initial eligibility filters
- identify one candidate for routing
- create one Candidate Selection Record
- include one pipeline_ready_intake_payload
- preserve safety boundaries

## MVP Output

The MVP should output one Candidate Selection Record at a time.

The record should include:

- record_id
- as_of_date
- company_name
- ticker
- exchange
- listing_country
- selection_reason
- selection_signals
- eligibility_filter_results
- pipeline_ready_intake_payload
- safety_boundary

## MVP Flow

Correct MVP flow:

1. User provides a small candidate list.
2. Company Selection Agent reads the list.
3. Company Selection Agent selects one candidate for routing.
4. Company Selection Agent emits one Candidate Selection Record.
5. Single-Company Pipeline receives the pipeline_ready_intake_payload.
6. Single-Company Pipeline generates one preparation-only report.

## Example MVP Flow

Example:

- Candidate list contains MSFT, AAPL, NVDA.
- Selection Agent selects MSFT for Pipeline preparation.
- Selection Agent emits candidate_msft_20260624.
- Pipeline runs for MSFT only.
- Pipeline produces one MSFT package readiness report.

The remaining candidates stay outside the Pipeline until selected one by one.

## Initial Eligibility Filters

The MVP should respect the existing discovery kill filters:

1. The company is listed and traded on an organized financial market.
2. Official, recent, and reliable financial statements are available.
3. The company has real operating revenues from a clear operating activity.

These filters are discovery checks only.

They do not replace Pipeline evidence validation.

## Initial Attention Signals

The MVP may include simple non-decisional attention signals.

Examples:

- user_watchlist_match
- passed_initial_eligibility
- financials_available
- operating_revenue_visible
- sector_relevance
- manually_prioritized

These are routing signals only.

They are not buy signals, rankings, or recommendations.

## Explicit Non-Goals

The MVP must not:

- scan the full S&P 500 live
- scan the Saudi market live
- rank all companies by investment attractiveness
- recommend buy or sell
- produce target prices
- produce portfolio weights
- produce trade signals
- produce execution instructions
- call investor agents
- call persona reviews
- aggregate multiple Pipeline reports into decisions
- auto-promote companies

## Why Manual List First

Starting with a manual list reduces architectural risk.

It allows safe testing of:

- candidate record creation
- routing into the Pipeline
- safety boundary enforcement
- one-company-per-run discipline
- separation from recommendation logic

Live market scanning can be added later as a separate capability after the MVP boundary is proven.

## Future Expansion Path

After the manual-list MVP is stable, future expansion may add:

1. CSV candidate list input
2. JSON candidate list input
3. saved watchlists
4. external universe snapshots
5. market-specific adapters
6. S&P 500 discovery adapter
7. Saudi market discovery adapter

Each expansion must keep the Pipeline single-company.

## Safety Boundary

The Company Selection Agent MVP is discovery and routing only.

It must not introduce:

- investor-agent execution
- persona review
- investor decisions
- company recommendations
- investment rankings
- allocations
- portfolio weights
- rebalancing instructions
- buy signals
- sell signals
- trade signals
- execution instructions
- strategy validation
- auto-promotion

## Recommended Next Task

Task 146-1D should define the initial manual candidate list format.

The format should be simple and should support creating one Candidate Selection Record without live market scanning.
