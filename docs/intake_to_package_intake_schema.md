# Intake-to-Package Intake Schema

## Status

Drafted.

## Purpose

This document defines the minimum safe intake schema for the Intake-to-Package MVP.

The schema captures the information needed to identify a company or ticker and begin evidence package preparation.

It does not trigger investor-agent execution, persona review, recommendations, rankings, allocations, trade signals, execution instructions, strategy validation, or auto-promotion.

## Scope

This schema is for preparation only.

It supports company identity capture, ticker and listing context, as-of date context, evidence source references, operator notes, and initial completeness review.

It does not support investor decisions, portfolio decisions, investment ratings, buy/sell/hold labels, rankings, or trade actions.

## Intake Object

Suggested object name: IntakeToPackageInput

## Required Fields

### company_name

Type: string

Purpose: Human-readable company name.

Validation: Must not be empty.

### ticker

Type: string

Purpose: Market ticker or trading symbol.

Validation: Required for ticker-based intake. Should be uppercase when possible.

### exchange

Type: string

Purpose: Listing exchange.

Validation: Required when ticker is provided.

### listing_country

Type: string

Purpose: Country or market where the company is listed.

Validation: Required when exchange is provided.

### as_of_date

Type: date string in YYYY-MM-DD format

Purpose: Date context for evidence preparation.

Validation: Must be a valid date. Must not be treated as an investment timing signal.

## Optional Fields

- sector
- industry
- fiscal_period
- official_filings
- financial_statement_sources
- market_data_sources
- operator_notes
- requested_output

## Allowed Requested Outputs

- intake_summary
- evidence_checklist
- missing_evidence_report
- source_verification_status
- package_readiness

## Blocked Requested Outputs

- recommendation
- ranking
- allocation
- buy_signal
- sell_signal
- investor_decision
- portfolio_weight
- rebalancing_instruction
- trade_signal
- execution_instruction
- strategy_validation
- auto_promotion

## Source Reference Object

Suggested object name: EvidenceSourceReference

Fields:

- title
- url_or_path
- source_type
- publication_date
- access_date
- reliability_label
- notes

Allowed source_type examples:

- annual_report
- quarterly_report
- sec_filing
- exchange_filing
- company_website
- official_database
- market_data_snapshot
- other

Allowed reliability_label values:

- official
- trusted_secondary
- unverified
- unknown

## Initial Completeness Labels

The intake schema should support these non-investment completeness labels:

- incomplete
- minimum_identity_complete
- ready_for_evidence_checklist

These labels do not imply investability or attractiveness.

## Validation Rules

The intake should be considered incomplete if:

1. company_name is missing.
2. Both ticker and official identity evidence are missing.
3. exchange is missing while ticker is provided.
4. as_of_date is missing.
5. requested_output includes blocked investment outputs.

The intake may proceed to evidence checklist if:

1. Company identity is clear.
2. Ticker or official identity evidence is available.
3. As-of date is provided.
4. Requested outputs are preparation-only.
5. No blocked investment output is requested.

## Example Minimal Intake

company_name: Microsoft Corporation
ticker: MSFT
exchange: NASDAQ
listing_country: United States
as_of_date: 2026-06-24
requested_output: intake_summary, evidence_checklist, missing_evidence_report

## Acceptance Criteria

This schema is acceptable if it:

1. Defines minimum identity fields.
2. Defines source reference fields.
3. Supports as-of date context.
4. Supports preparation-only requested outputs.
5. Flags blocked investment outputs.
6. Uses non-investment completeness labels.
7. Does not imply recommendations, rankings, allocations, or trade signals.
8. Aligns with docs/intake_to_package_mvp_plan.md.
9. Aligns with docs/safe_operations_guide.md.
10. Aligns with docs/cli_command_map.json.

## Future Implementation Notes

Future code implementation should begin with pure validation functions before any CLI is added.

Suggested future modules, if implementation is approved later:

- src/broker_agents/intake_to_package/intake_schema.py
- tests/test_intake_to_package_intake_schema.py

No implementation is approved by this documentation alone.

## Safety Boundary

This schema does not allow investment action, investor-agent execution, actual persona review, ranking, recommendation, portfolio construction, allocation, rebalancing, trade signal, execution instruction, or strategy validation.

It only defines safe intake fields for evidence preparation.
