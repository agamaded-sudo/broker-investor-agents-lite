# Restart Checklist

## Purpose

This checklist is the first document to read when resuming work on the Broker Investor Agents project.

It gives the minimum safe startup steps after Phase 19 closure and the simplified operational workflow reset.

## Current Baseline

Current phase:

- Phase 19 - Limited Preparation Governance Layer

Current phase status:

- Closed with warnings

Current operating direction:

- Simplified operational workflow

Primary safety guide:

- `docs/safe_operations_guide.md`

Machine-readable command map:

- `docs/cli_command_map.json`

## Safe Startup Steps

1. Confirm correct project path:

   - `C:\Projects\broker_investor_agents`

2. Confirm forbidden path is not being used:

   - Do not use:
     - `C:\Users\agali\OneDrive\Documents\broker-investor-agents\broker_investor_agents`

3. Check Git status:

   - `git status`

4. Read the current safety baseline:

   - `docs/safe_operations_guide.md`

5. Read the command map before running any project command:

   - `docs/cli_command_map.json`

6. Confirm the intended work is one of:

   - documentation
   - status reporting
   - command inventory
   - workflow mapping
   - safe local artifact inspection
   - command-map refinement
   - safety-boundary documentation

7. Do not run blocked commands.

8. If any file is changed, verify:

   - `python -m ruff check .`
   - `python -m pytest --basetemp=.pytest_tmp_current`

9. Clean pytest temp folder:

   - `Remove-Item .pytest_tmp_current -Recurse -Force -ErrorAction SilentlyContinue`

10. Commit only specific files:

    - `git add <specific file>`
    - `git commit -m "<clear commit message>"`
    - `git status`

## Blocked Commands

Do not run these commands without explicit approval:

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

Do not run casually. Review first:

- `run-evidence-decision-gate`
- `readiness-dashboard`
- `audit-candidates`
- `compare-many`

## Safety Boundary

This checklist does not allow:

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

## Recommended Next Step After Restart

After this checklist is confirmed, choose one safe micro-task and execute it with verification and commit discipline.
