$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $ProjectRoot

try {
    $Tickers = "MSFT,AAPL,NVDA,COST"

    Write-Host "Running Ruff..."
    ruff check .
    if ($LASTEXITCODE -ne 0) {
        throw "Ruff failed with exit code $LASTEXITCODE."
    }

    Write-Host "Running pytest..."
    pytest
    if ($LASTEXITCODE -ne 0) {
        throw "Pytest failed with exit code $LASTEXITCODE."
    }

    Write-Host "Checking deal intake readiness..."
    broker-agents deal-intakes `
        --tickers $Tickers `
        --examples-root examples `
        --outputs-root data/outputs `
        --fixtures-root tests/fixtures `
        --portfolio-context examples/portfolio_context.yaml
    if ($LASTEXITCODE -ne 0) {
        throw "Deal intake batch failed with exit code $LASTEXITCODE."
    }

    Write-Host "Generating broker deal packages..."
    broker-agents run-deals `
        --tickers $Tickers `
        --examples-root examples `
        --outputs-root data/outputs `
        --fixtures-root tests/fixtures `
        --portfolio-context examples/portfolio_context.yaml
    if ($LASTEXITCODE -ne 0) {
        throw "Broker deal batch failed with exit code $LASTEXITCODE."
    }

    Write-Host "Generated broker deal packages:"
    foreach ($Ticker in @("MSFT", "AAPL", "NVDA", "COST")) {
        $Lower = $Ticker.ToLowerInvariant()
        Write-Host "data/outputs/$Ticker/deal_package/${Lower}_broker_deal_package.md"
    }
}
finally {
    Pop-Location
}
