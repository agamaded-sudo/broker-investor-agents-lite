# Task 144-2 - CLI Command Inventory

## Status

Initial CLI command inventory documented.

## Purpose

This document records the current CLI surface before any cleanup, renaming, hiding, or workflow simplification.

The goal is to reduce operational confusion and prevent accidental execution of commands that may cross current safety boundaries.

## Source

CLI source inspected:

- `src/broker_agents/cli.py`

Inspection method:

- Python AST inspection of `@app.command` decorators.
- No CLI command was executed.
- No source file was modified during inspection.

## Inventory Summary

Total CLI commands found:

- 90

## Current Safety Context

Current project state:

- Phase 19 closed with warnings.
- Project moved into simplified operational workflow direction.
- Heavy governance expansion is paused.
- Actual persona reviews remain blocked.
- Investor-agent execution remains blocked.
- Recommendations, rankings, allocations, rebalancing, trade signals, execution instructions, strategy validation, and auto-promotion remain blocked.

## Category 1 - Safe / Status / Documentation-Oriented

These commands appear closest to status, audit, validation, or reporting. They may still need review before use, but they are the safest starting point for a command map.

- validate-pack
- validate-historical-snapshot
- validate-financials-csv
- validate-financials-as-of
- validate-price-window
- validate-historical-signal-candidate
- show-historical-readiness-ledger
- validate-readiness-trial-ledger
- validate-expanded-ticker-coverage
- validate-expanded-ticker-coverage-output
- analyze-expanded-trial-results
- build-research-evidence-scorecard
- build-research-audit-trail-bundle
- review-reports
- compare-summaries
- compare-many
- audit-candidates
- missing-evidence
- verify-sources
- readiness-dashboard

## Category 2 - Governance-Only Commands

These commands appear to belong to governance, gatekeeping, closure, packaging, review, stabilization, or permission-boundary layers.

They should remain non-actionable and should not be treated as investment workflows.

- human-review-queue
- run-research-gatekeeper
- build-re-run-re-gate-plan
- build-re-run-input-package
- execute-controlled-re-run-trial
- compare-pre-post-repair-evidence
- run-gatekeeper-re-evaluation
- close-phase-16
- define-targeted-evidence-stabilization-plan
- build-residual-blocker-work-orders
- execute-targeted-evidence-repairs
- run-stabilization-validation-trial
- compare-gatekeeper-stabilized-evidence
- run-gatekeeper-stabilization-re-review
- close-phase-17
- define-gatekeeper-return-package-plan
- build-gatekeeper-return-input-inventory
- assemble-gatekeeper-return-package
- validate-gatekeeper-return-package
- run-gatekeeper-return-review
- close-phase-18
- define-limited-preparation-governance-plan
- build-limited-preparation-artifact-inventory
- assemble-limited-preparation-package
- validate-limited-preparation-package
- review-limited-preparation-package-gatekeeper
- run-evidence-decision-gate

## Category 3 - Research / Data Preparation / Evidence Commands

These commands appear related to enrichment, fixtures, historical data, data preparation, evidence packs, backoffice packages, or research-only analysis.

They should be treated as research/data-preparation commands, not as investor decisions.

- enrich-pack
- enrich-known-ticker
- enrich-known-tickers
- merge-sec-fixture
- merge-market-fixture
- merge-historical-valuation-fixture
- merge-growth-peg-fixture
- build-backoffice-report
- run-pipeline
- run-enriched-pipeline
- run-enriched-pipelines
- compare-manual-enriched
- post-enrichment-gaps
- deal-intake
- deal-intakes
- run-deal
- analyze-stock
- export-readiness-trial-ledger
- run-historical-readiness-multidate
- run-expanded-ticker-readiness-trial
- build-investor-persona-attribution
- build-backoffice-evidence-quality-attribution
- build-backtest-driver-decomposition
- build-outlier-repair-path
- build-walk-forward-repair-plan
- build-delayed-anchor-repair
- build-metadata-diversity-recheck
- build-persona-evidence-pack-requirements
- build-bogle-benchmark-index-pack
- build-fisher-qualitative-growth-pack
- build-buffett-munger-quality-risk-pack
- run-historical-readiness-batch
- compare-clean-coverage-runs
- generate-readiness-trial-decision-report
- generate-readiness-trial-diagnostic-report
- validate-price-csv
- analyze-batch
- run-deals

## Category 4 - Blocked / High-Risk Until Explicit Approval

These commands have names that suggest actual investor-agent execution, portfolio readiness, agent runs, signal backtesting, or candidate decision workflows.

They should not be used under the current safety boundaries unless a future explicit approval path is created.

- run-agent
- run-all-agents
- summarize-agents
- portfolio-readiness
- backtest-signals

## Needs Further Review

The following commands need closer inspection before final classification because their names may be ambiguous or their outputs may overlap with blocked scopes:

- run-deal
- run-deals
- analyze-stock
- analyze-batch
- generate-readiness-trial-decision-report
- run-evidence-decision-gate
- readiness-dashboard
- audit-candidates
- compare-many

## Recommended Next Task

Task 144-2C should create a machine-readable CLI command map.

Suggested output:

- `docs/cli_command_map.json`

Suggested fields:

- command
- function
- line
- category
- allowed_now
- requires_review
- safety_note

## Safety Boundaries Preserved

This document does not allow:

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

## Implementation Boundary

This task is documentation-only. It does not modify CLI behavior, hide commands, rename commands, add commands, remove commands, or execute any CLI command.
