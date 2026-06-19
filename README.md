# Broker Investor Agents

Broker Investor Agents is a Python project skeleton for building investor-style analysis agents on top of a broker backoffice data pack.

The project is intentionally scaffold-only at this stage. Configuration, schema, method, report-template, and example files are present so the domain shape is clear, while implementation modules contain docstrings only.

## Purpose

The system is designed around two layers:

- Backoffice layer: collect, normalize, validate, and document source-backed company data.
- Investor agent layer: evaluate the same data through distinct long-term investing lenses.

The initial investor methods are:

- Buffett: durable economics, moat, management, intrinsic value, and margin of safety.
- Munger: business quality, incentives, simplicity, and avoidable errors.
- Fisher: qualitative growth, management depth, research culture, and long runway.
- Lynch: understandable growth, category fit, earnings durability, and valuation discipline.
- Bogle: broad-market discipline, cost awareness, diversification, and benchmark context.

## Project Layout

```text
broker_investor_agents/
  config/       Runtime settings, markets, benchmarks, and data-source policy.
  schemas/      YAML schemas for backoffice packs, agent outputs, and confidence.
  methods/      Investor method scorecards and report requirements.
  data/         Raw, interim, clean, and generated output folders.
  src/          Python package placeholders.
  notebooks/    Pilot notebooks.
  tests/        Placeholder test modules.
  examples/     Manual input examples.
```

## Current Scope

This repository currently provides:

- Project packaging metadata in `pyproject.toml`.
- Environment variable template in `.env.example`.
- Configuration and schema YAML files.
- Investor method definition YAML files.
- Markdown/Jinja report templates.
- Placeholder Python modules with docstrings only.

Advanced fetching, parsing, metrics, storage, reporting, validation, and agent logic will be implemented later.

## Quick Start

