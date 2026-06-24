# Task 144-18 - Intake-to-Package CLI Safety Contract

## Status

Completed.

## Purpose

This document defines the safety contract that must be satisfied before any CLI command is added for the Intake-to-Package MVP.

The CLI is not implemented in this task.

This task only defines the allowed and blocked boundaries for a future CLI command.

## Current CLI Status

CLI remains blocked.

No CLI command has been added for the Intake-to-Package MVP.

## Proposed Future CLI Command

Allowed future command name:

- intake-to-package

Alternative command names are not approved unless this contract is updated.

## Allowed CLI Purpose

The future CLI may only generate preparation-only Intake-to-Package artifacts.

It may:

- validate intake
- build evidence checklist
- classify package readiness
- render a safe readiness report
- write markdown artifact
- write JSON artifact
- update latest manifest

## Allowed Inputs

The future CLI may accept:

- company_name
- ticker
- exchange
- listing_country
- as_of_date
- optional sector
- optional industry
- optional fiscal_period
- optional official_filings source references
- optional financial_statement_sources source references
- optional market_data_sources source references
- optional operator_notes
- optional output_root
- optional run_id

## Allowed Outputs

The future CLI may output only:

- run_id
- output directory path
- markdown report path
- JSON report path
- latest manifest path
- readiness label
- human_review_required
- allowed_next_step

## Allowed Artifact Paths

The future CLI may write under:

- data/outputs/intake_to_package/<run_id>/package_readiness_report.md
- data/outputs/intake_to_package/<run_id>/package_readiness_report.json
- data/outputs/intake_to_package/latest_package_readiness_manifest.json

## Allowed Readiness Labels

The future CLI may expose only these labels:

- not_ready
- partial
- ready_for_human_review

These labels are preparation-only.

They must not be described as investment approval, investment quality, investability, attractiveness, or execution readiness.

## Human Review Requirement

The future CLI must preserve:

- human_review_required: true

Ready for human review does not mean approved.

Ready for human review does not mean recommended.

Ready for human review does not mean investable.

Ready for human review does not mean executable.

## Explicitly Blocked Outputs

The future CLI must not output:

- recommendation
- ranking
- allocation
- portfolio weight
- rebalancing instruction
- buy signal
- sell signal
- trade signal
- execution instruction
- investor decision
- persona review
- strategy validation
- auto-promotion

## Explicitly Blocked Workflows

The future CLI must not call:

- investor agents
- persona review workflows
- investor decision workflows
- broker deal execution workflows
- portfolio manager execution workflows
- ranking workflows
- allocation workflows
- trading workflows
- backtesting workflows
- strategy validation workflows
- auto-promotion workflows

## Required Safety Text

Any future CLI output must include or preserve this safety boundary:

Preparation-only output. No investor-agent execution, persona review, recommendation, ranking, allocation, rebalancing, trade signal, execution instruction, strategy validation, or auto-promotion.

## Required Tests Before CLI Approval

Any future CLI implementation must include tests confirming:

- the CLI writes markdown artifacts
- the CLI writes JSON artifacts
- the CLI updates latest manifest
- the CLI preserves the safety boundary
- the CLI keeps human_review_required true
- the CLI blocks investment requested outputs
- the CLI does not call investor-agent execution
- the CLI does not expose recommendations
- the CLI does not expose rankings
- the CLI does not expose allocations
- the CLI does not expose trade signals

## Required Implementation Limits

Any future CLI implementation must:

- call only the Intake-to-Package artifact writer
- avoid investor-agent modules
- avoid existing broker deal workflows
- avoid portfolio workflows
- avoid signal/backtest workflows
- avoid recommendation/ranking/allocation functions

## Approval Gate

This contract does not approve CLI implementation yet.

It only defines the requirements for a possible future CLI.

Task 144-18B should close this contract.

Task 144-19A may then implement a narrow CLI only if this contract remains accepted.
