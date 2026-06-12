# Historical Trial Ledgers

This folder is for user-supplied or sample historical signal ledgers used with
real local CSV price data or deterministic historical test fixtures.

Historical trial ledgers make it possible to validate 3-month, 6-month, and
12-month backtest windows before live market-data integration. Price files must
cover each signal date and the full forward window being evaluated.

The included `sample_historical_signal_ledger.csv` contains synthetic,
reconstructed signal inputs for pipeline validation and research testing only.
It is not a record of real historical investor decisions and is not a source
of investment recommendations.

User-supplied trial ledgers should follow the signal archive schema expected by
`backtest-signals`, including:

- `ticker`
- `run_id`
- `archive_record_id`
- `generated_at`
- `status`
- readiness and source-verification fields
- promotion blockers and work-order count
- the five investor interest-level fields

The optional `trial_signal_source` field should identify reconstructed inputs,
for example `synthetic_trial_ledger`.

These files are research inputs only. They do not produce recommendations,
rankings, allocations, or trade signals.