```powershell
cd broker_investor_agents
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Run the deterministic MSFT reporting pipeline:

```powershell
broker-agents run-pipeline --input examples/msft_input.yaml --output-dir data/outputs/MSFT
```

Review the generated report set:

```powershell
broker-agents review-reports --reports-dir data/outputs/MSFT --ticker MSFT --output data/outputs/MSFT/msft_reports_quality_review.md
```

## Official Financials Fetcher Skeleton

Live SEC fetching is not implemented yet. The SEC financials fetcher currently
provides deterministic company identity resolution, compact fixture mapping,
and source-log integration without requiring network access.

Fixture-based merging is available for development and testing:

```powershell
broker-agents merge-sec-fixture --input examples/msft_input.yaml --fixture tests/fixtures/sec_company_facts_msft.json --output data/outputs/MSFT/msft_input_with_sec_fixture.yaml
```

The command writes a new merged YAML file and does not overwrite the manual
input. Manual examples remain the default pipeline inputs.

## Market Data Fetcher Skeleton

Live market-data fetching is not implemented yet. The market-data fetcher
supports deterministic fixture mapping and non-destructive valuation snapshot
merges for offline development and tests.

```powershell
broker-agents merge-market-fixture --input examples/msft_input.yaml --fixture tests/fixtures/market_data_msft.json --output data/outputs/MSFT/msft_input_with_market_fixture.yaml
```

Fixture market data is treated as medium-confidence provider data by default.
The command writes a separate merged YAML file, and manual inputs remain the
default pipeline inputs.

## Historical Valuation Fetcher Skeleton

Live historical valuation fetching is not implemented yet. The historical
valuation fetcher supports deterministic fixture mapping and non-destructive
merges for offline development and testing.

```powershell
broker-agents merge-historical-valuation-fixture --input examples/msft_input.yaml --fixture tests/fixtures/historical_valuation_msft.json --output data/outputs/MSFT/msft_input_with_historical_valuation_fixture.yaml
```

Historical valuation fixtures are treated as medium-confidence market data by
default. The command writes a separate merged YAML file, while manual inputs
remain the default pipeline inputs.

## Growth & PEG Fetcher Skeleton

Live growth and PEG fetching is not implemented yet. The fetcher supports
deterministic fixture mapping and non-destructive Backoffice merges for offline
development and testing.

```powershell
broker-agents merge-growth-peg-fixture --input examples/msft_input.yaml --fixture tests/fixtures/growth_peg_msft.json --output data/outputs/MSFT/msft_input_with_growth_peg_fixture.yaml
```

Growth and PEG fixtures are treated as medium-confidence market data by
default. The command writes a separate merged YAML file, while manual inputs
remain the default pipeline inputs.

## Unified Backoffice Enrichment Pipeline

The unified enrichment pipeline applies the available SEC financials, market
data, historical valuation, and growth/PEG fixtures to a manual Backoffice
pack in a deterministic sequence.

```powershell
broker-agents enrich-known-ticker --ticker MSFT --input examples/msft_input.yaml --output data/outputs/MSFT/msft_enriched_input.yaml --fixtures-root tests/fixtures --summary-output data/outputs/MSFT/msft_enrichment_summary.md
```

The workflow is offline-safe and does not replace live fetching. It preserves
the original manual input, writes a separate enriched YAML pack, and can write
a Markdown summary of source-quality changes. Manual packs remain the default
until an enriched output is explicitly selected.

## Running Investor Pipeline on Enriched Packs

Generate enriched packs from the offline fixtures:

```powershell
broker-agents enrich-known-tickers --tickers MSFT,AAPL,NVDA --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures
```

Run the full deterministic investor workflow into each ticker's `enriched`
subdirectory:

```powershell
broker-agents run-enriched-pipelines --tickers MSFT,AAPL,NVDA --outputs-root data/outputs --portfolio-context examples/portfolio_context.yaml
```

Compare manual-pack and enriched-pack evidence, candidates, and final-decision
stability:

```powershell
broker-agents compare-manual-enriched --tickers MSFT,AAPL,NVDA --outputs-root data/outputs --output data/outputs/manual_vs_enriched_comparison.md
```

The comparison documents source-quality and evidence changes only. It does not
rank companies, create consensus, change final decisions, or enable
auto-promotion.

## Post-Enrichment Evidence Gap Report

Run this report after fixture enrichment and the enriched investor pipelines:

```powershell
broker-agents post-enrichment-gaps --tickers MSFT,AAPL,NVDA --outputs-root data/outputs --examples-root examples --output data/outputs/post_enrichment_evidence_gap_report.md
```

It separates evidence improved by enrichment from remaining fetcher,
methodology, user-input, and human-review gaps. The report prepares the project
for a later Human Review Queue, but does not implement that queue or change any
investor decision.

## Human Review Queue

Convert post-enrichment evidence gaps into structured Markdown and JSON review
items:

```powershell
broker-agents human-review-queue --tickers MSFT,AAPL,NVDA --outputs-root data/outputs --examples-root examples --output data/outputs/human_review_queue.md --json-output data/outputs/human_review_queue.json
```

The queue identifies questions that require human judgment and records the
evidence needed before review. It does not change final decisions, enable
promotion, rank companies, or produce allocation or trading instructions. It
prepares the project for later governed review workflows.

## Portfolio Manager Readiness Agent

Generate governance-only portfolio readiness assessments and manual triggers:

```powershell
broker-agents portfolio-readiness --tickers MSFT,AAPL,NVDA --outputs-root data/outputs --examples-root examples --output data/outputs/portfolio_manager_readiness_report.md --json-output data/outputs/portfolio_manager_readiness_report.json
```

This agent consolidates enriched evidence, source verification, investor
candidates, promotion eligibility, the Human Review Queue, and portfolio
context. It does not buy or sell, assign final weights, rebalance, override
investor agents, close review items, or enable auto-promotion. It prepares the
system for later governed portfolio-management tasks by producing a manual
trigger list and portfolio-readiness status.

## Broker Deal Workflow

The broker deal workflow is the core Backoffice plus Investor Agents operating
flow. A ticker and manual company pack are submitted, Backoffice applies the
available offline enrichments and verifies source quality, the five investor
agents review the enriched company independently, and a broker-facing deal
package is produced.

```powershell
broker-agents run-deal --ticker MSFT --input examples/msft_input.yaml --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml
```

Run the same workflow for the four current examples:

```powershell
broker-agents run-deals --tickers MSFT,AAPL,NVDA,COST --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml
```

This workflow is not a recommendation or portfolio action. It does not rank or
combine investor responses, assign weights, or execute trades. Opportunity
Scout, Portfolio Manager, and Integration Layer capabilities remain separate
future modules.

The demo set includes MSFT, AAPL, NVDA, and COST. COST is the non-Big-Tech
retail and membership test case, exercising customer loyalty, recurring
membership economics, inventory turnover, thin margins, store expansion, and
valuation discipline.

### Unified One-Command Run

Run deal intake and the complete existing broker deal workflow for one ticker:

```powershell
python -m broker_agents.cli analyze-stock --ticker COST --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml
```

This command refreshes the deal intake and generates the broker deal package,
investor response letters, source verification matrix, investor follow-up
memos, and Backoffice work orders. It prints the main output paths, evidence
readiness, work-order count, promotion-blocking categories, and completion
status. It does not change investor decisions or create a recommendation,
allocation, or trade instruction.

### Structured Analyze-Stock Intake

The same unified workflow can run from a structured YAML or JSON intake file:

```powershell
python -m broker_agents.cli analyze-stock --intake-file examples/deal_intakes/cost_analyze_stock_intake.yaml
```

The intake file records the ticker, optional company context, operating mode,
paths, investor set, and run label. The command writes a compact
`analyze_stock_intake_snapshot.yaml` into the deal package directory for
traceability. The existing `--ticker` mode remains supported and unchanged.
Providing both `--ticker` and `--intake-file` is rejected to avoid ambiguous
configuration.

### Final Run Output Bundle

Every successful `analyze-stock` execution also creates an archival run folder:

```text
data/outputs/{TICKER}/runs/{RUN_ID}/
```

For example:

```powershell
python -m broker_agents.cli analyze-stock --intake-file examples/deal_intakes/cost_analyze_stock_intake.yaml
```

Each run folder contains `run_summary.md` and `run_manifest.json`. These files
record the input mode, evidence readiness, canonical deal-package paths,
investor and work-order counts, promotion-blocking categories, and safety
boundaries. Canonical outputs under `data/outputs/{TICKER}/deal_package/`
remain unchanged. A `latest_run_manifest.json` copy is maintained under the
ticker's `runs` directory for simple discovery.

## Batch Analyze Many Tickers

Run the existing unified stock analysis for several tickers without combining,
ranking, or comparing their independent investor results:

```powershell
python -m broker_agents.cli analyze-batch --tickers MSFT,AAPL,NVDA,COST --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml
```

Each ticker keeps its normal deal package and receives its own archival run
folder. The batch itself is recorded under:

```text
data/outputs/batch_runs/{BATCH_RUN_ID}/
```

That folder contains `batch_summary.md` and `batch_manifest.json`.
`data/outputs/batch_runs/latest_batch_manifest.json` is refreshed after every
batch. The command records failures per ticker and continues processing the
remaining inputs. It does not rank tickers, create consensus, or produce an
allocation or trade signal.

## Signal Archive / Run Result Ledger

Every completed `analyze-stock` run appends one structured audit record. An
`analyze-batch` run appends one record per completed ticker and includes the
batch run ID and folder. The archive is stored at:

```text
data/outputs/signal_archive/signal_ledger.jsonl
data/outputs/signal_archive/signal_ledger.csv
data/outputs/signal_archive/latest_signal_ledger_snapshot.json
```

Records preserve run paths, evidence readiness, investor final decisions and
interest levels, promotion blockers, and explicit safety flags. This archive
is an audit and research ledger for future evaluation. It is not a
recommendation system, ranking engine, consensus mechanism, allocation
instruction, or trade signal, and it contains no backtesting or forward-return
logic.

## Backtesting Framework Skeleton

Evaluate archived readiness, source-quality, blocker, and investor-interest
fields against deterministic offline price fixtures:

```powershell
python -m broker_agents.cli backtest-signals --ledger data/outputs/signal_archive/signal_ledger.csv --price-fixtures tests/fixtures/price_history --outputs-root data/outputs --lookback-years 5
```

Each run creates `backtest_summary.md`, `backtest_results.csv`, and
`backtest_manifest.json` under `data/outputs/backtests/{BACKTEST_RUN_ID}/`.
Default lookback is 5 years; supported values are 2, 5, and 10 years.
Current price histories are clearly labeled synthetic fixtures for offline
framework testing.

This is a research-only evaluation skeleton. It measures associations in
archived fields and does not produce recommendations, rankings, consensus,
portfolio allocation, rebalancing instructions, or trade signals.

### Backtest Quality Controls

Default dedupe mode is `latest_per_ticker_per_day`. It retains the latest
archived record for each ticker and signal date before calculating fixture
returns:

```powershell
python -m broker_agents.cli backtest-signals --ledger data/outputs/signal_archive/signal_ledger.csv --price-fixtures tests/fixtures/price_history --outputs-root data/outputs --lookback-years 5 --dedupe-mode latest_per_ticker_per_day
```

Other supported modes are `none`, `first_per_ticker_per_day`, and
`latest_per_ticker`. Outputs disclose records before and after dedupe, actual
fixture price-anchor dates, blocker counts, minimum group sizes, and
small-sample warnings. Synthetic fixture data is for framework testing only.
Results remain research-only associations, not recommendations or trade
signals.

### Backtest Metrics Summary

Each backtest also creates `backtest_metrics_summary.json` and
`backtest_metrics_summary.md` in its run folder:

```powershell
python -m broker_agents.cli backtest-signals --ledger data/outputs/signal_archive/signal_ledger.csv --price-fixtures tests/fixtures/price_history --outputs-root data/outputs --lookback-years 5 --dedupe-mode latest_per_ticker_per_day
```

Metrics evaluate archived signal behavior through forward-return,
benchmark-relative, positive-return, and drawdown statistics. Grouped metrics
cover readiness, source verification, promotion blockers, and each investor's
interest level. Synthetic fixture data is not real market data. These metrics
are research-only and produce no recommendation, ranking, or trading signal.

### Data Provider Adapter

The backtester reads prices through a common provider interface:

- `fixture`: deterministic synthetic fixture data for tests.
- `csv`: local user-provided CSV files named `msft.csv`, `aapl.csv`, and so on.
- `live_stub`: a placeholder that performs no network calls and reports that
  live data is not configured.

Fixture provider example:

```powershell
python -m broker_agents.cli backtest-signals --ledger data/outputs/signal_archive/signal_ledger.csv --price-provider fixture --price-fixtures tests/fixtures/price_history --outputs-root data/outputs --lookback-years 5 --dedupe-mode latest_per_ticker_per_day
```

Local CSV provider example:

```powershell
python -m broker_agents.cli backtest-signals --ledger data/outputs/signal_archive/signal_ledger.csv --price-provider csv --price-fixtures tests/fixtures/price_history --outputs-root data/outputs --lookback-years 5 --dedupe-mode latest_per_ticker_per_day
```

The live provider is not implemented yet. No API keys, external dependencies,
or network calls are required. Hosted integration can be added later after a
provider is selected.

### Real Market Data CSV Trial

The first real-data trial path uses user-supplied local CSV files under
`data/inputs/market_prices/`. Adjusted close is preferred when present; the CSV
provider falls back to close. Common headers such as `Date`, `Close`,
`Adj Close`, and `Adjusted Close` are accepted.

Validate a local folder before running a backtest:

```powershell
python -m broker_agents.cli validate-price-csv --price-provider csv --price-fixtures data/inputs/market_prices --tickers MSFT,AAPL,NVDA,COST,SPY
```

Run the research backtest with locally supplied prices:

```powershell
python -m broker_agents.cli backtest-signals --ledger data/outputs/signal_archive/signal_ledger.csv --price-provider csv --price-fixtures data/inputs/market_prices --outputs-root data/outputs --lookback-years 5 --dedupe-mode latest_per_ticker_per_day
```

See [Market Data Provider Selection](docs/market_data_provider_selection.md)
for the future-provider checklist. This task does not add live API calls; CSV
data is supplied by the user. No recommendation, ranking, allocation
instruction, or trade signal is produced.

### Historical CSV Backtest Trial

Historical trial ledgers let locally supplied market-price files exercise full
3-month, 6-month, and 12-month forward windows before live data integration.

Validate the local market-price folder:

```powershell
python -m broker_agents.cli validate-price-csv --price-provider csv --price-fixtures data/inputs/market_prices --tickers MSFT,AAPL,NVDA,COST,SPY
```

Run the included historical trial ledger against user-supplied prices:

```powershell
python -m broker_agents.cli backtest-signals --ledger data/inputs/trial_ledgers/sample_historical_signal_ledger.csv --price-provider csv --price-fixtures data/inputs/market_prices --outputs-root data/outputs --lookback-years 5 --dedupe-mode latest_per_ticker_per_day
```

Real CSV files must cover each signal date and its forward windows. For
example, a signal dated `2021-06-30` needs price observations through at least
`2022-06-30` for a 12-month calculation.

`sample_historical_signal_ledger.csv` contains synthetic, reconstructed inputs
for pipeline validation only. It is not a real historical recommendation set.
No recommendation, ranking, allocation instruction, or trade signal is
produced.

### Walk-Forward Historical Validation

Walk-forward validation groups signal records into yearly cohorts and reports
their 3-month, 6-month, and 12-month outcomes separately:

```powershell
python -m broker_agents.cli backtest-signals --ledger data/inputs/trial_ledgers/sample_historical_signal_ledger.csv --price-provider csv --price-fixtures tests/fixtures/historical_price_history --outputs-root data/outputs --lookback-years 5 --dedupe-mode latest_per_ticker_per_day --walk-forward --walk-forward-frequency yearly
```

When enabled, the backtest run folder also contains
`walk_forward_summary.md`, `walk_forward_results.csv`, and
`walk_forward_metrics.json`.

This mode evaluates signal cohorts year by year to identify period-dependent
behavior. It does not build or simulate a portfolio, define entry or exit
rules, or represent live trading. It produces no recommendation, ranking, or
trade signal.

### As-Of-Date Historical Analysis Readiness

`analyze-stock` accepts an optional historical-readiness date:

```powershell
python -m broker_agents.cli analyze-stock --ticker COST --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml --as-of-date 2023-06-30
```

The date is recorded in the intake snapshot, run manifest, run summary, and
signal archive. A structured example is available at
`examples/deal_intakes/cost_historical_as_of_intake.yaml`.

`as_of_date` records the intended historical analysis date and makes the run's
historical mode explicit. This is readiness only: full point-in-time
enforcement requires future historical snapshots for every input and provider.
Current fixture and manual data may include information dated after the
requested cutoff, so each historical run carries a visible leakage warning.

This mode must not be interpreted as investment advice or a trading strategy.
It produces no recommendation, ranking, allocation instruction, or trade
signal.

### Historical Data Snapshot Contract

An `as_of_date` alone is not enough for true historical testing. Each
historical run now includes a snapshot contract that records which sections
support the intended date, which remain readiness-only, and where future-data
leakage may exist.

```powershell
python -m broker_agents.cli analyze-stock --ticker COST --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml --as-of-date 2023-06-30
```

The run manifest stores `historical_snapshot_contract`, including provider
capabilities, supported and unsupported sections, leakage-risk sections, and
warnings. Current enforcement remains `readiness_only`; full point-in-time
safety requires future historical snapshots for financials, valuations,
estimates, qualitative evidence, index holdings, and other inputs.

Validate the declared capability contract without running investor agents:

```powershell
python -m broker_agents.cli validate-historical-snapshot --as-of-date 2023-06-30 --price-provider csv --price-fixtures tests/fixtures/historical_price_history
```

This contract identifies readiness and leakage risk. It does not generate
historical signals and does not produce recommendations, rankings, allocation
instructions, or trade signals.

### Historical Price Window Enforcement

Historical analysis price inputs must not use observations after `as_of_date`.
The CSV provider can enforce this cutoff and reports the rows present before
and after filtering, including the number of future observations excluded.
Backtest outcome calculations remain separate: they may use future prices only
to measure 3-month, 6-month, and 12-month results.

```powershell
python -m broker_agents.cli analyze-stock --ticker COST --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml --as-of-date 2023-06-30
python -m broker_agents.cli validate-historical-snapshot --as-of-date 2023-06-30 --price-provider csv --price-fixtures tests/fixtures/historical_price_history
python -m broker_agents.cli validate-price-window --ticker COST --price-provider csv --price-fixtures tests/fixtures/historical_price_history --as-of-date 2023-06-30
```

This cutoff prevents future-price leakage in historical analysis contexts. It
does not yet guarantee full point-in-time safety for financial statements,
manual inputs, valuations, or qualitative evidence. No live data API is used.
This historical price window enforcement is not a recommendation, ranking,
vote, average score, consensus, allocation instruction, rebalancing
instruction, or trade signal.

### Official Financials As-Of Contract

Historical price windows can be filtered directly because price files are
date-indexed. Official financial statements require a stricter availability
contract: a fiscal period end date alone does not establish when the filing was
available. Point-in-time analysis also needs a `filing_date` or
`accepted_date`, plus statement and period metadata.

Current SEC and manual financial fixtures are readiness-only. They may contain
facts filed after the requested `as_of_date`, so historical runs list available
and missing date fields and retain a high leakage-risk warning.

```powershell
python -m broker_agents.cli analyze-stock --ticker COST --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml --as-of-date 2023-06-30
python -m broker_agents.cli validate-financials-as-of --as-of-date 2023-06-30 --fixtures-root tests/fixtures
```

A future provider may use point-in-time SEC filing snapshots or user-supplied
`financials_as_of` datasets. This task adds no live data or SEC requests and
does not guarantee full historical correctness. It identifies missing date
fields and leakage risk only. This official financials as-of contract is not a
recommendation, ranking, vote, average score, consensus, allocation
instruction, rebalancing instruction, or trade signal.

### Historical Financials CSV Input

User-supplied point-in-time financial statement snapshots use the folder
convention `data/inputs/historical_financials/` and filenames such as
`cost_financials_as_of.csv`. The required columns are `ticker`,
`fiscal_period_end_date`, `filing_date`, `accepted_date`, `statement_type`,
`period_type`, `metric`, `value`, and `source_url_or_accession_number`.
Optional metadata includes currency, units, filing form, fiscal year/quarter,
data-as-of date, ingestion date, and source name.

Period end date alone is not enough. For an analysis cutoff, a row is allowed
only when `filing_date <= as_of_date` or `accepted_date <= as_of_date`. Rows
with neither availability date are excluded as not point-in-time safe.

Validate local files without running investor analysis:

```powershell
python -m broker_agents.cli validate-financials-csv --financials-root tests/fixtures/historical_financials --tickers MSFT,AAPL,NVDA,COST --as-of-date 2023-06-30
```

Validate the aggregate snapshot capability with the local provider:

```powershell
python -m broker_agents.cli validate-historical-snapshot --as-of-date 2023-06-30 --price-provider csv --price-fixtures tests/fixtures/historical_price_history --financials-provider historical_csv --financials-root tests/fixtures/historical_financials
```

The local CSV provider is partially as-of capable when required availability
fields are present, but provenance remains user-managed. This task performs no
live SEC/API fetching and does not generate historical investor signals. This
historical financials CSV input format is not a recommendation, ranking, vote,
average score, consensus, allocation instruction, rebalancing instruction, or
trade signal.

### Historical Financials Provider Wiring

`validate-financials-csv` checks local point-in-time financial statement files.
`analyze-stock` can now attach a filtered official-financials snapshot to a
historical run when `historical_csv` is selected:

```powershell
python -m broker_agents.cli analyze-stock --ticker COST --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml --as-of-date 2023-06-30 --financials-provider historical_csv --financials-root tests/fixtures/historical_financials
```

The run folder contains `official_financials_as_of_snapshot.csv`, optional
snapshot metadata JSON, `run_manifest.json`, and `run_summary.md`. Rows are
included only when `filing_date` or `accepted_date` is on or before
`as_of_date`; rows missing both availability dates are counted and excluded.

This attachment does not alter investor decisions, generate historical
signals, or replace the existing enriched input assembly. It is a readiness
step for future historical analysis. No live API or SEC request is used, and
no recommendation, ranking, allocation instruction, or trade signal is
produced.

### Historical Enriched Input Assembly

Each historical `analyze-stock` run now creates a run-local readiness artifact
that combines the historical snapshot contract, analysis price window, and
official-financials snapshot metadata:

```powershell
python -m broker_agents.cli analyze-stock --ticker COST --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml --as-of-date 2023-06-30 --financials-provider historical_csv --financials-root tests/fixtures/historical_financials
```

Inspect `historical_enriched_input_assembly.json`,
`historical_enriched_input_assembly.md`, `run_manifest.json`, and
`run_summary.md` under `data/outputs/COST/runs/{RUN_ID}/`.

The assembly identifies partial/as-of-capable sections and the valuation,
growth, market snapshot, qualitative, index-overlap, verification, and
investor-output sections that remain readiness-only or leakage-risk.
It does not generate signals. It does not alter investor decisions.
`safe_for_historical_signal_generation` remains `false` until sufficient
point-in-time inputs are available. No live API is used. No recommendation,
ranking, allocation instruction, or trade signal is produced.

### Historical Signal Generation Readiness Trial

Historical `analyze-stock` runs now create a readiness-only research candidate
beside the enriched input assembly:

```powershell
python -m broker_agents.cli analyze-stock --ticker COST --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml --as-of-date 2023-06-30 --financials-provider historical_csv --financials-root tests/fixtures/historical_financials
```

Inspect `historical_enriched_input_assembly.json`,
`historical_signal_readiness_candidate.json`, `run_manifest.json`, and
`run_summary.md` under the generated run folder. Validate an existing
candidate without rerunning analysis:

```powershell
python -m broker_agents.cli validate-historical-signal-candidate --candidate-file data/outputs/COST/runs/{RUN_ID}/historical_signal_readiness_candidate.json
```

The candidate is not full historical signal generation.
It is not written to the main signal ledger.
It is not used for portfolio allocation. It remains
blocked while key inputs are readiness-only. The artifact exists to prepare
future historical research while preserving methodological honesty. It is not
a recommendation, ranking, vote, consensus, allocation instruction,
rebalancing instruction, trade signal, or execution instruction.

### Historical Readiness Candidate Ledger

Historical readiness candidates are exported to a dedicated research ledger,
separate from `data/outputs/signal_archive/signal_ledger.jsonl`:

```powershell
python -m broker_agents.cli analyze-stock --ticker COST --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml --as-of-date 2023-06-30 --financials-provider historical_csv --financials-root tests/fixtures/historical_financials
python -m broker_agents.cli show-historical-readiness-ledger --outputs-root data/outputs
```

Inspect:

* `data/outputs/historical_readiness_ledger/historical_signal_readiness_ledger.jsonl`
* `data/outputs/historical_readiness_ledger/historical_signal_readiness_ledger.csv`
* `data/outputs/historical_readiness_ledger/latest_historical_signal_readiness_ledger_snapshot.json`
* the latest historical run's `run_manifest.json`

Every record is explicitly `readiness_only`, with
`safe_for_historical_signal_generation=false`, `not_trade_signal=true`, and
`not_recommendation=true`. This separate ledger supports research traceability
before any future trial-backtest integration.
It must not be confused with the main signal ledger.
No live API is used, and no recommendation, ranking,
allocation instruction, rebalancing instruction, trade signal, or execution
instruction is produced.

### Readiness Ledger to Trial Backtest Input Export

The separate historical readiness ledger can be converted into a
research-only trial input file without changing the main signal ledger:

```powershell
python -m broker_agents.cli export-readiness-trial-ledger --outputs-root data/outputs --output-ledger data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv
python -m broker_agents.cli validate-readiness-trial-ledger --ledger data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv
```

The export maps `signal_date` from `as_of_date` and preserves
`readiness_only`, `safe_for_historical_signal_generation=false`,
`not_trade_signal=true`, `not_recommendation=true`, and
`not_allocation_instruction=true`. It also includes the timestamp and run
identifiers required by the existing research backtester.

This task prepares `historical_readiness_trial_ledger.csv` and its metadata
JSON only; it does not run a backtest. The file may be used later to study
outcomes after readiness events. It remains separate from the main signal
ledger and produces no recommendation, ranking, allocation instruction,
rebalancing instruction, trade signal, or execution instruction.

### Readiness Trial Backtest

The existing research backtester detects exported readiness-only ledgers and
labels the run as `readiness_trial`:

```powershell
python -m broker_agents.cli backtest-signals --ledger data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv --price-provider csv --price-fixtures tests/fixtures/historical_price_history --outputs-root data/outputs --lookback-years 5 --dedupe-mode latest_per_ticker_per_day
```

This studies outcomes after readiness events.
It is not a trading strategy backtest.
It is not a recommendation backtest or proof of investment performance.
Readiness safety fields are preserved in `backtest_results.csv`; invalid rows
are skipped with warnings. Deduplication should remain enabled to prevent
repeated run artifacts from inflating the sample. When only one ticker is
present, concentration and small-sample warnings are expected.

Results are research diagnostics only and must not be interpreted as
recommendations, rankings, allocation instructions, rebalancing instructions,
trade signals, or execution instructions.

### Readiness Trial Backtest Decision Report

Readiness trial backtests automatically create
`readiness_trial_decision_report.md` and
`readiness_trial_decision_report.json` beside the existing backtest artifacts:

```powershell
python -m broker_agents.cli backtest-signals --ledger data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv --price-provider csv --price-fixtures tests/fixtures/historical_price_history --outputs-root data/outputs --lookback-years 5 --dedupe-mode latest_per_ticker_per_day
```

Raw return metrics can be misleading when the evaluated sample is tiny. The
decision report interprets readiness results conservatively by diagnosing
sample size, dedupe impact, ticker concentration, and missing grouped metadata.
It states whether the run is decision-grade; current small samples are
expected to remain diagnostic only.

An existing readiness trial folder can be regenerated without rerunning price
calculations:

```powershell
python -m broker_agents.cli generate-readiness-trial-decision-report --backtest-folder data/outputs/backtests/{RUN_ID}
```

The report is about research data readiness, not strategy performance. It
produces no recommendation, ranking, allocation instruction, rebalancing
instruction, trade signal, execution instruction, or investment advice.

### Multi-Ticker Historical Readiness Batch

Generate readiness-only historical candidates for several tickers at one
as-of date:

```powershell
python -m broker_agents.cli run-historical-readiness-batch --tickers MSFT,AAPL,NVDA,COST --as-of-date 2023-06-30 --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml --financials-provider historical_csv --financials-root tests/fixtures/historical_financials
```

The command uses the existing historical `analyze-stock` pipeline for each
ticker, continues after individual failures, archives each readiness candidate,
and writes a manifest, summary, and results CSV under
`data/outputs/historical_readiness_batch_runs/{BATCH_RUN_ID}/`.

The optional full research pipeline exports and validates the readiness trial
ledger, then runs the existing readiness-only backtest and decision report:

```powershell
python -m broker_agents.cli run-historical-readiness-batch --tickers MSFT,AAPL,NVDA,COST --as-of-date 2023-06-30 --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml --financials-provider historical_csv --financials-root tests/fixtures/historical_financials --export-trial-ledger --validate-trial-ledger --run-readiness-backtest
```

This expands the research sample before interpretation. Dedupe remains important
because repeated historical runs can inflate raw record counts. The batch
creates no recommendation, ranking, allocation instruction, rebalancing
instruction, trade signal, or execution instruction.

### Multi-Date Historical Readiness Trial

Run the existing multi-ticker readiness batch across several as-of dates, then
optionally export, validate, and backtest the aggregate readiness sample:

```powershell
python -m broker_agents.cli run-historical-readiness-multidate --tickers MSFT,AAPL,NVDA,COST --as-of-dates 2021-06-30,2022-06-30,2023-06-30 --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml --financials-provider historical_csv --financials-root tests/fixtures/historical_financials --export-trial-ledger --validate-trial-ledger --run-readiness-backtest
```

This research-only workflow attempts every ticker for every date and continues
after isolated ticker or date failures. Four tickers across three dates target
approximately 12 readiness events before repeated-run dedupe. The multi-date
manifest, summary, and results CSV are written under
`data/outputs/historical_readiness_multidate_runs/{MULTIDATE_RUN_ID}/`.

The goal is sample expansion before interpretation, not strategy validation.
Dedupe remains important because repeated runs may inflate raw records.
Results remain diagnostic until sample size and data quality are sufficient;
missing metadata and readiness-only sections remain visible. No recommendation,
ranking, allocation instruction, rebalancing instruction, trade signal, or
execution instruction is produced.

### Expanded Historical Date Coverage

Historical readiness multi-date runs support reusable local-data presets:

- `annual_3`: the conservative 2021, 2022, and 2023 annual baseline.
- `semiannual_6`: the first expanded research preset with six requested dates.
- `quarterly_9`: an experimental preset that may require additional fixture
  coverage.

Run the semiannual preset with:

```powershell
python -m broker_agents.cli run-historical-readiness-multidate --tickers MSFT,AAPL,NVDA,COST --date-preset semiannual_6 --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml --financials-provider historical_csv --financials-root tests/fixtures/historical_financials --export-trial-ledger --validate-trial-ledger
```

The command validates local price and historical financial CSV coverage before
running a preset. It writes `historical_date_coverage_report.json` and
`historical_date_coverage_report.md` in the multi-date run folder. Dates without
the required local price anchors are listed as skipped and are not fabricated.
The run fails only when a preset has no usable dates. Explicit
`--as-of-dates` values take precedence when both explicit dates and
`--date-preset` are supplied, preserving the existing explicit-date workflow.

After export, the existing readiness walk-forward backtest remains available:

```powershell
python -m broker_agents.cli backtest-signals --ledger data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv --price-provider csv --price-fixtures tests/fixtures/historical_price_history --outputs-root data/outputs --lookback-years 5 --dedupe-mode latest_per_ticker_per_day --walk-forward --walk-forward-frequency yearly
```

All coverage checks use local fixtures only. Expanded results remain
readiness-only and diagnostic; no recommendation, ranking, allocation
instruction, rebalancing instruction, trade signal, or execution instruction
is produced.

### Expanded Date Coverage Quality Guardrails

Expanded historical dates may be usable without being equally clean. Coverage
validation now classifies each date and ticker-date record as `clean`,
`usable_with_warnings`, `delayed_price_anchor`, `limited_financials`,
`delayed_anchor_and_limited_financials`, or `unsupported`. Severity and stable
guardrail status fields distinguish clean evidence from delayed price anchors,
limited filing availability, and warning-heavy combinations.

```powershell
python -m broker_agents.cli run-historical-readiness-multidate --tickers MSFT,AAPL,NVDA,COST --date-preset semiannual_6 --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml --financials-provider historical_csv --financials-root tests/fixtures/historical_financials --export-trial-ledger --validate-trial-ledger

