"""Company-specific broker response language regression tests."""

from pathlib import Path

from broker_agents.deals.broker_deal_workflow import run_broker_deal_workflow

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
PORTFOLIO_CONTEXT = EXAMPLES / "portfolio_context.yaml"


def test_cost_response_letters_use_company_specific_language(
    tmp_path: Path,
) -> None:
    result = run_broker_deal_workflow(
        ticker="COST",
        input_pack_path=EXAMPLES / "cost_input.yaml",
        outputs_root=tmp_path / "outputs",
        fixtures_root=FIXTURES,
        portfolio_context_path=PORTFOLIO_CONTEXT,
    )
    letters = {
        investor: path.read_text(encoding="utf-8")
        for investor, path in result.investor_response_letter_paths.items()
    }

    assert "AI Capex Returns" not in letters["Munger"]
    assert "Incentives and Long-Term Durability" in letters["Munger"]

    buffett = letters["Buffett"]
    assert "Detected business model: retail." not in buffett
    assert "Membership economics" in buffett
    assert "customer loyalty" in buffett
    assert "pricing discipline" in buffett
    assert "durable retail franchise" in buffett

    fisher = letters["Fisher"]
    assert "Traffic and visit-frequency evidence" in fisher
    assert "Repeat purchase, membership, and loyalty evidence" in fisher
    assert "Comparable-store sales history and drivers" in fisher

    bogle = letters["Bogle"]
    assert "index and ETF overlap" in bogle
    assert "broad-index exposure" in bogle


def test_cost_package_uses_polished_response_details(tmp_path: Path) -> None:
    result = run_broker_deal_workflow(
        ticker="COST",
        input_pack_path=EXAMPLES / "cost_input.yaml",
        outputs_root=tmp_path / "outputs",
        fixtures_root=FIXTURES,
        portfolio_context_path=PORTFOLIO_CONTEXT,
    )
    package = result.broker_deal_package_path.read_text(encoding="utf-8")

    assert "AI Capex Returns" not in package
    assert "Membership economics" in package
    assert "Company-Specific Follow-Up" in package
    assert "PEG ratio of 6.22" in package
    assert "consumer/retail ETFs" in package


def test_cost_letters_contain_no_comparative_or_transaction_instruction(
    tmp_path: Path,
) -> None:
    result = run_broker_deal_workflow(
        ticker="COST",
        input_pack_path=EXAMPLES / "cost_input.yaml",
        outputs_root=tmp_path / "outputs",
        fixtures_root=FIXTURES,
        portfolio_context_path=PORTFOLIO_CONTEXT,
    )
    forbidden = (
        "ranking",
        "vote",
        "consensus",
        "allocation instruction",
        "rebalancing instruction",
        "trade signal",
    )
    for path in result.investor_response_letter_paths.values():
        letter = path.read_text(encoding="utf-8").lower()
        assert all(term not in letter for term in forbidden)
