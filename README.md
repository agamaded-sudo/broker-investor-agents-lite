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