python -m broker_agents.cli backtest-signals --ledger data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv --price-provider csv --price-fixtures tests/fixtures/historical_price_history --outputs-root data/outputs --lookback-years 5 --dedupe-mode latest_per_ticker_per_day --walk-forward --walk-forward-frequency yearly
```

Quality fields flow through the separate historical readiness ledger, trial
ledger, backtest results, grouped metrics, decision report, and diagnostic
report. Unsupported dates are excluded rather than fabricated. Warning records
remain available for research unless explicitly excluded, and delayed anchors
must not be interpreted as clean historical execution simulation.

These guardrails remain readiness-only and diagnostic. They do not produce
recommendations, rankings, allocation instructions, rebalancing instructions,
trade signals, or execution instructions.

### Clean Historical Fixture Coverage

The local historical financial fixtures now include point-in-time rows
available before the June 2021, June 2022, and June 2023 research cutoffs.
Fixture filtering requires both a fiscal period end on or before the cutoff and
at least one filing or accepted date on or before the cutoff. Future-period
facts and rows missing both availability dates are excluded.

For a ticker-date record, `clean` means the local fixture supplies usable
point-in-time financials and the price history supplies non-delayed start and
12-month anchors. Date-level reports may still contain warnings from other
ticker-date records, so clean classification is propagated at record level
rather than inferred from the whole date.

```powershell
python -m broker_agents.cli run-historical-readiness-multidate --tickers MSFT,AAPL,NVDA,COST --date-preset semiannual_6 --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml --financials-provider historical_csv --financials-root tests/fixtures/historical_financials --export-trial-ledger --validate-trial-ledger
```

These are deterministic local test fixtures only. Clean coverage improves data
quality comparison, but it does not produce recommendations, rankings,
allocation instructions, rebalancing instructions, trade signals, or
execution instructions. Clean sample thresholds remain conservative.

### Clean Coverage Before/After Comparison

The clean coverage comparison command audits a pre-clean-fixture readiness
backtest against a post-clean-fixture run. It records whether clean evidence
became available, whether warning-heavy and limited-financials records fell,
whether diagnostic metrics changed, and whether the decision remained
conservative.

Use explicit run IDs for a reproducible comparison:

```powershell
python -m broker_agents.cli compare-clean-coverage-runs --before-run-id 20260614_201147 --after-run-id 20260614_205804 --outputs-root data/outputs
```

Or select the latest matching pre-clean and post-clean runs:

```powershell
python -m broker_agents.cli compare-clean-coverage-runs --auto-latest --outputs-root data/outputs
```

Each comparison writes Markdown, JSON, and CSV artifacts under
`data/outputs/clean_coverage_comparisons/{COMPARE_RUN_ID}/`, plus
`latest_clean_coverage_comparison_manifest.json`. The report preserves clean
subset metrics alongside delayed-anchor and outlier context.

This is a research-only audit. It does not prove a strategy, validate investor
agents, or create recommendations, rankings, allocation instructions,
rebalancing instructions, trade signals, or execution instructions.

### Clean vs Warning Evidence Decision Gate

The evidence decision gate is separate from the readiness trial decision
report. The decision report remains conservative about the current evidence;
the gate only determines whether the research program may proceed to a broader
sample. It requires preliminary clean evidence, keeps warning-bearing records
visible, and treats delayed-anchor, outlier, sample-size, and concentration
issues as explicit cautions or blockers.

Run the gate for an explicit readiness trial:

```powershell
python -m broker_agents.cli run-evidence-decision-gate --backtest-run-id 20260614_205804 --outputs-root data/outputs
```

Or select the latest completed readiness trial with clean-coverage
sensitivity:

```powershell
python -m broker_agents.cli run-evidence-decision-gate --auto-latest --outputs-root data/outputs
```

An outcome of `research_ready_for_broader_trial` permits broader research
testing only. It does not validate performance or create investment
recommendations, rankings, allocations, execution instructions, or trade
signals. The required next action remains broader ticker coverage with
coverage validation and preserved clean/warning segmentation.

Each gate writes Markdown, JSON, and criterion CSV artifacts under
`data/outputs/evidence_decision_gates/{GATE_RUN_ID}/`, plus
`latest_evidence_decision_gate_manifest.json`.

### Expanded Ticker Universe with Coverage Validation

The expanded universe is a research fixture candidate list, not an endorsement
or ranking. Before any broader readiness trial, each ticker/date pair is
checked for point-in-time financial availability, start and forward price
anchors, benchmark outcomes, delayed anchors, and limited-financials
conditions.

```powershell
python -m broker_agents.cli validate-expanded-ticker-coverage --ticker-universe examples/expanded_ticker_universe.yaml --date-preset semiannual_6 --fixtures-root tests/fixtures --financials-root tests/fixtures/historical_financials --price-fixtures tests/fixtures/historical_price_history --outputs-root data/outputs
```

Ticker/date rows are classified as `eligible_clean`,
`eligible_with_warnings`, or `not_eligible`. Tickers require at least two clean
records with no more than half of requested dates excluded to enter the
expanded trial normally. A smaller but still usable cohort may be admitted
with caution; insufficient coverage is excluded.

Validation writes Markdown, JSON, a ticker/date matrix CSV, and
`expanded_ticker_eligible_universe.yaml` under
`data/outputs/expanded_ticker_coverage/{VALIDATION_RUN_ID}/`. The eligible YAML
can be converted to a comma-separated list for the existing multidate command.
All added financial and price rows are deterministic local research fixtures.
Coverage eligibility does not recommend or rank tickers, validate investor
agents, or create allocations, execution instructions, or trade signals.

### Expanded Ticker Coverage Output Validation

Before expanded trial execution, a final handoff validator checks that the
coverage report JSON, ticker-date matrix CSV, eligible-universe YAML, and
latest manifest are present and internally consistent. It verifies ticker
membership, clean and usable record minimums, unsupported-row exclusion,
reported counts, safety language, and the expected next research action.

Validate the latest expanded coverage output:

```powershell
python -m broker_agents.cli validate-expanded-ticker-coverage-output --auto-latest --outputs-root data/outputs
```

Or validate a specific run:

```powershell
python -m broker_agents.cli validate-expanded-ticker-coverage-output --validation-run-id 20260615_070003 --outputs-root data/outputs
```

This command only validates Task 101 artifacts. It does not run an expanded
trial or backtest, rank or recommend tickers, validate investor agents, or
produce allocations, execution instructions, or trade signals.

### Clean-Coverage Sensitivity Report

Readiness trial backtests now compare aggregate outcomes with coverage-quality
subsets including clean records, warning-bearing records, warning-heavy
records, delayed and non-delayed anchors, limited financial coverage, and
non-warning-heavy records.

```powershell
python -m broker_agents.cli backtest-signals --ledger data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv --price-provider csv --price-fixtures tests/fixtures/historical_price_history --outputs-root data/outputs --lookback-years 5 --dedupe-mode latest_per_ticker_per_day --walk-forward --walk-forward-frequency yearly
```

Each readiness trial run writes `clean_coverage_sensitivity_report.md` and
`clean_coverage_sensitivity_report.json`. Warning records are not automatically
discarded. The report instead shows whether aggregate evidence depends on
warning-heavy, delayed-anchor, or limited-financials rows. When no clean records
exist, clean-only sensitivity is explicitly unavailable and no metrics are
fabricated.

This is a research-only diagnostic. It does not prove a strategy or produce a
recommendation, ranking, allocation instruction, rebalancing instruction,
trade signal, or execution instruction.

### Delayed Anchor Impact Report

Readiness trial backtests now create a focused delayed-anchor impact report.
Delayed anchors occur when the nearest usable price observation falls after the
requested as-of or forward date. The report compares delayed-anchor rows with
non-delayed rows to show whether stronger aggregate outcomes depend materially
on delayed timing.

```powershell
python -m broker_agents.cli backtest-signals --ledger data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv --price-provider csv --price-fixtures tests/fixtures/historical_price_history --outputs-root data/outputs --lookback-years 5 --dedupe-mode latest_per_ticker_per_day --walk-forward --walk-forward-frequency yearly
```

Each readiness trial writes `delayed_anchor_impact_report.md` and
`delayed_anchor_impact_report.json`. The report also separates delayed,
non-delayed, delayed-and-warning-heavy, and non-delayed-but-limited-financials
records. Non-delayed records can still carry other warnings, so positive
non-delayed results are not clean-only evidence.

This report complements clean-coverage sensitivity and remains readiness-only.
It does not simulate exact historical execution or produce recommendations,
rankings, allocation instructions, rebalancing instructions, trade signals, or
execution instructions.

### Outlier and Ex-NVDA Sensitivity Report

Readiness trial backtests now compare the complete sample with Ex-NVDA,
NVDA-only, top-1/top-2/top-3 exclusion, capped-return, and non-extreme
subsets. This identifies whether the average is lifted by extreme winners and
whether the median, relative median, and benchmark hit rate remain positive
after conservative exclusions.

```powershell
python -m broker_agents.cli backtest-signals --ledger data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv --price-provider csv --price-fixtures tests/fixtures/historical_price_history --outputs-root data/outputs --lookback-years 5 --dedupe-mode latest_per_ticker_per_day --walk-forward --walk-forward-frequency yearly
```

Each readiness trial writes `outlier_sensitivity_report.md` and
`outlier_sensitivity_report.json`. The capped subset changes only report-local
copies; original backtest results and return calculations remain unchanged.
Ex-NVDA and top-outlier exclusions reduce sample size, so surviving positive
results remain preliminary rather than validated.

This report complements coverage quality, clean-coverage sensitivity, delayed
anchor impact, and metadata attribution. It remains readiness-only and does
not produce recommendations, rankings, allocation instructions, rebalancing
instructions, trade signals, or execution instructions.

### Readiness Trial Walk-Forward Backtest

After multi-date sample generation, run the readiness-only backtest by yearly
cohort:

```powershell
python -m broker_agents.cli backtest-signals --ledger data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv --price-provider csv --price-fixtures tests/fixtures/historical_price_history --outputs-root data/outputs --lookback-years 5 --dedupe-mode latest_per_ticker_per_day --walk-forward --walk-forward-frequency yearly
```

This evaluates readiness-only artifacts by time period and helps diagnose
whether aggregate results are stable or driven by a single year. It creates
yearly walk-forward results, metrics, and a readiness notice, then extends the
decision report with a conservative stability judgment.

The workflow is research-only and does not produce recommendations or trading
instructions. Results remain diagnostic until sample size and data quality are
sufficient. Missing metadata and readiness-only sections remain visible, and
dedupe remains important because repeated runs may inflate raw records.

### Expanded Ticker Readiness Trial

The expanded trial consumes the eligible universe produced by expanded ticker
coverage validation. It runs the existing historical multidate pipeline for
the validated local fixture cohort, preserves unsupported-date exclusions,
exports and validates the readiness ledger, and can run the complete
readiness-only backtest diagnostics with yearly walk-forward analysis.

```powershell
python -m broker_agents.cli run-expanded-ticker-readiness-trial --eligible-universe data/outputs/expanded_ticker_coverage/20260615_070003/expanded_ticker_eligible_universe.yaml --date-preset semiannual_6 --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml --financials-provider historical_csv --financials-root tests/fixtures/historical_financials --price-provider csv --price-fixtures tests/fixtures/historical_price_history --export-trial-ledger --validate-trial-ledger --run-readiness-backtest --walk-forward
```

The summary records source validation provenance, eligible tickers, usable and
skipped dates, completion totals, coverage-quality counts, and links to the
normal decision, diagnostic, clean-coverage, delayed-anchor, outlier, and
walk-forward artifacts. The expanded universe consists only of deterministic
local research fixtures. It is non-actionable and does not create
recommendations, rankings, allocation instructions, rebalancing instructions,
trade signals, or execution instructions.

### Expanded Trial Results Analysis

After an expanded ticker trial completes, the analysis command decomposes the
existing backtest by ticker, sector, category, universe group, historical date,
coverage quality, delayed-anchor status, and benchmark-relative outcome. It
also compares the validated current-core cohort with the added ticker cohort
and rechecks whether readiness and investor-interest metadata have enough
diversity to support attribution.

```powershell
python -m broker_agents.cli analyze-expanded-trial-results --auto-latest --outputs-root data/outputs

