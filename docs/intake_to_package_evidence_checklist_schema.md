# Intake-to-Package Evidence Checklist Schema

## Status

Drafted.

## Purpose

This document defines the minimum safe evidence checklist schema for the Intake-to-Package MVP.

The checklist identifies evidence categories required before package readiness can be assessed.

It does not trigger investor-agent execution, persona review, recommendations, rankings, allocations, trade signals, execution instructions, strategy validation, or auto-promotion.

## Scope

This schema is for evidence preparation only.

It supports checking whether required evidence categories are present, missing, partial, stale, unverified, or ready for human review.

It does not support investment decisions, company scoring, investor conclusions, portfolio decisions, rankings, ratings, or trade actions.

## Checklist Object

Suggested object name: IntakeToPackageEvidenceChecklist

## Required Top-Level Fields

- company_name
- ticker
- exchange
- listing_country
- as_of_date
- evidence_items
- checklist_status
- missing_evidence_count
- human_review_required

## Evidence Item Object

Suggested object name: EvidenceChecklistItem

Each evidence item should include:

- category
- requirement
- status
- source_references
- freshness_status
- verification_status
- notes

## Required Evidence Categories

The MVP should check these evidence categories:

1. company_identity
2. listing_and_exchange
3. official_financial_statements
4. operating_revenue
5. balance_sheet
6. cash_flow
7. business_model_or_segments
8. source_metadata
9. evidence_freshness
10. missing_evidence_summary

## Evidence Item Status Values

Allowed status values:

- missing
- partial
- present
- not_applicable

These are evidence-status labels only. They do not imply investability, quality, attractiveness, or recommendation.

## Freshness Status Values

Allowed freshness_status values:

- current
- stale
- unknown
- not_applicable

Freshness should be based on the as-of date and the publication date of the source.

## Verification Status Values

Allowed verification_status values:

- verified
- partially_verified
- unverified
- failed
- not_applicable

Verification status should describe source traceability and reliability only.

## Checklist Status Values

Allowed checklist_status values:

- incomplete
- partial
- ready_for_human_review

These labels must not be interpreted as investment decisions.

## Category Definitions

### company_identity

Purpose: Confirm the company identity is clear.

Expected evidence examples:

- official company name
- ticker
- exchange
- listing country
- company website or official filing

### listing_and_exchange

Purpose: Confirm the company is listed and traded on an organized financial market.

Expected evidence examples:

- exchange listing page
- official market profile
- ticker metadata

### official_financial_statements

Purpose: Confirm official, recent, and reliable financial statements are available.

Expected evidence examples:

- annual report
- quarterly report
- official filing
- official regulator database record

### operating_revenue

Purpose: Confirm the company has real operating revenue from a clear core activity.

Expected evidence examples:

- income statement revenue
- segment revenue
- management discussion of business activity

### balance_sheet

Purpose: Confirm balance sheet evidence is available.

Expected evidence examples:

- assets
- liabilities
- equity
- debt disclosures

### cash_flow

Purpose: Confirm cash flow evidence is available.

Expected evidence examples:

- operating cash flow
- investing cash flow
- financing cash flow
- capital expenditure

### business_model_or_segments

Purpose: Confirm the company business model or segment structure is understandable.

Expected evidence examples:

- segment reporting
- revenue breakdown
- product or service description
- business overview

### source_metadata

Purpose: Confirm sources have traceable metadata.

Expected evidence examples:

- source title
- source type
- publication date
- access date
- reliability label

### evidence_freshness

Purpose: Confirm evidence is recent enough for package preparation.

Expected evidence examples:

- publication dates
- reporting periods
- as-of date comparison

### missing_evidence_summary

Purpose: Summarize missing or incomplete evidence categories.

Expected evidence examples:

- list of missing categories
- partial categories
- unresolved verification gaps

## Blocked Checklist Content

The checklist must not include:

- buy labels
- sell labels
- hold labels
- investment ratings
- rankings
- portfolio weights
- valuation conclusions
- investor decisions
- trade signals
- execution instructions
- strategy validation results

## Human Review Trigger Rules

Human review should be required if:

1. Any required evidence category is missing.
2. Any official source is unverified.
3. Financial statements are missing or stale.
4. Operating revenue evidence is missing.
5. Source metadata is incomplete.
6. Requested output includes blocked investment output.

## Example Minimal Checklist Summary

company_name: Microsoft Corporation
ticker: MSFT
as_of_date: 2026-06-24
checklist_status: partial
missing_evidence_count: 2
human_review_required: true

## Acceptance Criteria

This schema is acceptable if it:

1. Defines required evidence categories.
2. Defines evidence item fields.
3. Defines evidence status values.
4. Defines freshness status values.
5. Defines verification status values.
6. Defines checklist status values.
7. Defines human review trigger rules.
8. Avoids recommendations, rankings, allocations, and trade signals.
9. Aligns with docs/intake_to_package_mvp_plan.md.
10. Aligns with docs/intake_to_package_intake_schema.md.

## Future Implementation Notes

Future code implementation should begin with pure checklist construction and validation functions before any CLI is added.

Suggested future modules, if implementation is approved later:

- src/broker_agents/intake_to_package/evidence_checklist.py
- tests/test_intake_to_package_evidence_checklist.py

No implementation is approved by this documentation alone.

## Safety Boundary

This checklist schema does not allow investment action, investor-agent execution, actual persona review, ranking, recommendation, portfolio construction, allocation, rebalancing, trade signal, execution instruction, or strategy validation.

It only defines safe evidence checklist fields for package preparation.
