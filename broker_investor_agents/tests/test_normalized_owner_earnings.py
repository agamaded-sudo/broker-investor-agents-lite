"""Tests for deterministic normalized owner-earnings evidence."""

from pathlib import Path

import yaml

from broker_agents.agents.buffett_agent import BuffettAgent
from broker_agents.calculators.normalized_owner_earnings import (
    calculate_normalized_owner_earnings,
)


ROOT = Path(__file__).resolve().parents[1]


def load_pack(ticker: str) -> dict:
    path = ROOT / "examples" / f"{ticker.lower()}_input.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_normalized_owner_earnings_returns_values_for_manual_companies() -> None:
    for ticker in ("MSFT", "AAPL", "NVDA"):
        result = calculate_normalized_owner_earnings(load_pack(ticker))

        assert result["latest_owner_earnings"] is not None
        assert result["normalized_owner_earnings"] is not None
        assert result["fcf_history_available_years"] == 1
        assert result["normalized_fcf_margin"] is not None


def test_company_confidence_and_durability_remain_conservative() -> None:
    msft = calculate_normalized_owner_earnings(load_pack("MSFT"))
    aapl = calculate_normalized_owner_earnings(load_pack("AAPL"))
    nvda = calculate_normalized_owner_earnings(load_pack("NVDA"))

    assert msft["normalized_owner_earnings_confidence"] == "Low"
    assert aapl["normalized_owner_earnings_confidence"] == "Medium"
    assert nvda["normalized_owner_earnings_confidence"] == "Low"
    assert nvda["owner_earnings_durability_label"] == (
        "cycle-sensitive / needs normalization"
    )


def test_buffett_reports_include_normalized_owner_earnings_evidence() -> None:
    method_path = ROOT / "methods" / "buffett_method.yaml"
    for ticker in ("MSFT", "AAPL", "NVDA"):
        report = BuffettAgent(load_pack(ticker), method_path).generate_report()
        assert "Normalized Owner Earnings Evidence" in report
