"""Tests for generalized signal consumption across Fisher, Lynch, and Bogle."""

from pathlib import Path

import yaml

from broker_agents.agents.bogle_agent import BogleAgent
from broker_agents.agents.fisher_agent import FisherAgent
from broker_agents.agents.lynch_agent import LynchAgent


ROOT = Path(__file__).resolve().parents[1]


def _load_example(filename: str) -> dict:
    return yaml.safe_load((ROOT / "examples" / filename).read_text(encoding="utf-8"))


def _report(agent_class: type, pack: dict, method: str) -> str:
    return agent_class(pack=pack, method_path=ROOT / "methods" / method).generate_report()


def test_msft_reports_use_generalized_software_cloud_signals() -> None:
    pack = _load_example("msft_input.yaml")

    fisher = _report(FisherAgent, pack, "fisher_method.yaml")
    lynch = _report(LynchAgent, pack, "lynch_method.yaml")
    bogle = _report(BogleAgent, pack, "bogle_method.yaml")

    assert "software_cloud" in fisher
    assert "Cloud" in fisher or "cloud" in fisher
    assert "Cloud/software growth story" in lynch
    assert "broad index" in bogle.lower()
    assert "concentration" in bogle.lower() or "index overlap" in bogle.lower()


def test_aapl_reports_use_generalized_consumer_ecosystem_signals() -> None:
    pack = _load_example("aapl_input.yaml")

    fisher = _report(FisherAgent, pack, "fisher_method.yaml")
    lynch = _report(LynchAgent, pack, "lynch_method.yaml")
    bogle = _report(BogleAgent, pack, "bogle_method.yaml")

    assert "consumer_ecosystem" in fisher
    assert any(term in fisher.lower() for term in ("installed base", "services", "loyalty"))
    assert "Ecosystem and services monetization story" in lynch
    assert "broad index" in bogle.lower()
    assert "concentration" in bogle.lower() or "index overlap" in bogle.lower()


def test_agents_have_no_direct_msft_or_aapl_branching() -> None:
    for filename in ("fisher_agent.py", "lynch_agent.py", "bogle_agent.py"):
        source = (ROOT / "src" / "broker_agents" / "agents" / filename).read_text(
            encoding="utf-8"
        )
        assert 'ticker == "MSFT"' not in source
        assert 'ticker == "AAPL"' not in source
        assert "if ticker ==" not in source


def test_semiconductor_pack_produces_semiconductor_wording() -> None:
    pack = {
        "metadata": {"company_name": "Chip Co", "ticker": "CHIP"},
        "company_identity": {
            "company_name": "Chip Co",
            "ticker": "CHIP",
            "industry": "Semiconductors / GPU",
        },
        "business_model": {"summary": "Designs chips and data center accelerators."},
        "financial_statements_summary": {"annual": {}},
    }

    reports = [
        _report(FisherAgent, pack, "fisher_method.yaml"),
        _report(LynchAgent, pack, "lynch_method.yaml"),
        _report(BogleAgent, pack, "bogle_method.yaml"),
    ]

    assert all("semiconductor" in report.lower() for report in reports)
    assert "cyclical" in reports[2].lower()


def test_retail_pack_produces_retail_wording() -> None:
    pack = {
        "metadata": {"company_name": "Retail Co", "ticker": "RTL"},
        "company_identity": {
            "company_name": "Retail Co",
            "ticker": "RTL",
            "industry": "Retail",
        },
        "business_model": {"summary": "Operates stores and sells consumer goods."},
        "sector_specific_operating_kpis": {"same_store_sales": 0.03},
        "financial_statements_summary": {"annual": {}},
    }

    reports = [
        _report(FisherAgent, pack, "fisher_method.yaml"),
        _report(LynchAgent, pack, "lynch_method.yaml"),
        _report(BogleAgent, pack, "bogle_method.yaml"),
    ]

    assert all("retail" in report.lower() for report in reports)
    assert "same-store sales" in reports[1]
