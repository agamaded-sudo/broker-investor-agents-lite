# Intake-to-Package Readiness Schema

## Status

Drafted.

## Purpose

This document defines the minimum safe package readiness schema for the Intake-to-Package MVP.

The schema explains how intake and evidence checklist results translate into non-investment readiness labels.

It does not trigger investor-agent execution, persona review, recommendations, rankings, allocations, trade signals, execution instructions, strategy validation, or auto-promotion.

## Scope

This schema is for package preparation readiness only.

It supports determining whether an evidence package is not ready, partial, or ready for human review.

It does not support investment decisions, investor conclusions, company ratings, rankings, portfolio decisions, or trade actions.

## Readiness Object

Suggested object name: IntakeToPackageReadiness

## Required Top-Level Fields

- company_name
- ticker
- exchange
- listing_country
- as_of_date
- intake_completeness_label
- checklist_status
- readiness_label
- blockers
- warnings
- human_review_required
- allowed_next_step
- blocked_next_steps

## Readiness Labels

Allowed readiness_label values:

- not_ready
- partial
- ready_for_human_review

These labels are operational preparation labels only.

They must not be interpreted as investment recommendations, investor decisions, rankings, allocations, or trade signals.

## Intake Completeness Input

The readiness schema may consume intake completeness labels from docs/intake_to_package_intake_schema.md:

- incomplete
- minimum_identity_complete
- ready_for_evidence_checklist

## Evidence Checklist Input

The readiness schema may consume checklist status values from docs/intake_to_package_evidence_checklist_schema.md:

- incomplete
- partial
- ready_for_human_review

## Blocker Object

Suggested object name: PackageReadinessBlocker

Each blocker should include:

- blocker_code
- blocker_type
- severity
- description
- related_field
- related_evidence_category
- required_human_action

Allowed severity values:

- blocking
- warning
- informational

## Warning Object

Suggested object name: PackageReadinessWarning

Each warning should include:

- warning_code
- description
- related_field
- related_evidence_category
- suggested_review_action

Warnings do not authorize investment decisions.

## Readiness Rule: not_ready

Use not_ready if any of the following applies:

1. Intake is incomplete.
2. Company identity is unclear.
3. Ticker is provided but exchange is missing.
4. As-of date is missing or invalid.
5. Requested output includes blocked investment outputs.
6. Official financial statements are missing.
7. Operating revenue evidence is missing.
8. Source verification failed.
9. Required evidence categories are mostly missing.

Allowed next step for not_ready:

- fix_intake_or_collect_missing_evidence

Blocked next steps for not_ready:

- investor_agent_execution
- persona_review
- recommendation
- ranking
- allocation
- trade_signal
- execution_instruction
- auto_promotion

## Readiness Rule: partial

Use partial if all of the following apply:

1. Minimum identity is complete.
2. Requested outputs are preparation-only.
3. Some evidence categories are present.
4. One or more evidence categories remain missing, partial, stale, or unverified.
5. Human review is required before package readiness can be accepted.

Allowed next step for partial:

- collect_remaining_evidence_or_send_to_human_review_with_gaps

Blocked next steps for partial:

- investor_agent_execution
- persona_review
- recommendation
- ranking
- allocation
- trade_signal
- execution_instruction
- auto_promotion

## Readiness Rule: ready_for_human_review

Use ready_for_human_review if all of the following apply:

1. Intake is ready for evidence checklist.
2. Required evidence categories are present or explicitly marked not applicable.
3. Source references are traceable.
4. No blocked investment output is requested.
5. Missing evidence count is zero or only non-blocking warnings remain.
6. Human review remains the next gate.

Allowed next step for ready_for_human_review:

- human_review

Blocked next steps for ready_for_human_review:

- automatic_promotion
- investor_agent_execution_without_explicit_approval
- persona_review_without_explicit_approval
- recommendation
- ranking
- allocation
- trade_signal
- execution_instruction

## Human Review Requirement

human_review_required should be true for all readiness labels in the current MVP.

Reason:

- The project is still in simplified operational workflow after Phase 19 closed with warnings.
- The MVP is preparation-only.
- No automated movement into investor-agent execution is allowed.

## Allowed Next Step Values

Allowed allowed_next_step values:

- fix_intake_or_collect_missing_evidence
- collect_remaining_evidence_or_send_to_human_review_with_gaps
- human_review

## Blocked Next Step Values

Blocked next step examples:

- investor_agent_execution
- persona_review
- investor_decision
- recommendation
- ranking
- allocation
- rebalancing
- trade_signal
- execution_instruction
- strategy_validation
- auto_promotion

## Example not_ready Summary

company_name: Unknown
ticker: MSFT
as_of_date: missing
readiness_label: not_ready
human_review_required: true
allowed_next_step: fix_intake_or_collect_missing_evidence

## Example partial Summary

company_name: Microsoft Corporation
ticker: MSFT
as_of_date: 2026-06-24
readiness_label: partial
blockers: official financial statements unverified
human_review_required: true
allowed_next_step: collect_remaining_evidence_or_send_to_human_review_with_gaps

## Example ready_for_human_review Summary

company_name: Microsoft Corporation
ticker: MSFT
as_of_date: 2026-06-24
readiness_label: ready_for_human_review
human_review_required: true
allowed_next_step: human_review

## Acceptance Criteria

This schema is acceptable if it:

1. Defines non-investment readiness labels.
2. Defines top-level readiness fields.
3. Defines blocker fields.
4. Defines warning fields.
5. Defines readiness rules for not_ready, partial, and ready_for_human_review.
6. Keeps human review required for all labels.
7. Defines allowed next steps.
8. Defines blocked next steps.
9. Avoids recommendations, rankings, allocations, and trade signals.
10. Aligns with docs/intake_to_package_mvp_plan.md.
11. Aligns with docs/intake_to_package_intake_schema.md.
12. Aligns with docs/intake_to_package_evidence_checklist_schema.md.

## Future Implementation Notes

Future code implementation should begin with pure readiness classification functions before any CLI is added.

Suggested future modules, if implementation is approved later:

- src/broker_agents/intake_to_package/readiness.py
- tests/test_intake_to_package_readiness.py

No implementation is approved by this documentation alone.

## Safety Boundary

This readiness schema does not allow investment action, investor-agent execution, actual persona review, ranking, recommendation, portfolio construction, allocation, rebalancing, trade signal, execution instruction, or strategy validation.

It only defines safe non-investment package readiness labels for evidence preparation.
