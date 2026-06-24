# Task 144-21 - Post-CLI Safety Verification and Smoke Test

## Status

Completed.

## Purpose

Task 144-21 performed a post-CLI safety verification and smoke test for the narrow Intake-to-Package CLI command.

The test confirmed that the new CLI can generate preparation-only artifacts without running investor agents or producing investment outputs.

## CLI Command Tested

Command:

- intake-to-package

## Smoke Test Run

Run ID:

- smoke_cli_run_144_21

Output root:

- data/outputs/intake_to_package

## Sample Payload

The smoke test used a safe sample identity-only payload:

- company_name: Microsoft Corporation
- ticker: MSFT
- exchange: NASDAQ
- listing_country: United States
- as_of_date: 2026-06-24

## Generated Artifacts

The CLI generated:

- data/outputs/intake_to_package/smoke_cli_run_144_21/package_readiness_report.md
- data/outputs/intake_to_package/smoke_cli_run_144_21/package_readiness_report.json
- data/outputs/intake_to_package/latest_package_readiness_manifest.json

## Artifact Checks

Confirmed:

- markdown report exists
- JSON report exists
- latest manifest exists

## JSON Verification

Report values:

- report.company_name: Microsoft Corporation
- report.ticker: MSFT
- report.readiness_label: not_ready
- report.human_review_required: True
- report.allowed_next_step: fix_intake_or_collect_missing_evidence

Manifest values:

- manifest.run_id: smoke_cli_run_144_21
- manifest.readiness_label: not_ready
- manifest.human_review_required: True

## Readiness Interpretation

The smoke test result was not_ready because the sample payload intentionally did not include official filings or financial statement evidence.

This is expected and confirms that the CLI does not overstate readiness.

## Safety Text Verification

The generated markdown report preserved the preparation-only safety boundary.

Confirmed safety terms:

- No investor-agent execution
- recommendation
- trade signal
- auto-promotion

## Verification

After the smoke test:

- python -m ruff check . passed.
- python -m pytest --basetemp=.pytest_tmp_current passed.
- Test count: 945 passed.
- git status was clean.

## Safety Boundaries Preserved

This task did not allow:

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

## Current MVP Capability

The Intake-to-Package MVP can now be used through a narrow CLI command to generate preparation-only artifacts and manifests.

## Recommended Next Task

Task 144-22A should define a small user-facing command guide for the Intake-to-Package CLI.

The guide should explain:

- required inputs
- optional inputs
- example command
- generated artifacts
- readiness labels
- safety boundary
- what the CLI does not do
