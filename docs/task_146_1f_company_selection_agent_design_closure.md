# Task 146-1F - Company Selection Agent Design Subphase Closure

## Status

Completed.

## Purpose

This document closes the Company Selection Agent design subphase.

The design subphase defined the Company Selection Agent as a separate discovery and routing component.

It also preserved the Single-Company Pipeline boundary.

## Completed Design Tasks

Completed:

- Task 146-1A - Company Selection Agent Requirements and Boundaries
- Task 146-1B - Candidate Selection Record Schema
- Task 146-1C - Minimal Company Selection Agent MVP Path
- Task 146-1D - Manual Candidate List Format
- Task 146-1E - First Simple Routing Rule

## Final Design Decision

The Company Selection Agent is discovery and routing only.

It chooses one company candidate to route into the Single-Company Pipeline.

It does not generate Pipeline reports.

It does not produce buy or sell recommendations.

It does not aggregate reports.

It does not replace the future Report Aggregator or Decision Agent.

## Architecture Position

Final flow:

1. Manual Candidate List
2. Company Selection Agent
3. Candidate Selection Record
4. Single-Company Pipeline
5. One preparation-only report
6. Future Report Aggregator / Decision Agent

## Fixed Boundary

The Single-Company Pipeline remains single-company.

The Pipeline receives one company payload per run.

The Pipeline produces one preparation-only report per run.

The Pipeline must not receive a full manual candidate list, market universe, or multi-company batch.

## Candidate Selection Record

The Candidate Selection Record is the safe handoff object between the Company Selection Agent and the Pipeline.

Each Candidate Selection Record represents one company only.

It contains one pipeline_ready_intake_payload.

It must preserve safety boundaries and must not include recommendation or trade instruction fields.

## Manual Candidate List

The first MVP input source is a manual JSON candidate list.

The list may contain multiple candidates.

However, the Selection Agent must emit one Candidate Selection Record at a time.

The list is never passed directly into the Single-Company Pipeline.

## First Routing Rule

The first routing rule is:

- manual_priority_then_list_order

Routing order:

1. user_priority = high
2. user_priority = medium
3. user_priority = low
4. no user_priority

If candidates have the same priority, list order decides.

This is a routing rule only.

It is not an investment ranking rule.

## MVP Non-Goals

The Company Selection Agent MVP must not:

- scan live markets
- scan the full S&P 500 live
- scan the Saudi market live
- rank candidates by investment attractiveness
- recommend buy or sell
- produce target prices
- produce portfolio weights
- produce trade signals
- produce execution instructions
- call investor agents
- call persona reviews
- aggregate multiple Pipeline reports into decisions
- auto-promote companies

## Implementation Readiness

The design subphase is now ready for minimal implementation.

The next implementation should create a small, safe, testable module for:

- manual candidate list validation
- Candidate Selection Record validation
- manual_priority_then_list_order routing
- one selected candidate output

## Suggested Implementation Scope

The first implementation should be narrow.

It should include:

1. a new company_selection package
2. manual candidate list schema models
3. Candidate Selection Record schema models
4. forbidden-field checks
5. simple routing rule implementation
6. unit tests

It should not include:

- CLI command yet, unless explicitly scoped later
- live market scanning
- API integrations
- investor-agent execution
- report aggregation
- recommendation logic

## Safety Boundary

The Company Selection Agent remains discovery and routing only.

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

## Latest Relevant Commits

- 0afbdd1 - Document external agent architecture decision
- d0c1a45 - Document company selection agent requirements
- 5c78111 - Document candidate selection record schema
- 426c6f7 - Document minimal company selection agent MVP path
- cefda19 - Document manual candidate list format
- 35855f2 - Document first company selection routing rule

## Verification

Latest stable verification:

- python -m ruff check . passed.
- python -m pytest --basetemp=.pytest_tmp_current passed.
- Test count: 949 passed.
- git status clean.

## Recommended Next Task

Task 146-2A should start the minimal Company Selection Agent schema implementation.

The first implementation should create validation models only, without CLI, live scanning, recommendation logic, investor-agent execution, or report aggregation.
