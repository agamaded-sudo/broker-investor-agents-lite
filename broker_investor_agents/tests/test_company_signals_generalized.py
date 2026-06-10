"""Tests for generalized business-model-driven company signals."""

from pathlib import Path

import yaml

from broker_agents.backoffice.company_signals import extract_company_signals


def _load_example(filename: str) -> dict:
    path = Path(__file__).resolve().parents[1] / "examples" / filename
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_msft_is_classified_as_software_cloud() -> None:
    signals = extract_company_signals(_load_example("msft_input.yaml"))

    assert signals["business_model_type"] == "software_cloud"
    assert "Cloud" in signals["primary_growth_engine"] or "AI" in signals["primary_growth_engine"]


def test_aapl_is_classified_as_consumer_ecosystem() -> None:
    signals = extract_company_signals(_load_example("aapl_input.yaml"))

    assert signals["business_model_type"] == "consumer_ecosystem"
    assert "iPhone" in signals["primary_growth_engine"] or "services" in signals[
        "primary_growth_engine"
    ].lower()


def test_unknown_pack_is_generic() -> None:
    pack = {
        "company_identity": {
            "company_name": "Unknown Co",
            "ticker": "UNK",
            "sector": "Other",
            "industry": "Other",
        },
        "business_model": {"summary": "A business with limited classification details."},
    }

    assert extract_company_signals(pack)["business_model_type"] == "generic"


def test_semiconductor_like_pack_is_classified_as_semiconductor() -> None:
    pack = {
        "company_identity": {"industry": "Semiconductors / GPU"},
        "business_model": {"summary": "Designs chips and data center accelerators."},
    }

    assert extract_company_signals(pack)["business_model_type"] == "semiconductor"


def test_retail_like_pack_is_classified_as_retail() -> None:
    pack = {
        "company_identity": {"industry": "Retail"},
        "sector_specific_operating_kpis": {
            "store_count": 100,
            "same_store_sales": 0.04,
        },
    }

    assert extract_company_signals(pack)["business_model_type"] == "retail"


def test_industrial_like_pack_is_classified_as_industrial() -> None:
    pack = {
        "company_identity": {"industry": "Industrial Machinery"},
        "sector_specific_operating_kpis": {
            "backlog": 1000,
            "capacity_utilization": 0.85,
        },
    }

    assert extract_company_signals(pack)["business_model_type"] == "industrial"
