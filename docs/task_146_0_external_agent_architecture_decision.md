# Task 146-0 - External Agent Architecture Decision

## Status

Completed.

## Purpose

This document records the architecture after closing the Intake Input Scaling Layer.

The Single-Company Pipeline boundary is fixed.

Future multi-company logic must live outside the Pipeline.

## Final Architecture

The system is split into three separate components:

1. Company Selection Agent
2. Single-Company Pipeline
3. Report Aggregator / Decision Agent

## Component 1 - Company Selection Agent

The Company Selection Agent is a separate future agent.

Its role is to find or select which company should enter the Pipeline next.

It may later search:

- S&P 500
- Saudi listed market
- Nasdaq or other markets
- custom watchlists
- sector lists
- manually supplied company candidates
- user-provided company data

## Company Selection Agent Allowed Outputs

The Company Selection Agent may output:

- one selected company candidate
- a candidate intake payload
- a reason for sending the company to the Pipeline
- source references for the selected candidate
- a queue of candidates for later single-company Pipeline runs

## Company Selection Agent Boundaries

The Company Selection Agent must not be confused with the Pipeline.

It must not:

- generate the Pipeline readiness report
- replace the Pipeline
- run investor agents
- produce final buy or sell decisions
- assign portfolio weights
- produce execution instructions

## Component 2 - Single-Company Pipeline

The Pipeline is the current Intake-to-Package workflow.

It receives one company per run.

Input:

- one company intake payload

Output:

- one preparation-only package readiness report

The Pipeline may validate intake, build evidence checklist, classify readiness, render reports, and write artifacts.

## Single-Company Pipeline Boundaries

The Pipeline must not:

- scan markets
- select companies
- process many companies in one run
- compare companies
- rank companies
- recommend buy or sell
- aggregate many reports into a decision
- act as a portfolio manager
- run investor agents
- auto-promote companies

## Component 3 - Report Aggregator / Decision Agent

The Report Aggregator or Decision Agent is a separate future agent.

Its role is to collect outputs from multiple sources.

It may later collect:

- multiple Pipeline reports
- investor-agent reports
- market data reports
- source verification reports
- portfolio context reports
- user-provided notes

## Report Aggregator / Decision Agent Future Role

The Aggregator or Decision Agent may later:

- compare companies
- rank opportunities
- produce buy or sell views
- support portfolio decisions
- summarize risks across companies
- generate action candidates for human review

## Report Aggregator / Decision Agent Boundaries

The Aggregator is not part of the Single-Company Pipeline.

It must be developed separately with its own safety boundaries, tests, and governance.

## Orchestration Rule

A future Orchestrator or Runner may call the Pipeline multiple times.

However, each Pipeline run remains single-company.

Correct pattern:

- Selection Agent selects MSFT
- Pipeline runs for MSFT
- Selection Agent selects AAPL
- Pipeline runs for AAPL
- Aggregator later collects MSFT and AAPL reports

Incorrect pattern:

- Pipeline receives the full S&P 500 in one run
- Pipeline compares all companies
- Pipeline recommends which company to buy

## Safety Boundary

The current Pipeline remains preparation-only.

It does not allow:

- investor-agent execution
- persona review
- investor decisions
- company recommendations
- company rankings
- allocations
- portfolio weights
- rebalancing instructions
- buy signals
- sell signals
- trade signals
- execution instructions
- strategy validation
- auto-promotion

## Roadmap Implication

The next implementation phase should not add batch processing inside the Pipeline.

Instead, future work should define the Company Selection Agent as a separate component.

## Recommended Next Task

Task 146-1A should define the Company Selection Agent requirements and boundaries.

The Company Selection Agent should be designed as a discovery and routing agent, not as the Single-Company Pipeline and not as the final recommendation engine.