python -m broker_agents.cli analyze-expanded-trial-results --expanded-trial-run-id 20260615_074713 --outputs-root data/outputs --prior-backtest-run-id 20260614_205804
```

The analyzer reads existing artifacts and does not rerun or alter the trial.
Its next action is a research evidence scorecard when instability is detected.
The output remains non-actionable: it does not create recommendations,
rankings, allocation instructions, rebalancing instructions, trade signals,
or execution instructions.

### Research Evidence Scorecard

The research evidence scorecard consolidates expanded-trial diagnostics into
one auditable research status. It scores sample strength, clean and warning
evidence, benchmark-relative and absolute outcomes, walk-forward stability,
metadata diversity, cohort and period effects, delayed anchors, outliers, and
data-integrity controls. The weights are research-governance weights, not
financial scores.

```powershell
python -m broker_agents.cli build-research-evidence-scorecard --auto-latest --outputs-root data/outputs

python -m broker_agents.cli build-research-evidence-scorecard --analysis-run-id 20260615_083635 --outputs-root data/outputs
```

The scorecard prepares the next gatekeeper step while preserving a hold bias
when expanded evidence is unstable. It does not validate a strategy or create
recommendations, rankings, allocation instructions, rebalancing instructions,
trade signals, or execution instructions.

### Research Gatekeeper

The research gatekeeper is a governance step after the research evidence
scorecard. It converts the scorecard into a deterministic `proceed`,
`proceed_with_warnings`, `hold`, or `block` decision. Unstable or mixed
evidence can therefore stop research progression even when trial execution and
data-quality controls succeeded.

```powershell
python -m broker_agents.cli run-research-gatekeeper --auto-latest --outputs-root data/outputs

