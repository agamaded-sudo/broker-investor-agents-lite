"""End-to-end coverage for the Costco retail and membership example."""

from pathlib import Path

import yaml

from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.backoffice.data_validator import validate_backoffice_pack
from broker_agents.backoffice.enrichment_pipeline import (
    fixture_paths_for_known_ticker,
    run_backoffice_enrichment_pipeline,
)
from broker_agents.calculators.decision_candidates import CURRENT_DECISIONS
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
)
from broker_agents.deals.broker_deal_workflow import run_broker_deal_workflow
from broker_agents.deals.deal_intake import build_deal_intake_status
from broker_agents.fetchers.growth_peg_fetcher import (
    GrowthPegFetcher,
    load_growth_peg_fixture,
)
from broker_agents.fetchers.historical_valuation_fetcher import (
    HistoricalValuationFetcher,
    load_historical_valuation_fixture,
)
from broker_agents.fetchers.market_data_fetcher import (
    MarketDataFetcher,
    load_market_data_fixture,
)
from broker_agents.fetchers.sec_financials_fetcher import (
    SecFinancialsFetcher,
    load_sec_fixture,
    map_fixture_to_financials,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
PORTFOLIO_CONTEXT = EXAMPLES / "portfolio_context.yaml"
COST_INPUT = EXAMPLES / "cost_input.yaml"


def _load_cost_pack() -> dict:
    return yaml.safe_load(COST_INPUT.read_text(encoding="utf-8"))


def test_cost_manual_pack_validates_and_detects_retail_membership_model() -> None:
    assert COST_INPUT.exists()
    pack = _load_cost_pack()
    signals = extract_company_signals(pack)

    assert validate_backoffice_pack(pack) == []
    assert signals["business_model_type"] in {"retail", "retail_membership"}
    assert "membership" in signals["primary_growth_engine"].lower()
    assert "membership" in signals["dominant_revenue_stream"].lower()


def test_cost_identity_and_all_fixtures_map() -> None:
    identity = SecFinancialsFetcher().resolve_company_identity("COST")
    sec = map_fixture_to_financials(
        load_sec_fixture(FIXTURES / "sec_company_facts_cost.json")
    )
    market = MarketDataFetcher().map_fixture_to_market_data(
        load_market_data_fixture(FIXTURES / "market_data_cost.json")
    )
    history = HistoricalValuationFetcher().map_fixture_to_historical_valuation(
        load_historical_valuation_fixture(
            FIXTURES / "historical_valuation_cost.json"
        )
    )
    growth = GrowthPegFetcher().map_fixture_to_growth_peg(
        load_growth_peg_fixture(FIXTURES / "growth_peg_cost.json")
    )

    assert identity.cik == "0000909832"
    assert sec.free_cash_flow == 6700
    assert market.p_fcf == 61.2
    assert history.p_fcf_5y_median == 42
    assert growth.peg_ratio == 6.22


def test_cost_intake_is_ready_and_enrichment_applies_all_sources(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    intake = build_deal_intake_status(
        ticker="COST",
        examples_root=EXAMPLES,
        outputs_root=outputs_root,
        fixtures_root=FIXTURES,
        portfolio_context_path=PORTFOLIO_CONTEXT,
    )
    enriched_path = outputs_root / "COST" / "cost_enriched_input.yaml"
    enrichment = run_backoffice_enrichment_pipeline(
        COST_INPUT,
        enriched_path,
        **fixture_paths_for_known_ticker("COST", FIXTURES),
    )

    assert intake.intake_status == "Ready for Deal Workflow"
    assert intake.can_run_deal is True
    assert enriched_path.exists()
    assert enrichment.applied_sources == [
        "official_financials",
        "market_data",
        "historical_valuation",
        "growth_peg",
    ]


def test_cost_broker_deal_workflow_creates_package_and_five_letters(
    tmp_path: Path,
) -> None:
    result = run_broker_deal_workflow(
        ticker="COST",
        input_pack_path=COST_INPUT,
        outputs_root=tmp_path / "outputs",
        fixtures_root=FIXTURES,
        portfolio_context_path=PORTFOLIO_CONTEXT,
    )
    package = result.broker_deal_package_path.read_text(encoding="utf-8")

    assert result.enriched_pack_path.exists()
    assert result.investor_summary_path.exists()
    assert len(result.investor_reports) == 5
    assert len(result.investor_response_letter_paths) == 5
    assert all(path.exists() for path in result.investor_response_letter_paths.values())
    for heading in (
        "Broker Deal Package - COST",
        "Executive Summary for Broker",
        "Independent Investor Responses",
        "Investor Response Letters",
        "Safety Check",
    ):
        assert heading in package
    assert "No recommendation" in package
    assert "No ranking" in package
    assert "No consensus" in package
    assert "No portfolio allocation" in package
    assert "No trade signal" in package
    assert "Auto-promotion disabled" in package


def test_existing_final_decisions_and_auto_promotion_remain_unchanged() -> None:
    assert CURRENT_DECISIONS == {
        "buffett": "Wait for Better Price / Complete Intrinsic Value Work",
        "munger": "Buy Gradually / Wait for Better Evidence on AI Capex Returns",
        "fisher": "Needs More Scuttlebutt / Watch Closely",
        "lynch": "Follow / Watch",
        "bogle": "Prefer Broad Index",
    }
    pack = _load_cost_pack()
    for investor in CURRENT_DECISIONS:
        eligibility = evaluate_promotion_eligibility(pack, investor)
        assert eligibility["auto_promotion_allowed"] is False
