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
