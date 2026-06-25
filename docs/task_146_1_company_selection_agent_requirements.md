# Task 146-1 - Company Selection Agent Requirements and Boundaries

## Status

Completed.

## Purpose

This document defines the Company Selection Agent as a separate future component.

The Company Selection Agent is responsible for discovery and routing.

It is not the Single-Company Pipeline.

It is not the Report Aggregator or Decision Agent.

## Role Definition

The Company Selection Agent identifies which company should be sent into the Single-Company Pipeline next.

Its job is to search, filter, and route candidate companies.

It does not generate the final Pipeline readiness report.

It does not produce buy or sell recommendations.

## Position in Architecture

Architecture position:

1. Company Selection Agent
2. Single-Company Pipeline
3. Report Aggregator / Decision Agent

Flow:

- Company Selection Agent selects one company candidate
- Single-Company Pipeline prepares one report for that company
- Report Aggregator / Decision Agent may later collect multiple reports

## Allowed Input Sources

The Company Selection Agent may later search or receive companies from:

- S&P 500
- Saudi listed market
- Nasdaq or other exchanges
- custom watchlists
- sector lists
- user-supplied company names
- user-supplied ticker symbols
- user-provided company data
- manually curated candidate lists

## Allowed Activities

The Company Selection Agent may:

- scan a defined universe
- apply initial eligibility filters
- apply opportunity or attention filters
- identify candidate companies
- prepare a candidate intake payload
- send one selected company to the Single-Company Pipeline
- maintain a candidate queue
- explain why a company was selected for Pipeline preparation
- attach source references for discovery purposes

## Required Output

The main output should be one selected company candidate or a queue of candidates.

For each candidate, the output may include:

- company_name
- ticker
- exchange
- listing_country
- sector
- industry
- as_of_date
- selection_reason
- selection_signals
- source_references
- pipeline_ready_intake_payload

## Relationship to the Single-Company Pipeline

The Company Selection Agent may prepare a payload that the Pipeline can consume.

However, the Pipeline remains single-company.

The Company Selection Agent may select many candidates over time, but each Pipeline run receives only one company.

Correct pattern:

- Selection Agent selects MSFT
- Pipeline runs for MSFT
- Selection Agent selects AAPL
- Pipeline runs for AAPL

Incorrect pattern:

- Pipeline receives S&P 500 directly
- Pipeline ranks all companies
- Pipeline recommends which company to buy

## What the Company Selection Agent Must Not Do

The Company Selection Agent must not:

- generate the Pipeline readiness report
- replace the Pipeline
- run investor agents
- run persona reviews
- make investor decisions
- produce final buy or sell recommendations
- assign portfolio weights
- produce trade signals
- produce execution instructions
- aggregate multiple Pipeline reports into final decisions
- auto-promote companies into investor-agent review

## Relationship to Report Aggregator / Decision Agent

The Company Selection Agent is upstream from the Pipeline.

The Report Aggregator / Decision Agent is downstream from the Pipeline.

The Company Selection Agent finds candidates.

The Pipeline prepares one-company reports.

The Aggregator may later compare reports and support recommendations.

## Initial Eligibility Filters

The Company Selection Agent should respect the existing kill filters for candidate eligibility:

1. The company is listed and traded on an organized financial market.
2. Official, recent, and reliable financial statements are available.
3. The company has real operating revenues from a clear operating activity.

These filters are discovery filters.

They do not replace Pipeline evidence validation.

## Opportunity or Attention Signals

The Company Selection Agent may later use positive signals to prioritize candidates.

Examples:

- unusual business quality signal
- strong operating revenue pattern
- improving fundamentals
- major market attention
- strategic sector relevance
- watchlist trigger
- user-specified interest

These signals are not recommendations.

They are only reasons to send a company into the Pipeline for preparation.

## Safety Boundary

The Company Selection Agent is discovery and routing only.

It must not introduce:

- investor-agent execution
- persona review
- investor decisions
- company recommendations
- company rankings for investment action
- allocations
- portfolio weights
- rebalancing instructions
- buy signals
- sell signals
- trade signals
- execution instructions
- strategy validation
- auto-promotion

## Future Implementation Notes

Future implementation should start small.

Recommended initial implementation:

- manually supplied candidate list
- select one candidate
- emit a single-company intake payload
- do not scan live markets yet
- do not rank investment attractiveness
- do not call investor agents

## Recommended Next Task

Task 146-1B should document the Company Selection Agent output schema.

The schema should define a safe Candidate Selection Record that can route one company into the Single-Company Pipeline.
