$ErrorActionPreference = "Stop"

Write-Host "=== Broker Investor Agents: First Stable Demo ==="

Write-Host "`n[1/4] Running Ruff..."
python -m ruff check .

Write-Host "`n[2/4] Running Pytest..."
python -m pytest --basetemp=.pytest_tmp_demo

Write-Host "`n[3/4] Running deal intakes..."
python -m broker_agents.cli deal-intakes --tickers MSFT,AAPL,NVDA,COST --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml

Write-Host "`n[4/4] Running broker deal packages..."
python -m broker_agents.cli run-deals --tickers MSFT,AAPL,NVDA,COST --examples-root examples --outputs-root data/outputs --fixtures-root tests/fixtures --portfolio-context examples/portfolio_context.yaml

Write-Host "`n=== Demo output files ==="
Write-Host "MSFT: data\outputs\MSFT\deal_package\msft_broker_deal_package.md"
Write-Host "AAPL: data\outputs\AAPL\deal_package\aapl_broker_deal_package.md"
Write-Host "NVDA: data\outputs\NVDA\deal_package\nvda_broker_deal_package.md"
Write-Host "COST: data\outputs\COST\deal_package\cost_broker_deal_package.md"

Write-Host "`nDemo completed successfully."
