# Task 144-6 - Simplified Workflow Direction Decision

## Status

Selected.

## Purpose

This document selects the next practical direction after the simplified operational workflow reset.

The goal is to move from safety documentation toward a practical, minimal, safe workflow without reopening investor-agent execution, recommendations, rankings, allocations, trade signals, or auto-promotion.

## Current Baseline

Current phase:

- Phase 19 - Limited Preparation Governance Layer

Current phase status:

- Closed with warnings

Current operating direction:

- Simplified operational workflow

Completed post-phase tasks:

- Task 144-0 - Simplified Workflow Decision Note
- Task 144-1 - Project Status Report Generator
- Task 144-2 - CLI Command Inventory and Command Map
- Task 144-3 - Ambiguous CLI Command Review and Updated Map
- Task 144-4 - Safe Operations Guide
- Task 144-5 - Restart Checklist

## Direction Options

The following options remain important:

1. Pause and use the current documentation baseline.
2. Build a lightweight status command later.
3. Prepare a safe Intake-to-Package MVP plan.
4. Review whether the simplified workflow is ready to move toward a new phase.

## Selected Direction

Selected now:

- Option 3 - Prepare a safe Intake-to-Package MVP plan.

## Why Option 3 Now

Option 3 is the most practical next step because the project already has enough safety documentation and command mapping.

The next useful move is to define a minimal safe path from company intake to evidence package preparation, without running investor agents or producing recommendations.

This gives the project an operational shape while preserving the current safety boundaries.

## Backlog Options Kept

The other options are not rejected.

They remain available for later:

### Option 1 - Pause and use the current documentation baseline

This remains useful if the project needs to stop after establishing a clean restart baseline.

### Option 2 - Build a lightweight status command later

This remains useful after the safe workflow is clearer.

A status command should only summarize current project state and safe artifacts. It should not execute investor workflows.

### Option 4 - Review phase readiness

This remains useful after the Intake-to-Package MVP plan is documented and evaluated.

A new phase should only be named after the simplified workflow has a clear operating boundary.

## Intake-to-Package MVP Scope

The planned MVP should define a safe workflow from:

1. Company or ticker intake.
2. Evidence requirement checklist.
3. Backoffice data package preparation.
4. Missing evidence report.
5. Source verification status.
6. Package readiness status.
7. Human review gate.

The workflow should stop before:

- investor-agent execution
- persona review
- investor decision
- company ranking
- recommendation
- allocation
- trade signal
- execution instruction
- auto-promotion

## MVP Boundary

The MVP is a preparation workflow only.

It may prepare evidence and readiness artifacts.

It must not create or imply investment decisions.

## Expected Future Output

Task 144-6B or Task 144-7 should create a safe MVP plan document such as:

- `docs/intake_to_package_mvp_plan.md`

The plan should include:

- inputs
- outputs
- allowed steps
- blocked steps
- human gates
- required evidence artifacts
- command restrictions
- acceptance criteria

## Safety Boundaries Preserved

This direction does not allow:

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

## Implementation Boundary

This task is a decision note only.

It does not modify code, execute CLI commands, change CLI behavior, run investor agents, or generate investment outputs.

## Recommended Next Task

Task 144-6B should close this direction decision.

After that, Task 144-7A should create the safe Intake-to-Package MVP plan.
