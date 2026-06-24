# Task 144-3 - Ambiguous CLI Command Review

## Status

Initial ambiguous command review documented.

## Purpose

This document reviews CLI commands that were marked as requiring further inspection in the CLI command map.

The goal is to clarify which commands can remain allowed-with-review and which commands should be treated as blocked or high-risk under the current simplified operational workflow.

## Inspection Method

- Source inspected: `src/broker_agents/cli.py`
- Method: Python AST inspection of selected function bodies.
- No CLI command was executed.
- No source file was modified.

## Commands Reviewed

The following ambiguous commands were inspected:

- `run-deal`
- `run-deals`
- `analyze-stock`
- `analyze-batch`
- `generate-readiness-trial-decision-report`
- `run-evidence-decision-gate`
- `readiness-dashboard`
- `audit-candidates`
- `compare-many`

## Key Findings

### `run-deal`

Function:

- `run_deal`

Docstring:

- Run one Backoffice-to-investor broker deal workflow.

Important internal calls:

- `run_broker_deal_workflow`

Assessment:

- This command appears to execute a broker deal workflow.
- It may generate investor-facing workflow artifacts.
- It should not be treated as a simple research/status command.

Recommended classification:

- `blocked_high_risk_until_explicit_approval`

### `run-deals`

Function:

- `run_deals`

Docstring:

- Run broker deal workflows for multiple tickers without stopping the batch.

Important internal calls:

- `run_broker_deal_workflow`

Assessment:

- This is a batch workflow execution command.
- It is more operationally risky than `run-deal` because it can run multiple workflows.

Recommended classification:

- `blocked_high_risk_until_explicit_approval`

### `analyze-stock`

Function:

- `analyze_stock`

Docstring:

- Run intake and the complete existing broker deal workflow for one ticker.

Important internal calls:

- `execute_analyze_stock`
- `archive_completed_run`
- `build_ticker_analyze_stock_intake`
- `load_analyze_stock_intake`

Assessment:

- This command runs a complete existing broker deal workflow for one ticker.
- It should not be treated as a simple analysis helper under current boundaries.

Recommended classification:

- `blocked_high_risk_until_explicit_approval`

### `analyze-batch`

Function:

- `analyze_batch`

Docstring:

- Run the existing analyze-stock pipeline for a batch of inputs.

Important internal calls:

- `execute_analyze_stock`
- `create_analyze_batch_bundle`
- `archive_completed_run`

Assessment:

- This is a batch version of `analyze-stock`.
- It can execute multiple analysis workflows.
- It should be blocked until explicit approval.

Recommended classification:

- `blocked_high_risk_until_explicit_approval`

### `generate-readiness-trial-decision-report`

Function:

- `generate_readiness_trial_decision_report`

Docstring:

- Regenerate conservative decision artifacts for a readiness trial.

Important internal calls:

- `regenerate_readiness_trial_decision_report`

Assessment:

- The command name and docstring include decision artifacts.
- Even if conservative, it overlaps with current blocked decision territory.
- It should remain unavailable until the decision-artifact boundary is reviewed.

Recommended classification:

- `blocked_high_risk_until_explicit_approval`

### `run-evidence-decision-gate`

Function:

- `run_evidence_decision_gate`

Docstring:

- Evaluate whether readiness research may expand its sample.

Important internal calls:

- `write_evidence_decision_gate_report`
- `find_latest_evidence_gate_backtest`

Assessment:

- This is a governance/research expansion gate, not direct investor execution.
- However, the term decision gate requires care.
- It can remain governance-only but should continue requiring review.

Recommended classification:

- `governance_only`

Recommended flags:

- `allowed_now`: true
- `requires_review`: true

### `readiness-dashboard`

Function:

- `readiness_dashboard`

Docstring:

- Generate the deterministic investor-agent readiness dashboard.

Important internal calls:

- `generate_investor_agent_readiness_dashboard`

Assessment:

- This is a status/readiness report.
- It mentions investor-agent readiness but does not appear to execute investor agents.
- It can remain safe/status with review.

Recommended classification:

- `safe_status_documentation`

Recommended flags:

- `allowed_now`: true
- `requires_review`: true

### `audit-candidates`

Function:

- `audit_candidates`

Docstring:

- Audit provisional candidate decisions without changing final decisions.

Important internal calls:

- `generate_decision_candidate_audit`
- `load_portfolio_context`

Assessment:

- This audits provisional candidate decisions.
- It does not change final decisions, but it overlaps with decision-candidate territory.
- It should remain safe/status only with review.

Recommended classification:

- `safe_status_documentation`

Recommended flags:

- `allowed_now`: true
- `requires_review`: true

### `compare-many`

Function:

- `compare_many`

Docstring:

- Compare independent agent outputs across multiple companies.

Important internal calls:

- `generate_multi_company_comparison`
- `load_portfolio_context`

Assessment:

- This compares independent agent outputs across companies.
- It could be mistaken for ranking or recommendation support.
- It should remain safe/status only with review.

Recommended classification:

- `safe_status_documentation`

Recommended flags:

- `allowed_now`: true
- `requires_review`: true

## Recommended Command Map Changes

The following commands should move from research/data-preparation to blocked/high-risk:

- `run-deal`
- `run-deals`
- `analyze-stock`
- `analyze-batch`
- `generate-readiness-trial-decision-report`

The following commands should keep their existing category but remain review-gated:

- `run-evidence-decision-gate`
- `readiness-dashboard`
- `audit-candidates`
- `compare-many`

## Safety Boundaries Preserved

This review does not allow:

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

This task is documentation-only. It does not update `docs/cli_command_map.json`, modify CLI behavior, execute CLI commands, hide commands, rename commands, add commands, or remove commands.

## Recommended Next Task

Task 144-3C should update `docs/cli_command_map.json` to reflect these reviewed classifications.