python -m broker_agents.cli run-research-gatekeeper --scorecard-run-id 20260615_085455 --outputs-root data/outputs
```

The gatekeeper is non-actionable and research-only. It prevents premature
progression when expanded evidence weakens; it does not validate a strategy or
create recommendations, rankings, allocation instructions, rebalancing
instructions, trade signals, or execution instructions.

### Investor-Agent Attribution by Persona

After a research gatekeeper hold, the persona attribution report maps the
existing evidence strengths, weaknesses, and repair needs to the Buffett,
Munger, Fisher, Lynch, and Bogle personas independently. It identifies the
backoffice evidence each persona would need before a later review without
running the agents or changing their philosophies, scores, or decision logic.

```powershell
python -m broker_agents.cli build-investor-persona-attribution --auto-latest --outputs-root data/outputs

python -m broker_agents.cli build-investor-persona-attribution --gatekeeper-run-id 20260615_185320 --outputs-root data/outputs
```

The report does not ask the agents for decisions, rank or average them, create
a vote or consensus, or produce recommendations, allocation instructions,
rebalancing instructions, trade signals, or execution instructions.

### Backoffice Evidence Quality Attribution

The Backoffice evidence quality attribution is the repair-planning layer after
a gatekeeper hold and persona attribution. It converts held research evidence
into traceable issues and prioritized work orders for robustness retesting,
data repair, metadata rechecks, qualitative enrichment, persona-specific
packaging, and audit documentation.

```powershell
python -m broker_agents.cli build-backoffice-evidence-quality-attribution --auto-latest --outputs-root data/outputs

