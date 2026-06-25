# Task 145-0 - Intake Input Scaling Direction Decision

## Status

Completed.

## Purpose

This document records the corrected post-MVP direction after completing the Safe Intake-to-Package MVP.

The selected direction is not limited to one JSON file per company.

The selected direction is an Intake Input Scaling Layer that starts with single JSON intake support and later expands to universe and batch intake support.

## Previous Path Closed

The Safe Intake-to-Package MVP was completed and documented.

The MVP now includes:

- intake validation
- evidence checklist construction
- package readiness classification
- safe markdown and JSON reporting
- runtime artifact writing
- narrow CLI command
- CLI tests
- smoke test
- user-facing CLI guide
- final MVP completion summary

## Current Baseline

Current stable baseline:

- latest MVP completion commit: 2778964
- latest test count: 945 passed
- repository status after completion: clean

## Corrected Direction Decision

Selected next direction:

- Intake Input Scaling Layer

This direction includes:

1. Single JSON Intake File Support
2. Universe Intake File Support
3. Batch Intake-to-Package Processing

## Important Clarification

JSON is not intended to force manual company-by-company work.

The user should not be required to manually create separate JSON files for every company in the S&P 500, the Saudi market, or any other market.

JSON is only the first structured input format.

It allows the system to move from long CLI arguments to reusable structured inputs.

## Target Operating Model

The intended future operating model is:

- single company intake for testing or focused preparation
- universe files for groups of companies
- batch processing for many companies
- later source enrichment and evidence collection workflows

## Single Company JSON Use Case

Single JSON intake is useful for:

- testing one company
- preparing one company manually
- debugging readiness logic
- building a clear input contract
- creating examples and templates

## Universe File Use Case

Universe files are intended for:

- S&P 500
- Saudi listed companies
- watchlists
- sector lists
- custom broker/backoffice coverage lists

A universe file may contain many companies and should not require one file per company.

## Batch Processing Use Case

Batch processing is intended to run Intake-to-Package preparation across many companies from a universe file.

The batch process should generate one preparation-only output package per company or a summarized batch manifest.

## Expected Future Command Shapes

Possible future single-company command:

python -m broker_agents.cli intake-to-package --input-file data/intakes/msft.json --run-id msft_json_run

Possible future universe command:

python -m broker_agents.cli intake-to-package-batch --universe-file data/universes/sp500.json --run-id sp500_batch_run

The exact command shape may change during implementation, but the safety boundaries must not change.

## Backlog Options Preserved

The following options remain important but are deferred:

1. richer source references through CLI or JSON
2. missing evidence report enhancement
3. project status dashboard integration
4. human review queue integration
5. source verification integration

## Safety Boundary

The selected direction remains preparation-only.

The Intake Input Scaling Layer must not introduce:

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

## Implementation Requirements for Task 145-1A

Task 145-1A should implement Single JSON Intake File Support.

It should:

- accept an input JSON file
- load the JSON payload
- pass the payload to write_package_readiness_artifacts
- preserve existing CLI option behavior
- preserve the safety boundary
- preserve human_review_required
- keep investment requested outputs blocked
- include tests for valid JSON intake
- include tests for blocked requested outputs from JSON intake
- include tests that no investor-agent execution is reachable

## Future Requirement for Task 145-2A

Task 145-2A should implement Universe or Batch Intake File Support.

It should allow one file to represent many companies.

It should support markets such as:

- S&P 500
- Saudi listed companies
- custom watchlists

It must remain preparation-only.

## Recommended Next Task

Task 145-1A - Implement Single JSON Intake File Support.
