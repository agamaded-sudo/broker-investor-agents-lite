# Task 144-19 - CLI Insertion-Point Inspection

## Status

Completed.

## Purpose

Task 144-19 performed a read-only inspection of the existing CLI file before any Intake-to-Package CLI implementation.

The goal was to understand the current CLI structure and confirm whether Intake-to-Package references already exist.

## Inspection Type

Read-only.

No source files were modified.

No CLI command was added.

No commit was created during the inspection step.

## Reviewed File

- src/broker_agents/cli.py

## Inspection Method

The CLI file was parsed using Python AST inspection.

The inspection counted:

- imports
- functions
- Typer command functions
- existing Intake-to-Package references

## Findings

### CLI Structure Counts

The inspection found:

- total imports: 110
- total functions: 100
- total Typer commands: 90

### Existing Intake-to-Package References

No existing references were found for:

- intake_to_package
- intake-to-package

### Existing Command Pattern

The CLI uses Typer commands with decorators such as:

- app.command('<command-name>')

### Current CLI Size

The CLI file is large and contains many historical project commands.

Because of this, any future Intake-to-Package command should be narrow, isolated, and safety-constrained.

## Safe Insertion Guidance

A future Intake-to-Package CLI implementation should:

- add only the minimal import needed from broker_agents.intake_to_package
- add only one narrow command named intake-to-package
- place the command near other safe status/documentation commands or near the end before main
- call only write_package_readiness_artifacts
- avoid investor-agent modules
- avoid broker deal workflows
- avoid portfolio workflows
- avoid signal/backtest workflows
- avoid recommendation/ranking/allocation workflows

## Safety Boundary

The inspection did not approve broad CLI work.

Any future CLI must remain bound by the CLI Safety Contract from Task 144-18.

## Verification

After the read-only inspection:

- python -m ruff check . passed.
- python -m pytest --basetemp=.pytest_tmp_current passed.
- Test count: 940 passed.
- git status was clean.

## Safety Boundaries Preserved

This task does not allow:

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

## Recommended Next Task

Task 144-20A may implement the narrow Intake-to-Package CLI if the CLI Safety Contract remains accepted.

Task 144-20A must be minimal and must include tests confirming:

- the CLI writes markdown artifacts
- the CLI writes JSON artifacts
- the CLI updates latest manifest
- the CLI preserves the safety boundary
- the CLI keeps human_review_required true
- blocked investment requested outputs remain blocked
- no investor-agent execution is reachable