python -m broker_agents.cli build-backoffice-evidence-quality-attribution --persona-attribution-run-id 20260615_192219 --outputs-root data/outputs
```

Backoffice does not make investment decisions or override the gatekeeper. The
report prepares evidence for a future rerun and re-gating; it does not create
recommendations, rankings, consensus, allocation instructions, rebalancing
instructions, trade signals, or execution instructions.

### Backtest Driver Decomposition

The backtest driver decomposition executes BO-001 from the Backoffice repair
queue. It decomposes benchmark-relative underperformance and expanded-cohort
weakening by ticker, date, cohort, sector, category, and universe group, while
reconciling all evaluated rows back to the expanded readiness backtest.

```powershell
python -m broker_agents.cli build-backtest-driver-decomposition --auto-latest --outputs-root data/outputs

python -m broker_agents.cli build-backtest-driver-decomposition --backoffice-attribution-run-id 20260615_195343 --outputs-root data/outputs
```

This is evidence repair only. It does not rerun investor agents, change the
original backtest, validate a strategy, rank tickers, create recommendations,
allocation instructions, rebalancing instructions, trade signals, or execution
instructions.

### Outlier and Ex-NVDA Repair Path

The outlier and Ex-NVDA repair path executes BO-002 from the Backoffice repair
queue. It checks whether expanded research evidence survives exclusion of NVDA
and leading positive contributors, separates current-core and expanded-cohort
evidence, documents supportive-date dependence, and writes a retest
specification for the next repair step.

```powershell
python -m broker_agents.cli build-outlier-repair-path --auto-latest --outputs-root data/outputs

python -m broker_agents.cli build-outlier-repair-path --decomposition-run-id 20260616_171625 --outputs-root data/outputs
```

This is evidence repair only. It does not rerun investor agents, change the
original backtest, validate a strategy, rank tickers, create recommendations,
allocation instructions, rebalancing instructions, trade signals, or execution
instructions.

### Walk-Forward Stability Repair Plan

The walk-forward stability repair plan executes BO-003 from the Backoffice
repair queue. It identifies unstable historical periods, separates clean-date
and warning-date evidence, compares current-core and expanded-cohort behavior
by period, checks Ex-NVDA period behavior, and creates a retest plan before any
future re-gating.

```powershell
python -m broker_agents.cli build-walk-forward-repair-plan --auto-latest --outputs-root data/outputs

python -m broker_agents.cli build-walk-forward-repair-plan --outlier-repair-run-id 20260616_174925 --outputs-root data/outputs
```

This is evidence repair only. It does not rerun investor agents, change the
original backtest, validate a strategy, rank tickers, create recommendations,
allocation instructions, rebalancing instructions, trade signals, or execution
instructions.

### Delayed Anchor Exposure Repair

The delayed anchor exposure repair executes BO-004 from the Backoffice repair
queue. It separates clean-anchor, delayed-anchor, and unknown-anchor evidence
where available, attributes anchor exposure by date and cohort, documents when
exact delay-day fields are unavailable, and creates delayed-anchor retest
controls before any future re-gating.

```powershell
python -m broker_agents.cli build-delayed-anchor-repair --auto-latest --outputs-root data/outputs

python -m broker_agents.cli build-delayed-anchor-repair --walk-forward-repair-run-id 20260616_182026 --outputs-root data/outputs
```

This is evidence repair only. It does not rerun investor agents, change the
original backtest, validate a strategy, rank tickers, create recommendations,
allocation instructions, rebalancing instructions, trade signals, or execution
instructions.

### Metadata Diversity Recheck

The metadata diversity recheck executes BO-005 from the Backoffice repair
queue. It builds a ticker-level metadata matrix and checks concentration by
sector, category, universe group, cohort, investor-interest labels, source
verification status, and promotion bucket metadata where available.

```powershell
python -m broker_agents.cli build-metadata-diversity-recheck --auto-latest --outputs-root data/outputs

python -m broker_agents.cli build-metadata-diversity-recheck --delayed-anchor-repair-run-id 20260616_191450 --outputs-root data/outputs
```

This is evidence repair only. It does not rerun investor agents, change the
original backtest, validate a strategy, rank tickers, create recommendations,
allocation instructions, rebalancing instructions, trade signals, or execution
instructions.

### Persona-Specific Evidence Pack Requirements

The persona-specific evidence pack requirements execute BO-006 from the
Backoffice repair queue. It converts the current Gatekeeper HOLD state and
repair findings into distinct evidence checklists for Buffett, Munger, Fisher,
Lynch, and Bogle personas without asking any persona for a decision.

```powershell
python -m broker_agents.cli build-persona-evidence-pack-requirements --auto-latest --outputs-root data/outputs

python -m broker_agents.cli build-persona-evidence-pack-requirements --metadata-diversity-recheck-run-id 20260617_192720 --outputs-root data/outputs
```

This is evidence packaging only. It preserves persona independence and does not
rerun investor agents, override the Gatekeeper, validate a strategy, rank
companies or personas, create recommendations, allocation instructions,
rebalancing instructions, trade signals, or execution instructions.

### Bogle Benchmark / Index Comparison Pack

The Bogle benchmark/index comparison pack executes BO-007 from the Backoffice
repair queue. It prepares Bogle-specific evidence requirements around
benchmark-relative performance, broad-index framing, concentration risk,
clean-anchor versus delayed-anchor views, current-core versus expanded-cohort
views, and walk-forward instability.

```powershell
python -m broker_agents.cli build-bogle-benchmark-index-pack --auto-latest --outputs-root data/outputs

python -m broker_agents.cli build-bogle-benchmark-index-pack --persona-evidence-pack-run-id 20260617_200326 --outputs-root data/outputs
```

This is evidence packaging only. It does not ask Bogle for a decision, recommend
an index or stock, rank securities, create allocation instructions, create
rebalancing instructions, create trade signals, or override the Gatekeeper HOLD.

### Fisher Qualitative Growth Evidence Pack

The Fisher qualitative growth evidence pack executes BO-008 from the Backoffice
repair queue. It prepares Fisher-specific qualitative growth requirements for
product pipeline, innovation, sales organization, market expansion, management
depth, customer and competitive proxy evidence, and durable growth runway.

```powershell
python -m broker_agents.cli build-fisher-qualitative-growth-pack --auto-latest --outputs-root data/outputs

python -m broker_agents.cli build-fisher-qualitative-growth-pack --bogle-benchmark-pack-run-id 20260617_204227 --outputs-root data/outputs
```

This is evidence packaging only. It does not ask Fisher for a decision, rerun
investor agents, recommend a company, rank companies, create allocation
instructions, create rebalancing instructions, create trade signals, or override
the Gatekeeper HOLD.

### Buffett/Munger Quality and Risk Pack

The Buffett/Munger quality and risk pack executes BO-009 from the Backoffice
repair queue. It prepares Buffett-specific quality, owner earnings, valuation
assumption, margin-of-safety discussion, and capital allocation evidence
requirements while separately preparing Munger-specific moat, incentives,
inversion, hidden-risk, and failure-mode evidence requirements.

```powershell
python -m broker_agents.cli build-buffett-munger-quality-risk-pack --auto-latest --outputs-root data/outputs

python -m broker_agents.cli build-buffett-munger-quality-risk-pack --fisher-growth-pack-run-id 20260618_063909 --outputs-root data/outputs
```

This is evidence packaging only. It does not ask Buffett or Munger for
decisions, compute intrinsic values, create price targets, recommend a company,
rank companies, create allocation instructions, create rebalancing instructions,
create trade signals, or override the Gatekeeper HOLD.

### Research Audit Trail Bundle

The research audit trail bundle executes BO-010 from the Backoffice repair
queue. It closes Phase 15, the Backoffice Repair Execution Layer, by linking the
Gatekeeper HOLD decision, Backoffice evidence issues, BO-001 through BO-010
repair work orders, generated report paths, safety boundaries, and remaining
re-gate prerequisites.

```powershell
python -m broker_agents.cli build-research-audit-trail-bundle --auto-latest --outputs-root data/outputs

