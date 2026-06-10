#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

TICKERS="MSFT,AAPL,NVDA,COST"

echo "Running Ruff..."
ruff check .

echo "Running pytest..."
pytest

echo "Checking deal intake readiness..."
broker-agents deal-intakes \
  --tickers "${TICKERS}" \
  --examples-root examples \
  --outputs-root data/outputs \
  --fixtures-root tests/fixtures \
  --portfolio-context examples/portfolio_context.yaml

echo "Generating broker deal packages..."
broker-agents run-deals \
  --tickers "${TICKERS}" \
  --examples-root examples \
  --outputs-root data/outputs \
  --fixtures-root tests/fixtures \
  --portfolio-context examples/portfolio_context.yaml

echo "Generated broker deal packages:"
for ticker in MSFT AAPL NVDA COST; do
  lower="$(printf '%s' "${ticker}" | tr '[:upper:]' '[:lower:]')"
  echo "data/outputs/${ticker}/deal_package/${lower}_broker_deal_package.md"
done
