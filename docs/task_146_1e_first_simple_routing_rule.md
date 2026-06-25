# Task 146-1E - First Simple Routing Rule

## Status

Completed.

## Purpose

This document defines the first simple routing rule for the Company Selection Agent MVP.

The rule selects one company candidate from a manual candidate list and emits one Candidate Selection Record.

The rule is for routing only.

It is not an investment ranking rule.

It is not a recommendation rule.

## Routing Rule Name

The first MVP routing rule is:

- manual_priority_then_list_order

## Core Principle

The rule chooses which company should be prepared next by the Single-Company Pipeline.

It does not choose which company is better as an investment.

It does not produce a buy or sell recommendation.

It only determines routing order for preparation.

## Inputs

The rule receives one Manual Candidate List.

The list may contain multiple company candidates.

Each candidate may include:

- company_name
- ticker
- exchange
- listing_country
- user_priority
- initial_selection_signals
- initial_eligibility_assumptions

## Output

The rule emits one Candidate Selection Record.

The emitted record must represent one company only.

The emitted record must include one pipeline_ready_intake_payload.

## Routing Priority Order

The rule should route candidates in this order:

1. candidates with user_priority = high
2. candidates with user_priority = medium
3. candidates with user_priority = low
4. candidates without user_priority

If multiple candidates have the same priority, the rule uses list order.

List order means the candidate that appears earlier in the manual candidate list is selected first.

## Required Candidate Eligibility for Routing

A candidate can be routed only if it has the required identity fields:

- company_name
- ticker
- exchange
- listing_country

If a candidate is missing required identity fields, it should be skipped or flagged for correction.

## Eligibility Assumptions

The rule may read initial_eligibility_assumptions.

However, these are only preliminary discovery assumptions.

They do not replace Pipeline evidence validation.

The Pipeline still performs its own preparation and evidence readiness checks.

## Selection Reason

The generated Candidate Selection Record should include a routing reason.

Allowed example:

- Selected for Pipeline preparation by manual_priority_then_list_order because it had high routing priority and complete identity fields.

Disallowed examples:

- Selected because it is the best investment.
- Selected because it is a buy.
- Selected because it has the highest upside.

## Selection Signals

The generated Candidate Selection Record may include non-decisional routing signals.

Allowed examples:

- manual_priority_high
- complete_identity_fields
- user_watchlist_match
- manual_test_candidate
- financials_expected_available

These are routing signals only.

They are not buy signals.

They are not investment rankings.

## Tie Handling

If two or more candidates have the same user_priority, list order decides.

This makes the MVP deterministic and easy to test.

No valuation, momentum, quality score, investor preference, or portfolio condition should be used for tie-breaking in the MVP.

## Skipped Candidate Handling

If a candidate is skipped because required identity fields are missing, the MVP may record a simple skip reason.

Examples:

- missing_company_name
- missing_ticker
- missing_exchange
- missing_listing_country

Skip reasons are operational diagnostics only.

They are not investment judgments.

## Correct MVP Behavior

Example candidate list:

1. MSFT with user_priority = high
2. AAPL with user_priority = medium
3. NVDA with user_priority = high

Correct result:

- MSFT is selected first because it has high priority and appears before NVDA.

This does not mean MSFT is better than NVDA.

It only means MSFT is routed first for Pipeline preparation.

## Incorrect MVP Behavior

The routing rule must not:

- compare investment attractiveness
- rank candidates by expected return
- rank candidates by valuation
- rank candidates by momentum
- rank candidates by investor preference
- recommend which company to buy
- produce a final decision
- call investor agents
- call the Aggregator or Decision Agent

## Relationship to Single-Company Pipeline

After one candidate is selected, the Company Selection Agent emits one Candidate Selection Record.

The Single-Company Pipeline receives only the pipeline_ready_intake_payload from that one record.

The Pipeline still processes one company per run.

## Future Routing Rule Expansion

Future routing rules may be added later.

Examples:

- oldest_unprocessed_first
- user_watchlist_first
- sector_focus_first
- source_universe_first
- manual_queue_order

These should remain routing rules unless explicitly moved into a separate decision agent with its own governance.

## Safety Boundary

The first routing rule is discovery and routing only.

It must not introduce:

- investor-agent execution
- persona review
- investor decisions
- company recommendations
- investment rankings
- allocations
- portfolio weights
- rebalancing instructions
- buy signals
- sell signals
- trade signals
- execution instructions
- strategy validation
- auto-promotion

## Recommended Next Task

Task 146-1F should close the Company Selection Agent design subphase.

After that, the next implementation task may create the first minimal schema and validation code for the manual candidate list and Candidate Selection Record.
