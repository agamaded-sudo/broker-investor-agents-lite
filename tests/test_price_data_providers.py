"""Tests for offline price provider adapters and the live stub."""

from pathlib import Path

from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.data_providers.csv_price_provider import CsvPriceProvider
from broker_agents.data_providers.fixture_price_provider import (
    FixturePriceProvider,
)
from broker_agents.data_providers.live_stub_price_provider import (
    LIVE_STUB_MESSAGE,
    LiveStubPriceProvider,
)
from broker_agents.data_providers.price_csv_validation import (
    validate_price_csvs,
)

ROOT = Path(__file__).resolve().parents[1]
PRICE_FIXTURES = ROOT / "tests" / "fixtures" / "price_history"


def test_fixture_provider_loads_synthetic_history() -> None:
    provider = FixturePriceProvider(PRICE_FIXTURES)

    result = provider.get_price_history("COST")

    assert result.status == "available"
    assert result.provider_name == "fixture"
    assert result.data_type == "synthetic_fixture"
    assert len(result.rows) == 13
    assert result.rows[0].close == 920


def test_csv_provider_loads_local_history_and_handles_missing() -> None:
    provider = CsvPriceProvider(PRICE_FIXTURES)

    available = provider.get_price_history("MSFT")
    missing = provider.get_price_history("MISSING")

    assert available.status == "available"
    assert available.provider_name == "csv"
    assert available.data_type == "local_csv"
    assert available.price_column_used == "close"
    assert available.rows
    assert missing.status == "missing_price_data"
    assert missing.rows == []
    assert "not found" in missing.warnings[0]


def test_live_stub_is_controlled_and_network_free() -> None:
    provider = LiveStubPriceProvider()

    result = provider.get_price_history("NVDA")

    assert result.status == "live_provider_not_configured"
    assert result.provider_name == "live_stub"
    assert result.data_type == "live_stub"
    assert result.rows == []
    assert result.warnings == [LIVE_STUB_MESSAGE]
    module_text = (
        ROOT
        / "src"
        / "broker_agents"
        / "data_providers"
        / "live_stub_price_provider.py"
    ).read_text(encoding="utf-8")
    for forbidden in ("requests", "httpx", "urllib", "socket", "api_key"):
        assert forbidden not in module_text.lower()


def test_csv_provider_prefers_adjusted_close(tmp_path: Path) -> None:
    (tmp_path / "test.csv").write_text(
        "date,close,adjusted_close\n"
        "2026-01-01,100,90\n"
        "2026-02-01,110,99\n",
        encoding="utf-8",
    )

    result = CsvPriceProvider(tmp_path).get_price_history("TEST")

    assert result.status == "available"
    assert result.price_column_used == "adjusted_close"
    assert [point.close for point in result.rows] == [90, 99]


def test_csv_provider_supports_common_header_variants(
    tmp_path: Path,
) -> None:
    (tmp_path / "test.csv").write_text(
        "Date,Close,Adj Close\n"
        "2026-01-01,100,95\n"
        "2026-02-01,110,104.5\n",
        encoding="utf-8",
    )

    adjusted = CsvPriceProvider(tmp_path).get_price_history("TEST")
    (tmp_path / "test.csv").write_text(
        "Date,Close\n"
        "2026-01-01,100\n"
        "2026-02-01,110\n",
        encoding="utf-8",
    )
    close_only = CsvPriceProvider(tmp_path).get_price_history("TEST")

    assert adjusted.price_column_used == "adjusted_close"
    assert adjusted.rows[-1].close == 104.5
    assert close_only.price_column_used == "close"
    assert close_only.rows[-1].close == 110


def test_validate_price_csv_reports_local_file_metadata(
    tmp_path: Path,
) -> None:
    (tmp_path / "cost.csv").write_text(
        "Date,Close,Adjusted Close\n"
        "2026-01-01,900,895\n"
        "2026-02-01,920,915\n",
        encoding="utf-8",
    )

    direct = validate_price_csvs(["COST", "MISSING"], tmp_path)
    command = CliRunner().invoke(
        app,
        [
            "validate-price-csv",
            "--price-provider",
            "csv",
            "--price-fixtures",
            str(tmp_path),
            "--tickers",
            "COST,MISSING",
        ],
    )

    assert direct[0].file_found is True
    assert direct[0].rows_count == 2
    assert direct[0].min_date == "2026-01-01"
    assert direct[0].max_date == "2026-02-01"
    assert direct[0].price_column_used == "adjusted_close"
    assert direct[0].status == "available"
    assert direct[1].file_found is False
    assert direct[1].status == "missing_price_data"
    assert command.exit_code == 0, command.output
    for text in (
        "Local Price CSV Validation",
        "file_found=true",
        "rows=2",
        "min_date=2026-01-01",
        "max_date=2026-02-01",
        "price_column_used=adjusted_close",
        "status=available",
        "status=missing_price_data",
    ):
        assert text in command.output


def test_market_data_selection_docs_and_input_convention_exist() -> None:
    selection = (
        ROOT / "docs" / "market_data_provider_selection.md"
    ).read_text(encoding="utf-8")
    input_readme = (
        ROOT / "data" / "inputs" / "market_prices" / "README.md"
    ).read_text(encoding="utf-8")

    for text in (
        "Local CSV",
        "Alpha Vantage",
        "Financial Modeling Prep",
        "Polygon",
        "Tiingo",
        "Twelve Data",
        "Nasdaq Data Link",
        "IBKR",
        "Adjusted close is preferred",
        "no live API integration",
    ):
        assert text.lower() in selection.lower()
    for text in (
        "msft.csv",
        "aapl.csv",
        "nvda.csv",
        "cost.csv",
        "spy.csv",
        "date",
        "close",
        "adjusted_close",
        "user-supplied",
    ):
        assert text.lower() in input_readme.lower()

    provider_modules = (
        ROOT / "src" / "broker_agents" / "data_providers"
    )
    added_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in provider_modules.glob("*.py")
    ).lower()
    for network_call in (
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "urlopen(",
    ):
        assert network_call not in added_source
