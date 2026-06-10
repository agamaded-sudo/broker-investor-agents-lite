"""Tests for deterministic company signal extraction."""

from pathlib import Path

import yaml

from broker_agents.agents.buffett_agent import BuffettAgent
from broker_agents.backoffice.company_signals import extract_company_signals


def _load_example(filename: str) -> dict:
    path = Path(__file__).resolve().parents[1] / "examples" / filename
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_msft_signal_extraction_includes_cloud() -> None:
    signals = extract_company_signals(_load_example("msft_input.yaml"))

    assert "Cloud" in signals["primary_growth_engine"]


def test_aapl_signal_extraction_includes_iphone() -> None:
    signals = extract_company_signals(_load_example("aapl_input.yaml"))

    assert "iPhone" in signals["primary_growth_engine"]


def test_investor_report_includes_company_specific_signal() -> None:
    pack = _load_example("msft_input.yaml")
    method_path = Path(__file__).resolve().parents[1] / "methods" / "buffett_method.yaml"

    report = BuffettAgent(pack=pack, method_path=method_path).generate_report()

    assert "Company-Specific Signal" in report


def test_msft_buffett_report_contains_company_specific_decision_rationale() -> None:
    pack = _load_example("msft_input.yaml")
    method_path = Path(__file__).resolve().parents[1] / "methods" / "buffett_method.yaml"

    report = BuffettAgent(pack=pack, method_path=method_path).generate_report()

    assert "Decision Rationale" in report
    assert "AI/data-center capex" in report or "AI" in report


def test_aapl_buffett_report_contains_company_specific_decision_rationale() -> None:
    pack = _load_example("aapl_input.yaml")
    method_path = Path(__file__).resolve().parents[1] / "methods" / "buffett_method.yaml"

    report = BuffettAgent(pack=pack, method_path=method_path).generate_report()

    assert "Decision Rationale" in report
    assert "lower capex intensity" in report or "cash generation" in report
