# Intake-to-Package MVP Plan

## Status

Drafted.

## Purpose

This document defines a minimal safe workflow from company or ticker intake to evidence package preparation.

The MVP is designed to give the Broker Investor Agents project a practical operating path while preserving current safety boundaries.

The workflow stops before investor-agent execution, persona review, investor decisions, recommendations, rankings, allocations, trade signals, execution instructions, strategy validation, or auto-promotion.

## Current Context

Current phase:

- Phase 19 - Limited Preparation Governance Layer

Current phase status:

- Closed with warnings

Current operating direction:

- Simplified operational workflow

Selected next direction:

- Safe Intake-to-Package MVP

## MVP Principle

The MVP is a preparation workflow only.

It may collect, structure, validate, and package evidence.

It must not generate or imply investment decisions.

## Intended User Role

The user acts as the broker or internal operator.

The system helps prepare a safe evidence package.

The system does not decide whether a company is attractive, investable, recommended, ranked, or suitable for allocation.

## Workflow Boundary

### Starts With

- A company name, ticker, or manually prepared intake.
- Basic identity information.
- Available official source references.
- Initial evidence requirements.

### Ends With

- Evidence package readiness status.
- Missing evidence report.
- Source verification status.
- Human review gate result.

### Stops Before

- investor-agent execution
- persona review
- investor decision
- recommendation
- ranking
- allocation
- rebalancing
- trade signal
- execution instruction
- strategy validation
- auto-promotion

## MVP Inputs

The MVP may accept:

1. Company name.
2. Ticker.
3. Exchange.
4. Sector.
5. Country or listing market.
6. Fiscal period or as-of date.
7. Available official filings.
8. Available financial statements.
9. Available market data snapshots.
10. Optional notes from the broker/operator.

## Required Evidence Categories

The MVP should check for:

1. Company identity evidence.
2. Listing and exchange evidence.
3. Official financial statements.
4. Revenue evidence from real operating activity.
5. Balance sheet evidence.
6. Cash flow evidence.
7. Segment or business model evidence.
8. Source metadata.
9. Evidence freshness.
10. Missing evidence list.

## MVP Outputs

The MVP should produce or identify:

1. Intake summary.
2. Evidence requirements checklist.
3. Backoffice preparation package outline.
4. Missing evidence report.
5. Source verification status.
6. Evidence freshness status.
7. Package readiness status.
8. Human review gate note.

## Allowed Steps

The MVP may:

- inspect existing local docs and manifests
- define intake fields
- define evidence requirements
- define package structure
- map required artifacts
- identify missing evidence categories
- mark package readiness as incomplete, partial, or ready-for-human-review
- document human gates

## Blocked Steps

The MVP must not:

- run investor agents
- run actual persona reviews
- generate investor decisions
- recommend a company
- rank companies
- assign portfolio weights
- suggest allocation
- suggest rebalancing
- produce trade signals
- produce execution instructions
- validate strategies
- auto-promote companies

## Command Restrictions

The following commands remain blocked / high-risk until explicit approval:

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

The following commands remain review-gated:

- `run-evidence-decision-gate`
- `readiness-dashboard`
- `audit-candidates`
- `compare-many`

## Human Gates

The MVP should include these human gates:

### Gate 1 - Intake Completeness

Question:

- Is the company or ticker identity clear enough to proceed?

Possible outcomes:

- incomplete
- proceed to evidence checklist
- stop and request more input

### Gate 2 - Evidence Sufficiency

Question:

- Are official, recent, and reliable evidence sources available?

Possible outcomes:

- insufficient evidence
- partial evidence
- sufficient for package preparation

### Gate 3 - Source Verification

Question:

- Are source references traceable and sufficiently reliable?

Possible outcomes:

- failed verification
- partial verification
- verified enough for human review

### Gate 4 - Package Readiness

Question:

- Is the package ready for human review?

Possible outcomes:

- not ready
- ready with gaps
- ready for human review

## Readiness Labels

The MVP should use non-investment readiness labels only:

- `not_ready`
- `partial`
- `ready_for_human_review`

The MVP must not use investment decision labels such as:

- buy
- sell
- hold
- accumulate
- avoid
- overweight
- underweight
- rank 1
- top pick

## Proposed Artifact Structure

Future implementation may produce artifacts under a safe output folder such as:

- `data/outputs/intake_to_package/<run_id>/intake_summary.json`
- `data/outputs/intake_to_package/<run_id>/evidence_checklist.json`
- `data/outputs/intake_to_package/<run_id>/missing_evidence_report.md`
- `data/outputs/intake_to_package/<run_id>/source_verification_status.json`
- `data/outputs/intake_to_package/<run_id>/package_readiness.md`
- `data/outputs/intake_to_package/latest_intake_to_package_manifest.json`

Runtime outputs should remain ignored by Git.

## Acceptance Criteria

The MVP plan is acceptable if it:

1. Defines clear inputs.
2. Defines clear outputs.
3. Defines allowed steps.
4. Defines blocked steps.
5. Defines human gates.
6. Uses non-investment readiness labels.
7. Avoids investor-agent execution.
8. Avoids recommendations, rankings, allocations, and trade signals.
9. Aligns with `docs/safe_operations_guide.md`.
10. Aligns with `docs/cli_command_map.json`.

## Future Implementation Sequence

Suggested future tasks:

1. Define intake schema.
2. Define evidence checklist schema.
3. Define package readiness schema.
4. Add pure functions for readiness classification.
5. Add tests.
6. Add optional report rendering.
7. Add CLI only after safety review.

## Safety Boundary

This MVP plan does not allow any investment action, investor-agent execution, actual persona review, ranking, recommendation, portfolio construction, allocation, rebalancing, trade signal, execution instruction, or strategy validation.

It is only a plan for safe evidence preparation and package readiness.
