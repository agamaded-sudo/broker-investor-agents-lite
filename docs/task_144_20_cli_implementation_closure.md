# Task 144-20 - Intake-to-Package CLI Implementation Closure

## Status

Completed.

## Purpose

Task 144-20 implemented the narrow Intake-to-Package CLI command approved by the CLI Safety Contract.

The command is limited to preparation-only package readiness artifact generation.

## CLI Command Added

Added command:

- intake-to-package

## Files Changed

Updated:

- src/broker_agents/cli.py

Created in the first commit:

- tests/test_intake_to_package_cli.py

## Implementation Notes

The first implementation attempt committed the CLI tests before the CLI command was successfully inserted.

That caused the new CLI tests to fail because the command did not exist yet.

A follow-up repair commit added the missing CLI implementation to src/broker_agents/cli.py.

## Commits

- 4f3407d - Add intake to package CLI command
- 5f3fec0 - Fix intake to package CLI implementation

## CLI Behavior

The CLI command can:

- accept company identity inputs
- accept listing and as-of-date inputs
- accept optional sector, industry, and fiscal period
- accept requested_output values
- accept output_root
- accept run_id
- call write_package_readiness_artifacts
- write markdown artifact
- write JSON artifact
- update latest manifest
- print run_id and artifact paths
- print readiness_label
- print human_review_required
- print allowed_next_step
- print explicit preparation-only safety boundary

## Safety Boundary

The CLI output includes this safety boundary:

Preparation-only output. No investor-agent execution, persona review, recommendation, ranking, allocation, rebalancing, trade signal, execution instruction, strategy validation, or auto-promotion.

## Tests Added

Added tests confirming:

- the CLI writes markdown artifacts
- the CLI writes JSON artifacts
- the CLI updates latest manifest
- the CLI preserves the safety boundary
- the CLI keeps human_review_required true
- blocked investment requested outputs remain blocked
- the CLI output remains preparation-only

## Verification

Latest verification after repair commit:

- python -m ruff check . passed.
- python -m pytest --basetemp=.pytest_tmp_current passed.
- Test count: 945 passed.
- git status clean after commit.

## Safety Boundaries Preserved

This task does not allow:

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

The Intake-to-Package MVP can now be used through a narrow CLI command to generate preparation-only artifacts.

## Recommended Next Task

Task 144-21A should perform a post-CLI safety verification and command smoke test.

The smoke test should run the new CLI command once with a safe sample payload and verify generated artifacts.

The smoke test must remain preparation-only and must not run investor agents.
