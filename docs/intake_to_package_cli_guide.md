# Intake-to-Package CLI Guide

## Purpose

This guide explains how to use the narrow Intake-to-Package CLI command.

The command generates preparation-only package readiness artifacts.

It does not run investor agents.

It does not produce investment recommendations.

## Command Name

- intake-to-package

## Required Inputs

The command requires:

- company-name
- as-of-date

## Strongly Recommended Inputs

For listed companies, provide:

- ticker
- exchange
- listing-country

## Optional Inputs

Optional inputs:

- sector
- industry
- fiscal-period
- requested-output
- output-root
- run-id

## Example Command

Run from the project root:

python -m broker_agents.cli intake-to-package --company-name Microsoft Corporation --ticker MSFT --exchange NASDAQ --listing-country United States --as-of-date 2026-06-24 --run-id sample_intake_run

## Default Output Location

By default, the command writes to:

- data/outputs/intake_to_package

## Generated Artifacts

The command generates:

- package_readiness_report.md
- package_readiness_report.json
- latest_package_readiness_manifest.json

## Readiness Labels

The command can return only preparation-only readiness labels:

- not_ready
- partial
- ready_for_human_review

## Meaning of Ready for Human Review

ready_for_human_review means the package may be reviewed by a human.

It does not mean approved.

It does not mean recommended.

It does not mean investable.

It does not mean executable.

## Human Review Requirement

The command preserves:

- human_review_required: true

## Safety Boundary

The command is preparation-only.

It does not allow:

- investor-agent execution
- persona review
- investor decisions
- recommendations
- rankings
- allocations
- portfolio weights
- rebalancing instructions
- buy signals
- sell signals
- trade signals
- execution instructions
- strategy validation
- auto-promotion

## Expected Not Ready Result

A company may return not_ready when official filings, financial statement evidence, operating revenue evidence, or source metadata are missing.

This is expected behavior.

The CLI should not overstate readiness when evidence is incomplete.

## Safe Usage Pattern

Use the command to prepare an evidence package.

Then review missing evidence and blockers manually.

Only after human review should any separate future workflow be considered.

## Current Scope

Current scope:

- intake validation
- evidence checklist
- package readiness classification
- markdown report generation
- JSON report generation
- latest manifest update

## Out of Scope

Out of scope:

- investor-agent analysis
- investor-style judgment
- buy or sell recommendation
- ranking companies
- assigning allocations
- portfolio construction
- trading
- backtesting
- strategy validation
