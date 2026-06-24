# Task 144-0 - Simplified Workflow Decision Note

## Status

Proposed and documented.

## Purpose

This note records the post-Phase 19 direction decision before starting any new implementation work.

Phase 19 was closed with warnings through a minimal closure path. The project will not continue into additional heavy governance layers by default. The next direction should be a lighter, cleaner workflow that makes the Broker Investor Agents project easier to operate, inspect, and maintain.

## Where We Are Now

Current Phase:

- Phase 19 - Limited Preparation Governance Layer

Current Phase Status:

- Closed with warnings

Latest Stable Phase 19 Closure Run ID:

- 20260620_061039

Latest Stable Source Gatekeeper Review Run ID:

- 20260619_201936

Current Task:

- Task 144-0 - Simplified Workflow Decision Note

Task Status:

- Documentation-only decision note

Next Direct Step:

- Choose the simplest practical workflow path before implementing Task 144-1.

Is the next task the last task in the phase?

- No. Task 144-0 is a decision note only. It opens a simplified post-governance workflow direction.

Next Phase After Current Direction:

- Not assigned yet. The next phase should be named only after the simplified workflow is selected.

## Decision

Pause further heavy governance-layer expansion.

Move toward a simplified operational workflow that supports the Broker Investor Agents system without enabling actual investor-agent execution, actual persona review, investment recommendations, company rankings, allocations, rebalancing, trade signals, execution instructions, strategy validation, or auto-promotion.

## Candidate Simplified Workflow Paths

### Option A - CLI Cleanup and Command Map

Create a clear command map for the existing CLI and identify which commands are safe, governance-only, research-only, or blocked.

Expected value:

- Easier operation.
- Less confusion.
- Lower risk of accidentally running the wrong layer.
- Useful before any broader workflow build.

### Option B - Intake-to-Package MVP Workflow

Build a simplified workflow from company intake to limited preparation package only.

Expected value:

- More practical path.
- Supports the broker role.
- Keeps output non-actionable.
- Avoids investor-agent execution.

### Option C - Project Status Dashboard

Build a lightweight status dashboard or generated project status report.

Expected value:

- Shows phase status, latest run IDs, allowed scope, blocked scope, and next safe task.
- Helps resume work without re-reading long histories.
- Useful before expanding features.

### Option D - Governance Pause and MVP Reset

Create a short MVP reset plan that freezes heavy governance and defines the smallest usable product path.

Expected value:

- Prevents over-engineering.
- Re-centers the system around practical use.
- Keeps safety boundaries explicit.

## Preferred Direction

The preferred next direction is:

- Option C first: Project Status Dashboard or generated project status report.
- Then Option A: CLI Cleanup and Command Map.
- Then Option B: Intake-to-Package MVP Workflow.

Rationale:

A project status layer should come first because the codebase now has many phases, tasks, outputs, and safety boundaries. A lightweight status report will reduce operational confusion before any new workflow is added.

## Safety Boundaries Preserved

This decision note does not allow:

- actual persona reviews
- investor-agent execution
- investor decisions
- company recommendations
- company rankings
- allocations
- rebalancing
- trade signals
- execution instructions
- strategy validation
- auto-promotion

## Allowed Work After This Note

Allowed next work should be limited to:

- documentation
- status reporting
- command inventory
- workflow mapping
- safe local artifact inspection
- non-actionable project operations

## Blocked Work After This Note

Blocked work remains:

- running investor agents
- running actual persona reviews
- generating investment decisions
- generating recommendations
- ranking companies
- creating portfolio allocations
- producing rebalancing instructions
- producing trade signals
- producing execution instructions
- validating trading or investment strategies
- enabling auto-promotion

## Recommended Task 144-1

Task 144-1 should create a minimal project status report generator.

Suggested output:

- `project_status_report.md`
- `project_status_report.json`
- `latest_project_status_report_manifest.json`

Suggested scope:

- read latest known manifests where available
- summarize current phase and latest safe run IDs
- summarize allowed and blocked scope
- summarize recommended next safe task
- remain non-actionable

## Implementation Boundary

Task 144-0 is documentation-only. It does not add a new Python module, CLI command, runtime generator, or data output.