python -m broker_agents.cli build-research-audit-trail-bundle --buffett-munger-pack-run-id 20260618_065614 --outputs-root data/outputs
```

This is audit and documentation only. It does not rerun Gatekeeper, allow
persona review, recommend a company, rank companies, create allocation
instructions, create rebalancing instructions, create trade signals, or override
the Gatekeeper HOLD.

### Re-Run & Re-Gate Plan

The re-run and re-gate plan starts Phase 16, the Re-Run & Re-Gate
Layer. It converts the completed research audit trail into a planning-only
roadmap for controlled re-run packaging, future controlled trial execution,
pre/post repair comparison, and later Gatekeeper re-evaluation.

```powershell
python -m broker_agents.cli build-re-run-re-gate-plan --auto-latest --outputs-root data/outputs

python -m broker_agents.cli build-re-run-re-gate-plan --research-audit-trail-run-id 20260618_072740 --outputs-root data/outputs
```

This is planning only. It does not execute a re-run, rerun Gatekeeper, allow
persona review, recommend a company, rank companies, create allocation
instructions, create rebalancing instructions, create trade signals, or create
execution instructions. Task 119 satisfies only the re-run/retest planning
prerequisite; it leaves Gatekeeper re-evaluation for a later task.

### Re-Run Input Package

The re-run input package executes Task 120 in Phase 16. It converts the
re-run/re-gate plan into a controlled input package for Task 121, including the
universe matrix, date matrix, control matrix, artifact source map, Task 121
execution manifest, and validation checks.

```powershell
python -m broker_agents.cli build-re-run-input-package --auto-latest --outputs-root data/outputs

python -m broker_agents.cli build-re-run-input-package --re-run-re-gate-plan-run-id 20260618_083143 --outputs-root data/outputs
```

This is input packaging only. It does not execute the re-run, rerun Gatekeeper,
allow persona review, recommend a company, rank companies, create allocation
instructions, create rebalancing instructions, create trade signals, or create
execution instructions.

### Controlled Re-Run Trial

The controlled re-run trial executes Task 121 in Phase 16. It consumes the Task
120 input package and reports local scenario results, control diagnostics,
limitations, and the Task 122 handoff manifest for future pre-repair versus
post-repair comparison.

```powershell
python -m broker_agents.cli execute-controlled-re-run-trial --auto-latest --outputs-root data/outputs

python -m broker_agents.cli execute-controlled-re-run-trial --re-run-input-package-run-id 20260618_085936 --outputs-root data/outputs
```

This is a controlled research re-run only. It does not rerun Gatekeeper, allow
persona review, recommend a company, rank companies, create allocation
instructions, create rebalancing instructions, create trade signals, or create
execution instructions.

### Pre/Post Repair Evidence Comparison

The pre/post repair evidence comparison executes Task 122 in Phase 16. It
consumes the Task 121 controlled re-run trial and compares pre-repair evidence
with post-controlled-re-run evidence across evidence deltas, scenario deltas,
stability deltas, limitation resolution, and Task 123 handoff readiness.

```powershell
python -m broker_agents.cli compare-pre-post-repair-evidence --auto-latest --outputs-root data/outputs

python -m broker_agents.cli compare-pre-post-repair-evidence --controlled-re-run-trial-run-id 20260618_094644 --outputs-root data/outputs
```

This is comparison only. It does not rerun Gatekeeper, allow persona review,
recommend a company, rank companies, create allocation instructions, create
rebalancing instructions, create trade signals, or create execution
instructions.

### Gatekeeper Re-Evaluation

The Gatekeeper re-evaluation executes Task 123 in Phase 16. It consumes the
Task 122 pre/post repair comparison and performs a research Gatekeeper
re-evaluation with readiness inputs, rule evaluations, evidence change
assessment, safety checks, a decision record, next-phase options, and a Task
124 handoff.

```powershell
python -m broker_agents.cli run-gatekeeper-re-evaluation --auto-latest --outputs-root data/outputs

python -m broker_agents.cli run-gatekeeper-re-evaluation --pre-post-repair-comparison-run-id 20260618_105141 --outputs-root data/outputs
```

This is a research Gatekeeper re-evaluation only. It does not run investor
agents, allow persona review automatically, recommend a company, rank
companies, create allocation instructions, create rebalancing instructions,
create trade signals, or create execution instructions.

### Phase 16 Closure & Next-Phase Recommendation

The Phase 16 closure executes Task 124. It consumes the Task 123 Gatekeeper
re-evaluation, preserves the final Gatekeeper outcome, closes Phase 16, and
recommends the next governance phase. With a `hold_with_repair_progress`
outcome, the next phase is targeted evidence stabilization rather than persona
review.

```powershell
python -m broker_agents.cli close-phase-16 --auto-latest --outputs-root data/outputs

python -m broker_agents.cli close-phase-16 --gatekeeper-re-evaluation-run-id 20260618_111449 --outputs-root data/outputs
```

This is phase closure and governance planning only. It does not rerun
Gatekeeper, run investor agents, allow persona review, recommend a company,
rank companies, create allocation instructions, create rebalancing
instructions, create trade signals, or create execution instructions.

### Targeted Evidence Stabilization Plan

The targeted evidence stabilization plan executes Task 125 and starts Phase 17.
It consumes the Phase 16 closure, preserves the `hold_with_repair_progress`
state, and converts residual blockers into stabilization workstreams,
priorities, success criteria, blocked actions, and a Task 126 handoff.

```powershell
python -m broker_agents.cli define-targeted-evidence-stabilization-plan --auto-latest --outputs-root data/outputs

python -m broker_agents.cli define-targeted-evidence-stabilization-plan --phase-16-closure-run-id 20260618_115312 --outputs-root data/outputs
```

This is research-only planning. It does not execute repairs, rerun Gatekeeper,
run investor agents, allow persona review, recommend a company, rank companies,
create allocation instructions, create rebalancing instructions, create trade
signals, or create execution instructions.

### Residual Blocker Work Orders

The residual blocker work-order package executes Task 126. It consumes the
Task 125 targeted evidence stabilization plan, converts residual blockers into
work orders, defines dependencies, input requirements, success criteria, and
the execution sequence, and prepares the Task 127 execution manifest.

```powershell
python -m broker_agents.cli build-residual-blocker-work-orders --auto-latest --outputs-root data/outputs

python -m broker_agents.cli build-residual-blocker-work-orders --stabilization-plan-run-id 20260618_163127 --outputs-root data/outputs
```

This is research-only work-order packaging. It does not execute repairs, rerun
Gatekeeper, run investor agents, allow persona review, recommend a company,
rank companies, create allocation instructions, create rebalancing
instructions, create trade signals, or create execution instructions.

### Targeted Evidence Repairs

The targeted evidence repairs package executes Task 127. It consumes Task 126
residual blocker work orders, performs controlled local evidence repair
packaging, documents bounded findings and remaining limitations, and prepares
the Task 128 validation input manifest.

```powershell
python -m broker_agents.cli execute-targeted-evidence-repairs --auto-latest --outputs-root data/outputs

python -m broker_agents.cli execute-targeted-evidence-repairs --residual-work-order-package-run-id 20260618_183647 --outputs-root data/outputs
```

This is research-only repair execution. It does not rerun Gatekeeper, run
investor agents, allow persona review, recommend a company, rank companies,
create allocation instructions, create rebalancing instructions, create trade
signals, or create execution instructions.

### Stabilization Validation Trial

The stabilization validation trial executes Task 128. It consumes Task 127
targeted evidence repairs, validates repair outputs and residual uncertainty,
and prepares the Task 129 handoff for comparing the Task 123 Gatekeeper baseline
against stabilized evidence.

```powershell
python -m broker_agents.cli run-stabilization-validation-trial --auto-latest --outputs-root data/outputs

python -m broker_agents.cli run-stabilization-validation-trial --targeted-repair-run-id 20260618_190207 --outputs-root data/outputs
```

This is research-only validation. It does not rerun Gatekeeper, run investor
agents, allow persona review, recommend a company, rank companies, create
allocation instructions, create rebalancing instructions, create trade signals,
or create execution instructions.

### Gatekeeper 123 vs Stabilized Evidence Comparison

The Gatekeeper 123 vs stabilized evidence comparison executes Task 129. It
consumes the Task 128 stabilization validation trial, compares it with the Task
123 Gatekeeper baseline, and prepares the Task 130 Gatekeeper Stabilization
Re-Review handoff.

```powershell
python -m broker_agents.cli compare-gatekeeper-stabilized-evidence --auto-latest --outputs-root data/outputs

python -m broker_agents.cli compare-gatekeeper-stabilized-evidence --stabilization-validation-run-id 20260618_193123 --outputs-root data/outputs

python -m broker_agents.cli compare-gatekeeper-stabilized-evidence --stabilization-validation-run-id 20260618_193123 --gatekeeper-re-evaluation-run-id 20260618_111449 --outputs-root data/outputs
```

This is research-only comparison. It does not rerun Gatekeeper, issue a new
Gatekeeper decision, run investor agents, allow persona review, recommend a
company, rank companies, create allocation instructions, create rebalancing
instructions, create trade signals, or create execution instructions.

### Gatekeeper Stabilization Re-Review

The Gatekeeper Stabilization Re-Review executes Task 130. It consumes the Task
129 Gatekeeper 123 vs Stabilized Evidence Comparison and performs a conservative
Gatekeeper stabilization re-review for Phase 17 closure.

```powershell
python -m broker_agents.cli run-gatekeeper-stabilization-re-review --auto-latest --outputs-root data/outputs

