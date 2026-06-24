# Task 144-2 - CLI Command Map and Safe Inventory

## Status

Completed.

## Purpose

This task created a safe inventory of the current CLI command surface and converted it into a machine-readable command map.

The purpose is to reduce operational confusion before any future CLI cleanup or workflow simplification.

## Work Completed

### Task 144-2A - CLI Inspection

- Inspected `src/broker_agents/cli.py`.
- Used Python AST inspection of `@app.command` decorators.
- No CLI command was executed.
- No source file was modified.
- Total CLI commands found: 90.

### Task 144-2B - Human-Readable Inventory

Created:

- `docs/task_144_2_cli_command_inventory.md`

The inventory classified commands into:

- Safe / status / documentation-oriented
- Governance-only
- Research / data preparation / evidence
- Blocked / high-risk until explicit approval

### Task 144-2C - Machine-Readable Command Map

Created:

- `docs/cli_command_map.json`

Command map summary:

- Total commands: 90
- Safe / status / documentation: 20
- Research / data preparation: 38
- Governance-only: 27
- Blocked / high-risk until explicit approval: 5

## Commits

- `88be43f` - Document CLI command inventory
- `a5debf6` - Add CLI command map

## Verification

Latest verification before commit:

- `python -m ruff check .` passed.
- `python -m pytest --basetemp=.pytest_tmp_current` passed.
- Test count: 908 passed.
- `git status` clean after commit.

## Current Blocked Commands

The following commands remain blocked / high-risk until explicit approval:

- `run-agent`
- `run-all-agents`
- `summarize-agents`
- `portfolio-readiness`
- `backtest-signals`

## Commands Requiring Further Review

The following commands are not blocked, but should be inspected more closely before operational use:

- `run-deal`
- `run-deals`
- `analyze-stock`
- `analyze-batch`
- `generate-readiness-trial-decision-report`
- `run-evidence-decision-gate`
- `readiness-dashboard`
- `audit-candidates`
- `compare-many`

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

## Implementation Boundary

This task did not modify CLI behavior, hide commands, rename commands, add commands, remove commands, or execute any CLI command.

## Recommended Next Task

Task 144-3 should inspect ambiguous commands one by one and decide whether each should remain allowed-with-review, become governance-only, or move to blocked.

Suggested first focus:

- `analyze-stock`
- `run-deal`
- `run-deals`
- `generate-readiness-trial-decision-report`
