# Task 145-1 - Single JSON Intake File Support Closure

## Status

Completed.

## Purpose

Task 145-1 implemented Single JSON Intake File Support for the Intake-to-Package CLI.

The command can now accept a JSON intake payload for one company through --input-file.

## CLI Command Updated

Updated command:

- intake-to-package

## New CLI Option

Added:

- --input-file

Purpose:

- load a JSON intake payload for one company

## Supported Usage

The CLI now supports two safe input modes:

1. manual CLI options
2. JSON input file

Example JSON input command:

python -m broker_agents.cli intake-to-package --input-file data/intakes/msft.json --run-id msft_json_run

## Implementation Summary

Updated:

- src/broker_agents/cli.py

The implementation:

- loads JSON from --input-file
- requires the JSON payload to be a single object
- merges JSON payload values with explicit CLI options
- allows explicit CLI options to override JSON values
- preserves requested_output handling
- preserves company_name requirement
- preserves as_of_date requirement
- passes the final payload to write_package_readiness_artifacts

## Tests Updated

Updated:

- tests/test_intake_to_package_cli.py

Added tests confirming:

- JSON input file is accepted
- markdown artifact is generated from JSON input
- JSON artifact is generated from JSON input
- investment-output requests inside JSON remain blocked
- preparation-only safety boundary remains visible in CLI output

## Test Count

Test count increased from:

- 945 passed

to:

- 948 passed

## Commit

- dfbecc2 - Add single JSON intake file support

## Verification

Latest verification before commit:

- python -m ruff check . passed.
- python -m pytest --basetemp=.pytest_tmp_current passed.
- Test count: 948 passed.
- git status clean after commit.

## Safety Boundaries Preserved

This task does not allow:

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

The Intake-to-Package CLI can now prepare package readiness artifacts from a single-company JSON intake file.

This is the first step in the Intake Input Scaling Layer.

## Recommended Next Task

Task 145-1C should perform a real CLI smoke test using an actual JSON intake file.

After that, Task 145-2A can start Universe or Batch Intake File Support.
