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
