# Intake-to-Package Implementation Sequence

## Status

Drafted.

## Purpose

This document defines the safest implementation sequence for the Intake-to-Package MVP.

The goal is to move from documentation toward future code in a controlled order without triggering investor-agent execution, persona review, recommendations, rankings, allocations, trade signals, execution instructions, strategy validation, or auto-promotion.

## Current Documentation Stack

The MVP currently has these core documents:

1. docs/intake_to_package_mvp_plan.md
2. docs/intake_to_package_intake_schema.md
3. docs/intake_to_package_evidence_checklist_schema.md
4. docs/intake_to_package_readiness_schema.md

## Implementation Principle

Implementation should begin with pure, deterministic, testable functions.

No CLI command should be added until the core functions, tests, outputs, and safety boundaries are reviewed.

## Proposed Implementation Order

### Step 1 - Intake Validation

Purpose:

- Validate company or ticker intake.
- Detect missing identity fields.
- Detect blocked requested outputs.
- Produce non-investment completeness labels only.

Possible future module:

- src/broker_agents/intake_to_package/intake_schema.py

Possible future tests:

- tests/test_intake_to_package_intake_schema.py

Allowed outputs:

- incomplete
- minimum_identity_complete
- ready_for_evidence_checklist

Blocked outputs:

- recommendation
- ranking
- allocation
- buy_signal
- sell_signal
- investor_decision

### Step 2 - Evidence Checklist Construction

Purpose:

- Build a checklist from validated intake.
- Identify required evidence categories.
- Mark evidence items as missing, partial, present, or not_applicable.
- Track freshness and verification status.

Possible future module:

- src/broker_agents/intake_to_package/evidence_checklist.py

Possible future tests:

- tests/test_intake_to_package_evidence_checklist.py

Allowed outputs:

- evidence checklist
- missing evidence count
- checklist status
- human review required flag

### Step 3 - Package Readiness Classification

Purpose:

- Translate intake and checklist results into package readiness labels.
- Keep all labels non-investment and preparation-only.

Possible future module:

- src/broker_agents/intake_to_package/readiness.py

Possible future tests:

- tests/test_intake_to_package_readiness.py

Allowed readiness labels:

- not_ready
- partial
- ready_for_human_review

### Step 4 - Report Rendering

Purpose:

- Render safe human-readable preparation reports.
- Summarize intake, missing evidence, source verification status, and package readiness.

Possible future module:

- src/broker_agents/intake_to_package/reporting.py

Possible future tests:

- tests/test_intake_to_package_reporting.py

Allowed reports:

- intake summary
- evidence checklist report
- missing evidence report
- package readiness report

### Step 5 - Runtime Artifact Writer

Purpose:

- Write safe runtime artifacts under ignored output folders.

Possible future output folder:

- data/outputs/intake_to_package/<run_id>/

Possible artifacts:

- intake_summary.json
- evidence_checklist.json
- missing_evidence_report.md
- package_readiness.md
- latest_intake_to_package_manifest.json

Runtime outputs should remain ignored by Git.

### Step 6 - Safety Review Before CLI

Purpose:

- Review whether a CLI command is safe to add.
- Confirm the command only prepares evidence and readiness artifacts.
- Confirm no investor-agent execution or investment output is possible.

No CLI should be added before this review is complete.

### Step 7 - Optional CLI After Approval

Purpose:

- Add a narrow preparation-only CLI command if approved later.

Possible future command name:

- prepare-intake-package

The command must not call blocked commands or investor-agent workflows.

## Blocked Implementation Shortcuts

Do not start with:

- CLI first
- investor-agent execution
- run-deal
- analyze-stock
- analyze-batch
- portfolio-readiness
- backtest-signals
- recommendations
- rankings
- allocation logic
- trade signal logic
- auto-promotion logic

## Required Test Discipline

Every implementation task should include tests before commit.

Verification commands:

- python -m ruff check .
- python -m pytest --basetemp=.pytest_tmp_current

Temporary pytest folder should be removed before and after pytest.

## Acceptance Criteria

This implementation sequence is acceptable if it:

1. Starts with pure intake validation.
2. Builds evidence checklist second.
3. Adds readiness classification third.
4. Adds report rendering only after schemas are stable.
5. Delays CLI until safety review.
6. Keeps all labels non-investment.
7. Blocks investor-agent execution.
8. Blocks recommendations, rankings, allocations, and trade signals.
9. Preserves human review as the final MVP gate.
10. Aligns with the current safe operations guide and CLI command map.

## Recommended Next Task

Task 144-11B should close this implementation sequence documentation.

After that, Task 144-12A may begin the first code task only if approved:

- create a minimal intake_to_package package skeleton
- add pure intake validation functions
- add tests

## Safety Boundary

This implementation sequence does not approve any code execution path that generates investment action, investor-agent execution, actual persona review, ranking, recommendation, portfolio construction, allocation, rebalancing, trade signal, execution instruction, or strategy validation.

It only defines the safe order for future MVP implementation.
