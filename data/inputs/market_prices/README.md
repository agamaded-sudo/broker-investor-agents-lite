# User-Supplied Market Price CSV Files

Place locally supplied market-price histories in this folder using lower-case
ticker filenames:

- `msft.csv`
- `aapl.csv`
- `nvda.csv`
- `cost.csv`
- `spy.csv`

## Expected Columns

Required:

- `date`
- `close`, unless an adjusted-close column is supplied

Optional:

- `open`
- `high`
- `low`
- `adjusted_close`
- `volume`

Common variants such as `Date`, `Close`, `adj_close`, `Adj Close`, and
`Adjusted Close` are accepted. Adjusted close is preferred for backtesting;
when present it is used instead of close.

These files are user-supplied market data. Keep production-size or licensed
datasets out of Git unless they are explicitly small and intended for the
repository. The deterministic files under `tests/fixtures/price_history/`
remain the source for automated tests.

No API keys or network calls are used by the local CSV provider.
