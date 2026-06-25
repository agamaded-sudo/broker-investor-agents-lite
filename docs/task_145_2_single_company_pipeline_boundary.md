# Task 145-2 - Single-Company Pipeline Boundary

## Status

Completed.

## Purpose

This document fixes the architectural boundary of the Intake-to-Package Pipeline.

The Pipeline is a single-company preparation pipeline.

It must not become a market scanner, company selector, comparison engine, recommendation engine, or portfolio decision engine.

## Final Boundary Decision

The Pipeline processes one company per run.

Input:

- one company intake payload

Output:

- one preparation-only package readiness report for that company

## What the Pipeline Does

The Pipeline may:

- receive one company intake
- validate the intake
- normalize requested preparation outputs
- block investment-output requests
- build an evidence checklist
- classify package readiness
- identify blockers
- identify warnings
- render a markdown report
- render a JSON report
- write runtime artifacts
- update the latest manifest
- require human review
- preserve the safety boundary

## What the Pipeline Must Not Do

The Pipeline must not:

- scan the S&P 500
- scan the Saudi market
- scan any full market universe
- choose which companies should enter the pipeline
- compare companies against each other
- rank companies
- recommend buy or sell
- assign portfolio weights
- produce trade signals
- produce execution instructions
- aggregate multiple company reports into a decision
- act as a portfolio manager
- run investor agents
- run persona reviews
- auto-promote a company

## Company Selection Agent Boundary

Company selection belongs to a separate future agent.

The Company Selection Agent may later:

- search the S&P 500
- search the Saudi listed market
- search a custom watchlist
- search sector lists
- receive manually supplied company data
- decide which single company should be sent into the Pipeline next

The Company Selection Agent is not part of the Single-Company Pipeline.

## Aggregator and Decision Agent Boundary

Aggregation and recommendation belong to a separate future agent.

The Aggregator or Decision Agent may later:

- collect multiple Pipeline reports
- collect reports from other sources
- compare companies
- produce recommendations
- produce buy or sell views
- support portfolio-level decisions

The Aggregator or Decision Agent is not part of the Single-Company Pipeline.

## Correct Interpretation of JSON Intake Support

Single JSON Intake File Support does not mean the Pipeline should process many companies at once.

It only means the Pipeline can receive one company intake through a structured JSON file instead of long CLI options.

Correct usage:

python -m broker_agents.cli intake-to-package --input-file data/intakes/msft.json --run-id msft_json_run

Incorrect interpretation:

- one Pipeline run processing the full S&P 500
- one Pipeline run processing the Saudi market
- one Pipeline run comparing many companies

## Correct Interpretation of Future Orchestration

A future orchestrator may run the Pipeline many times.

But each Pipeline run remains single-company.

Example:

- Selection Agent chooses MSFT
- Pipeline runs for MSFT
- Selection Agent chooses AAPL
- Pipeline runs for AAPL
- Aggregator later collects MSFT and AAPL reports

The orchestration layer may be multi-company.

The Pipeline itself remains single-company.

## Updated Roadmap Implication

The next architecture work should not add batch processing inside the Pipeline.

Instead, future work should be split into separate components:

1. Single-Company Pipeline
2. Company Selection Agent
3. Pipeline Orchestrator or Runner
4. Report Aggregator / Decision Agent

## Safety Boundary

The Single-Company Pipeline remains preparation-only.

It must not introduce:

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

## Completion Statement

The Single-Company Pipeline boundary is now fixed.

The Pipeline prepares one company report per run.

Company selection and multi-company recommendations are separate future agents.
