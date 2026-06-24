# Safe Operations Guide

## Purpose

This guide explains how to resume work on the Broker Investor Agents project safely after Phase 19 closure and the post-phase simplified workflow reset.

It is designed to prevent accidental execution of investor-agent workflows, persona reviews, recommendations, rankings, allocations, rebalancing, trade signals, execution instructions, strategy validation, or auto-promotion.

## Current Project State

Current phase:

- Phase 19 - Limited Preparation Governance Layer

Current phase status:

- Closed with warnings

Post-phase direction:

- Simplified operational workflow

Latest known Phase 19 closure run:

- `20260620_061039`

Latest known Gatekeeper Review run:

- `20260619_201936`

Latest known Project Status Report run:

- `20260624_181823`

## Where We Are Now

Current completed tasks:

- Task 144-0 - Simplified Workflow Decision Note
- Task 144-1 - Project Status Report Generator
- Task 144-2 - CLI Command Inventory and Command Map
- Task 144-3 - Ambiguous CLI Command Review and Updated Command Map

Current next safe direction:

- Use documentation and command maps to operate the project safely.
- Avoid workflow execution until an explicit safe path is defined.

Is the next task the last task in the phase?

- No. The current direction is a simplified operational workflow, not a closed phase yet.

Next phase after current direction:

- Not assigned yet. It should only be named after the simplified workflow is stable and intentionally selected.

## First Files to Read Before Resuming Work

Read these files first:

1. `docs/task_144_0_simplified_workflow_decision_note.md`
2. `docs/task_144_1_project_status_report_summary.md`
3. `docs/task_144_2_cli_command_inventory.md`
4. `docs/cli_command_map.json`
5. `docs/task_144_3_ambiguous_cli_command_review.md`
6. `docs/task_144_3_ambiguous_cli_review_closure.md`

Optional runtime outputs, if available locally:

1. `data/outputs/project_status_reports/latest_project_status_report_manifest.json`
2. `data/outputs/phase_19_closures/latest_phase_19_closure_manifest.json`
3. `data/outputs/limited_preparation_gatekeeper_reviews/latest_limited_preparation_gatekeeper_review_manifest.json`

Runtime outputs under `data/outputs` are intentionally ignored by Git.

## Safe Start Checklist

Before doing any new work:

1. Confirm project path:
   - `C:\Projects\broker_investor_agents`

2. Confirm Git status:
   - `git status`

3. Confirm no work is being done in the forbidden path:
   - Do not use `C:\Users\agali\OneDrive\Documents\broker-investor-agents\broker_investor_agents`

4. Read the command map:
   - `docs/cli_command_map.json`

5. Confirm the task is documentation, status, command inventory, workflow mapping, or safe local artifact inspection.

6. Avoid running any blocked command.

7. After changes, verify:
   - `python -m ruff check .`
   - `python -m pytest --basetemp=.pytest_tmp_current`

8. Clean pytest temp folder after testing:
   - `Remove-Item .pytest_tmp_current -Recurse -Force -ErrorAction SilentlyContinue`

9. Commit only specific files:
   - Avoid `git add .`
   - Prefer `git add <specific file>`

## Allowed Work Now

Allowed work should remain limited to:

- documentation
- status reporting
- command inventory
- workflow mapping
- safe local artifact inspection
- non-actionable project operations
- command-map refinement
- safety-boundary documentation

## Blocked Work

The following remain blocked:

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

## Currently Blocked CLI Commands

These commands are blocked / high-risk until explicit approval:

- `run-agent`
- `run-all-agents`
- `summarize-agents`
- `portfolio-readiness`
- `backtest-signals`
- `run-deal`
- `run-deals`
- `analyze-stock`
- `analyze-batch`
- `generate-readiness-trial-decision-report`

## Review-Gated Commands

These commands are not classified as fully blocked, but should not be used casually. They require explicit review before operational use:

- `run-evidence-decision-gate`
- `readiness-dashboard`
- `audit-candidates`
- `compare-many`

## Safe Reference Commands

Safe shell checks:

- `git status`
- `python -m ruff check .`
- `Remove-Item .pytest_tmp_current -Recurse -Force -ErrorAction SilentlyContinue`
- `python -m pytest --basetemp=.pytest_tmp_current`
- `Remove-Item .pytest_tmp_current -Recurse -Force -ErrorAction SilentlyContinue`

## Recommended Operating Pattern

Use this pattern for each small task:

1. Define one micro-task.
2. Change the minimum number of files.
3. Run `ruff`.
4. Run pytest with `.pytest_tmp_current`.
5. Check `git status`.
6. Commit only the changed specific files.
7. Document the task if it affects project operation or safety.

## Commit Discipline

Preferred commit pattern:

- `git add <specific file or files>`
- `git commit -m "<clear commit message>"`
- `git status`

Avoid `git add .` unless there is a clear reason.

## Safety Boundary

This guide does not allow any investment action, investor-agent execution, actual persona review, ranking, recommendation, portfolio construction, allocation, rebalancing, trade signal, execution instruction, or strategy validation.

It is only a safe operations guide for project maintenance.

## Recommended Next Task

Task 144-4B should document a short restart checklist or add a small committed summary that closes Task 144-4 after this guide is verified.