python -m broker_agents.cli run-gatekeeper-stabilization-re-review --gatekeeper-stabilized-comparison-run-id 20260618_210843 --outputs-root data/outputs
```

This is research-only governance re-review. It does not run investor agents,
run actual persona review, recommend a company, rank companies, create
allocation instructions, create rebalancing instructions, create trade signals,
or create execution instructions.

### Phase 17 Closure & Next-Step Decision

The Phase 17 Closure & Next-Step Decision executes Task 131. It consumes the
Task 130 Gatekeeper Stabilization Re-Review, closes the targeted evidence
stabilization layer, preserves the limited Gatekeeper return package scope, and
prepares the Task 132 handoff.

```powershell
python -m broker_agents.cli close-phase-17 --auto-latest --outputs-root data/outputs

python -m broker_agents.cli close-phase-17 --gatekeeper-stabilization-re-review-run-id 20260618_213210 --outputs-root data/outputs
```

This is phase closure and next-step governance only. It does not allow persona
review, run investor agents, recommend a company, rank companies, create
allocation instructions, create rebalancing instructions, create trade signals,
create execution instructions, validate a strategy, or enable auto-promotion.

### Gatekeeper Return Package Plan

The Gatekeeper Return Package Plan executes Task 132 and starts Phase 18. It
consumes Phase 17 closure and defines the plan for a Gatekeeper return package,
including package components, evidence inventory, residual risk disclosure,
permission boundaries, and the Phase 18 roadmap.

```powershell
python -m broker_agents.cli define-gatekeeper-return-package-plan --auto-latest --outputs-root data/outputs

python -m broker_agents.cli define-gatekeeper-return-package-plan --phase-17-closure-run-id 20260619_062711 --outputs-root data/outputs
```

This is research-only planning. It does not build the final package, rerun
Gatekeeper, run investor agents, allow actual persona review, recommend a
company, rank companies, create allocation instructions, create rebalancing
instructions, create trade signals, create execution instructions, validate a
strategy, or enable auto-promotion.

### Gatekeeper Return Package Input Inventory

The Gatekeeper Return Package Input Inventory executes Task 133. It consumes
the Task 132 Gatekeeper Return Package Plan, inventories planned components,
maps evidence artifacts to local source files, checks source-run traceability,
and prepares the Task 134 handoff for package assembly.

```powershell
python -m broker_agents.cli build-gatekeeper-return-input-inventory --auto-latest --outputs-root data/outputs

python -m broker_agents.cli build-gatekeeper-return-input-inventory --gatekeeper-return-plan-run-id 20260619_064951 --outputs-root data/outputs
```

This is research-only input inventory. It does not assemble the final package,
rerun Gatekeeper, run investor agents, allow actual persona review, recommend a
company, rank companies, create allocation instructions, create rebalancing
instructions, create trade signals, create execution instructions, validate a
strategy, or enable auto-promotion.

### Gatekeeper Return Package Assembly

The Gatekeeper Return Package Assembly executes Task 134. It consumes the Task
133 input inventory and assembles the Gatekeeper-facing return package with
section, evidence-reference, residual-risk, permission-boundary, limitation, and
Task 135 handoff matrices.

```powershell
python -m broker_agents.cli assemble-gatekeeper-return-package --auto-latest --outputs-root data/outputs

python -m broker_agents.cli assemble-gatekeeper-return-package --gatekeeper-return-input-inventory-run-id 20260619_072007 --outputs-root data/outputs
```

This is research-only package assembly. It does not validate final completeness,
rerun Gatekeeper, run investor agents, allow actual persona review, recommend a
company, rank companies, create allocation instructions, create rebalancing
instructions, create trade signals, create execution instructions, validate a
strategy, or enable auto-promotion.

### Gatekeeper Return Package Completeness Validation

The Gatekeeper Return Package Completeness Validation executes Task 135. It
consumes the Task 134 Gatekeeper Return Package and validates required sections,
evidence references, residual risk disclosures, permission boundaries,
limitations, safety boundaries, and the Task 136 handoff.

```powershell
python -m broker_agents.cli validate-gatekeeper-return-package --auto-latest --outputs-root data/outputs

python -m broker_agents.cli validate-gatekeeper-return-package --gatekeeper-return-package-run-id 20260619_081150 --outputs-root data/outputs
```

This is research-only completeness validation. It does not rerun Gatekeeper, run
investor agents, allow actual persona review, recommend a company, rank
companies, create allocation instructions, create rebalancing instructions,
create trade signals, create execution instructions, validate a strategy, or
enable auto-promotion.

### Gatekeeper Return Review

The Gatekeeper Return Review executes Task 136. It consumes the Task 135
Gatekeeper Return Package Completeness Validation and performs a conservative
Gatekeeper-only review of the validated return package, including warnings,
residual risks, permission boundaries, and post-review scope.

```powershell
python -m broker_agents.cli run-gatekeeper-return-review --auto-latest --outputs-root data/outputs

python -m broker_agents.cli run-gatekeeper-return-review --gatekeeper-return-package-validation-run-id 20260619_083419 --outputs-root data/outputs
```

This is research-only Gatekeeper review. It does not run investor agents, allow
actual persona review, recommend a company, rank companies, create allocation
instructions, create rebalancing instructions, create trade signals, create
execution instructions, validate a strategy, or enable auto-promotion.

### Readiness Trial Diagnostic Report

Readiness trial backtests now create a diagnostic report beside the decision
report:

```powershell
python -m broker_agents.cli backtest-signals --ledger data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv --price-provider csv --price-fixtures tests/fixtures/historical_price_history --outputs-root data/outputs --lookback-years 5 --dedupe-mode latest_per_ticker_per_day --walk-forward --walk-forward-frequency yearly
```

The decision report states whether results are decision-grade. The diagnostic
report explains what is driving results through several focused reviews. It
covers period, ticker, outlier, horizon, concentration, stability, and
missing-metadata drivers. It is research-only and does not create
recommendations or trade signals.

Regenerate diagnostics from an existing readiness backtest folder with:

```powershell
python -m broker_agents.cli generate-readiness-trial-diagnostic-report --backtest-folder data/outputs/backtests/{RUN_ID}
```

### Readiness Trial Metadata Enrichment

Readiness trial export now enriches research rows from existing structured local
run manifests and deal-package JSON artifacts. Available metadata includes
readiness status, source verification counts, promotion blockers, and investor
interest and existing decision fields. Missing metadata remains explicit, source
paths are recorded, and no value is fabricated.

```powershell
python -m broker_agents.cli export-readiness-trial-ledger --outputs-root data/outputs --output-ledger data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv

python -m broker_agents.cli validate-readiness-trial-ledger --ledger data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv

python -m broker_agents.cli backtest-signals --ledger data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv --price-provider csv --price-fixtures tests/fixtures/historical_price_history --outputs-root data/outputs --lookback-years 5 --dedupe-mode latest_per_ticker_per_day --walk-forward --walk-forward-frequency yearly
```

This enrichment is research-only. It does not convert readiness artifacts into
recommendations, rankings, allocation instructions, or trade signals.

### Metadata-Aware Diagnostic Attribution

The readiness trial diagnostic report uses enriched grouped metrics to examine
whether readiness labels, source verification states, promotion blocker
buckets, or investor interest levels are associated with different outcomes.
Comparisons are conservative: groups below five records remain small-sample
limited, and fields dominated by one group are reported as low-diversity rather
than explanatory.

This attribution does not prove causality, validate an investor philosophy, or
create recommendations or trade signals. It identifies preliminary associations
and clearly records when the current metadata cannot explain performance
differences.

### Investor Response Letters

Each broker deal package now includes one broker-facing response letter from
Buffett, Munger, Fisher, Lynch, and Bogle. Every letter independently states
the interest level, interest type, main concern, and evidence required before
stronger interest. These letters are communication artifacts only; they are
not recommendations, votes, consensus, allocations, or trade instructions.

### Broker Deal Executive Summary

Each broker deal package begins with an executive summary that groups
conditional, watchlist, needs-evidence, low-interest, index-preferred, and pass
responses. It highlights positive themes, evidence blockers, and non-execution
Backoffice next actions. It does not rank investors, create consensus, or
recommend a transaction.

## Deal Intake / New Ticker Readiness

Deal intake is a filesystem preflight for a new broker submission. It checks
whether the required manual Backoffice pack exists, identifies available
offline enrichment fixtures, and lists the work needed before `run-deal`.
Fixtures are optional but improve enrichment. Portfolio context is also
optional unless Bogle-specific portfolio fit analysis is needed.

```powershell
broker-agents deal-intake --ticker MSFT --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml --output data/outputs/MSFT/deal_intake_report.md --json-output data/outputs/MSFT/deal_intake_report.json
```

Generate intake reports for all current manual examples:

```powershell
broker-agents deal-intakes --tickers MSFT,AAPL,NVDA,COST --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml
```

The intake step does not enrich data, run investor agents, or create a deal
package. It does not make recommendations or change decisions. Use
`examples/deal_intake_template.yaml` to capture a new submission before
creating its full Backoffice Data Pack.

## Trial Run / Demo

Use [the trial run checklist](docs/trial_run_checklist.md) to verify the full
Backoffice, independent investor-agent, and broker-package workflow for MSFT,
AAPL, NVDA, and COST. Record observations in
[the trial results template](docs/trial_run_results_template.md).

Run the complete trial sequence with Bash:

```bash
bash scripts/run_trial_demo.sh
```

Run it with PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_trial_demo.ps1
```

Without the wrapper scripts, run `ruff check .`, `pytest`, the four-ticker
`deal-intakes` command, and then the four-ticker `run-deals` command shown in
the checklist.

Review each ticker's intake report, broker deal package, five investor response
letters, and detailed investor outputs under `data/outputs/{TICKER}/`. This is
a system trial only; it does not create a recommendation, allocation, or trade
instruction.

## Data Philosophy

Every metric and conclusion should eventually trace back to a source record with:

- Source name and URL or local reference.
- Retrieval date.
- Confidence score.
- Freshness assessment.
- Notes about missing, estimated, or conflicting values.

## Status

Scaffold only. No production logic is implemented.
