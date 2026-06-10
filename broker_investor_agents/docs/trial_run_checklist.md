# Trial Run Checklist — Backoffice + Investor Agents

## 1. Purpose

This checklist tests the core workflow where a ticker is submitted, Backoffice
prepares and enriches the company file, investor agents review it independently,
and the broker receives a deal package.

## 2. Scope of This Trial

In scope:

- Deal intake
- Backoffice enrichment
- Source verification
- Investor reports
- Investor response letters
- Broker deal package
- Executive summary

Out of scope:

- Opportunity Scout Intern
- Portfolio Manager
- Human review operations
- Portfolio allocation
- Trading or execution
- Live data fetching

## 3. Companies for Trial

| Ticker | Company | Business Model | Purpose of Test |
| --- | --- | --- | --- |
| MSFT | Microsoft Corporation | Software / Cloud / AI infrastructure | High-quality compounder and capex sensitivity |
| AAPL | Apple Inc. | Consumer ecosystem / services | Mature quality, buybacks, and ecosystem durability |
| NVDA | NVIDIA Corporation | Semiconductor / AI compute | High growth and cyclicality |
| COST | Costco Wholesale Corporation | Retail membership | Non-tech quality and valuation discipline |

## 4. Pre-Run Checks

- [ ] Ruff passes.
- [ ] Pytest passes.
- [ ] Each manual input pack exists.
- [ ] Each enrichment fixture set exists.
- [ ] Portfolio context exists if it will be used.
- [ ] Deal intake reports `Ready for Deal Workflow`.

Expected manual packs:

- `examples/msft_input.yaml`
- `examples/aapl_input.yaml`
- `examples/nvda_input.yaml`
- `examples/cost_input.yaml`

Expected fixture types for each ticker:

- SEC company facts
- Market data
- Historical valuation
- Growth and PEG

## 5. Run Commands

Run from the project root:

```text
ruff check .
pytest

broker-agents deal-intakes --tickers MSFT,AAPL,NVDA,COST --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml

broker-agents run-deals --tickers MSFT,AAPL,NVDA,COST --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml
```

The same sequence is available through:

```text
bash scripts/run_trial_demo.sh
powershell -ExecutionPolicy Bypass -File scripts/run_trial_demo.ps1
```

## 6. Outputs to Review

For each ticker, review:

- `data/outputs/{TICKER}/deal_intake_report.md`
- `data/outputs/{TICKER}/deal_package/{ticker_lower}_broker_deal_package.md`
- `data/outputs/{TICKER}/deal_package/investor_response_letters/`
- `data/outputs/{TICKER}/deal_package/investor_outputs/`

Confirm that the broker package JSON and intake JSON also exist when structured
output needs inspection.

## 7. Broker Review Checklist

For each ticker:

- [ ] Is the intake status correct?
- [ ] Did all enrichment sources apply?
- [ ] Is the executive summary readable?
- [ ] Are investor responses independent?
- [ ] Are response letters clear?
- [ ] Are main concerns understandable?
- [ ] Are required evidence items useful?
- [ ] Is there any accidental ranking or consensus?
- [ ] Is there any accidental trade or execution language?
- [ ] Does the package help the broker identify the next Backoffice action?

## 8. Investor Response Review

For Buffett, Munger, Fisher, Lynch, and Bogle:

- [ ] Does the response match the investor's philosophy?
- [ ] Is the interest level reasonable?
- [ ] Is the main concern clear?
- [ ] Is the required evidence specific?
- [ ] Is the final response wording useful to the broker?

Also compare the four companies. The responses should reflect their distinct
business models rather than repeating generic language.

## 9. Trial Notes Template

```text
Ticker:
Package reviewed:
What worked:
What was unclear:
Investor response quality:
Backoffice evidence quality:
Missing evidence:
Unexpected behavior:
Next action:
Ready for broader testing? Yes/No
```

Use `docs/trial_run_results_template.md` for a complete multi-company record.

## 10. Pass / Fail Criteria

Pass if:

- All commands run successfully.
- All four deal packages are generated.
- Each ticker has five response letters.
- Executive summaries are readable.
- Investor responses remain independent.
- No ranking, consensus, allocation, or execution language appears.
- Final decisions remain unchanged.
- Auto-promotion remains disabled.

Fail if:

- The pipeline crashes.
- A deal package is missing.
- An investor report is missing.
- Response letters are missing.
- Investor responses look identical or generic.
- A package creates a ranking or consensus.
- A package implies trade action.
- Final decisions change unexpectedly.
- Auto-promotion becomes enabled.

## 11. Safety Reminder

This trial is for system testing only. It is not investment advice, not a
recommendation, not an allocation plan, and not a trade instruction.
