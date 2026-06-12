# User-Supplied Historical Financials CSV Files

This folder is for user-supplied point-in-time financial statement snapshots. No live SEC or API fetching is performed. Files must record when a
financial fact became available so future historical analysis can avoid using
facts that were not public by the requested `as_of_date`.

Suggested filenames:

- `msft_financials_as_of.csv`
- `aapl_financials_as_of.csv`
- `nvda_financials_as_of.csv`
- `cost_financials_as_of.csv`

## Required Columns

- `ticker`
- `fiscal_period_end_date`
- `filing_date`
- `accepted_date`
- `statement_type`
- `period_type`
- `metric`
- `value`
- `source_url_or_accession_number`

`fiscal_period_end_date` identifies the reporting period, but does not prove
when the information was available. A row is point-in-time eligible only when
`filing_date <= as_of_date` or `accepted_date <= as_of_date`. If both
availability fields are blank, the row is not point-in-time safe.

Allowed `statement_type` examples include `income_statement`,
`balance_sheet`, `cash_flow`, `ratios`, `segment`, and `other`. Allowed
`period_type` examples include `annual`, `quarterly`, and
`trailing_twelve_months`.

## Optional Columns

- `currency`
- `units`
- `form_type`
- `fiscal_year`
- `fiscal_quarter`
- `data_as_of_date`
- `ingestion_date`
- `source_name`

These are user-supplied local files for research and pipeline validation only.
Keep large production or licensed datasets out of Git unless they are
intentionally small and documented. This format does not generate historical
investor signals and does not guarantee source provenance beyond the supplied
traceability fields.

This historical financials CSV input format is not a recommendation, ranking,
vote, average score, consensus, allocation instruction, rebalancing
instruction, or trade signal.
