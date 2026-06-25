# Task 145-1C - JSON Intake CLI Smoke Test

## Status

Completed after repair.

## Purpose

Task 145-1C performed a real CLI smoke test using an actual single-company JSON intake file.

The smoke test confirmed that the Intake-to-Package CLI can process JSON input through --input-file and generate preparation-only artifacts.

## Initial Smoke Test Result

The first smoke test failed because the JSON file created through PowerShell contained a UTF-8 BOM.

The CLI originally read the file using utf-8 and raised:

- JSONDecodeError: Unexpected UTF-8 BOM

## Repair

Task 145-1C-R1 repaired JSON file loading by reading input JSON files with:

- utf-8-sig

Repair commit:

- 55d9bba - Handle UTF-8 BOM in JSON intake files

## Re-run Smoke Test

Task 145-1C-R2 re-ran the JSON intake smoke test after the BOM repair.

Run ID:

- smoke_json_intake_145_1

Input file used during smoke test:

- data/intakes/msft_smoke_intake.json

The input file was removed after the smoke test.

## JSON Payload

The smoke test used:

- company_name: Microsoft Corporation
- ticker: MSFT
- exchange: NASDAQ
- listing_country: United States
- as_of_date: 2026-06-24
- requested_output: package_readiness

## Generated Artifacts

The smoke test generated:

- data/outputs/intake_to_package/smoke_json_intake_145_1/package_readiness_report.md
- data/outputs/intake_to_package/smoke_json_intake_145_1/package_readiness_report.json
- data/outputs/intake_to_package/latest_package_readiness_manifest.json

## Output Verification

Confirmed report values:

- report.company_name: Microsoft Corporation
- report.ticker: MSFT
- report.readiness_label: not_ready
- report.human_review_required: True
- report.allowed_next_step: fix_intake_or_collect_missing_evidence

Confirmed manifest values:

- manifest.run_id: smoke_json_intake_145_1
- manifest.readiness_label: not_ready
- manifest.human_review_required: True

## Readiness Interpretation

The not_ready result is expected.

The sample JSON intake did not include official financial statement evidence or operating revenue evidence.

The CLI correctly avoided overstating readiness.

## Safety Boundary Verification

The generated markdown preserved the preparation-only safety boundary.

Confirmed blocked terms:

- No investor-agent execution
- recommendation
- trade signal
- auto-promotion

## Verification

After the successful smoke test:

- python -m ruff check . passed.
- python -m pytest --basetemp=.pytest_tmp_current passed.
- Test count: 949 passed.
- git status was clean.

## Safety Boundaries Preserved

This task did not allow:

- actual persona reviews
- investor-agent execution
- investor decisions
- company recommendations
- company rankings
- allocations
- portfolio weights
- rebalancing
- trade signals
- execution instructions
- strategy validation
- auto-promotion

## Current Capability

Single JSON Intake File Support is now operational and smoke-tested.

The CLI can process a JSON intake file saved with or without UTF-8 BOM.

## Recommended Next Task

Task 145-2A should start Universe or Batch Intake Support.

This next step should allow one file to represent many companies, such as an S&P 500 universe, Saudi listed companies, sector lists, or custom watchlists.
