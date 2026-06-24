# Task 144-3 - Ambiguous CLI Command Review Closure

## Status

Completed.

## Purpose

Task 144-3 reviewed ambiguous CLI commands that were previously marked as requiring further review in the CLI command map.

The purpose was to reduce the risk of treating workflow-execution commands as safe research or status commands.

## Work Completed

### Task 144-3A - Safe Inspection

Inspected selected ambiguous CLI command functions using Python AST and source-level inspection.

No CLI command was executed.

Commands inspected:

- `run-deal`
- `run-deals`
- `analyze-stock`
- `analyze-batch`
- `generate-readiness-trial-decision-report`
- `run-evidence-decision-gate`
- `readiness-dashboard`
- `audit-candidates`
- `compare-many`

### Task 144-3B - Review Documentation

Created:

- `docs/task_144_3_ambiguous_cli_command_review.md`

The review concluded that several commands should be treated as blocked / high-risk because they may execute broker-deal workflows, analyze-stock workflows, batch workflows, or generate decision-adjacent artifacts.

### Task 144-3C - Command Map Update

Updated:

- `docs/cli_command_map.json`

The following commands were moved to `blocked_high_risk_until_explicit_approval`:

- `run-deal`
- `run-deals`
- `analyze-stock`
- `analyze-batch`
- `generate-readiness-trial-decision-report`

## Updated Command Map Counts

After Task 144-3C:

- Total CLI commands: 90
- Safe / status / documentation: 20
- Research / data preparation: 33
- Governance-only: 27
- Blocked / high-risk until explicit approval: 10

## Commits

- `2c6b055` - Document ambiguous CLI command review
- `4ee4e7d` - Update CLI command map reviewed classifications

## Verification

Latest verification before Task 144-3C commit:

- `python -m ruff check .` passed.
- `python -m pytest --basetemp=.pytest_tmp_current` passed.
- Test count: 908 passed.
- `git status` clean after commit.

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

This task did not modify CLI behavior, execute CLI commands, hide commands, rename commands, add commands, or remove commands.

It only updated documentation and the machine-readable command map.

## Recommended Next Task

Task 144-4 should create a lightweight safe-operation guide for the simplified workflow.

Suggested output:

- `docs/safe_operations_guide.md`

Suggested purpose:

- Explain which artifacts to check first.
- Explain which commands are blocked.
- Explain which files represent current project status.
- Give a safe restart checklist before future work.
