"""End-to-end tests for investor-specific broker follow-up memos."""

import json
from pathlib import Path

import pytest

from broker_agents.deals.broker_deal_workflow import (
    BrokerDealWorkflowResult,
    run_broker_deal_workflow,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
PORTFOLIO_CONTEXT = EXAMPLES / "portfolio_context.yaml"
EXPECTED_FILES = {
    "Buffett": "cost_buffett_follow_up_memo.md",
    "Munger": "cost_munger_follow_up_memo.md",
    "Fisher": "cost_fisher_follow_up_memo.md",
    "Lynch": "cost_lynch_follow_up_memo.md",
    "Bogle": "cost_bogle_follow_up_memo.md",
}
EXPECTED_DECISIONS = (
    "Wait for Better Price / Complete Intrinsic Value Work",
    "Buy Gradually / Wait for Better Evidence on Incentives and Long-Term Durability",
    "Needs More Scuttlebutt / Watch Closely",
    "Follow / Watch",
    "Prefer Broad Index",
)


@pytest.fixture
def cost_deal(tmp_path: Path) -> BrokerDealWorkflowResult:
    """Generate one isolated COST deal package for memo assertions."""
    return run_broker_deal_workflow(
        ticker="COST",
        input_pack_path=EXAMPLES / "cost_input.yaml",
        outputs_root=tmp_path / "outputs",
        fixtures_root=FIXTURES,
        portfolio_context_path=PORTFOLIO_CONTEXT,
    )


def test_cost_follow_up_memos_are_generated_and_linked(
    cost_deal: BrokerDealWorkflowResult,
) -> None:
    assert set(cost_deal.investor_follow_up_memo_paths) == set(EXPECTED_FILES)
    for investor, filename in EXPECTED_FILES.items():
        path = cost_deal.investor_follow_up_memo_paths[investor]
        assert path.name == filename
        assert path.parent.name == "investor_follow_up_memos"
        assert path.exists()

    package = cost_deal.broker_deal_package_path.read_text(encoding="utf-8")
    assert "Investor Follow-Up Memos" in package
    for filename in EXPECTED_FILES.values():
        assert filename in package
    for decision in EXPECTED_DECISIONS:
        assert decision in package

    payload_path = (
        cost_deal.deal_output_dir / "cost_broker_deal_package.json"
    )
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    assert set(
        payload["workflow_result"]["investor_follow_up_memo_paths"]
    ) == set(EXPECTED_FILES)


def test_cost_follow_up_memos_contain_investor_specific_evidence(
    cost_deal: BrokerDealWorkflowResult,
) -> None:
    memos = {
        investor: path.read_text(encoding="utf-8").lower()
        for investor, path in cost_deal.investor_follow_up_memo_paths.items()
    }

    assert any(
        term in memos["Buffett"]
        for term in (
            "owner earnings",
            "margin of safety",
            "valuation history",
            "intrinsic value",
        )
    )
    assert any(
        term in memos["Munger"]
        for term in (
            "management incentives",
            "compensation",
            "ownership",
            "capital allocation",
        )
    )
    fisher_terms = (
        "customer traffic",
        "repeat purchase",
        "loyalty",
        "same-store sales",
        "store economics",
        "inventory discipline",
        "employee culture",
        "supplier relationships",
    )
    assert "scuttlebutt" in memos["Fisher"]
    assert sum(term in memos["Fisher"] for term in fisher_terms) >= 3
    assert any(
        term in memos["Lynch"]
        for term in (
            "peg",
            "growth methodology",
            "category classification",
            "comparable sales",
        )
    )
    assert any(
        term in memos["Bogle"]
        for term in (
            "index overlap",
            "etf holdings",
            "benchmark-relative",
            "broad index exposure",
        )
    )


def test_follow_up_memo_safety_boundaries_and_demo_runner_remain(
    cost_deal: BrokerDealWorkflowResult,
) -> None:
    for path in cost_deal.investor_follow_up_memo_paths.values():
        memo = path.read_text(encoding="utf-8").lower()
        for boundary in (
            "not a recommendation",
            "ranking",
            "vote",
            "consensus",
            "allocation instruction",
            "trade signal",
        ):
            assert boundary in memo

    package = cost_deal.broker_deal_package_path.read_text(encoding="utf-8")
    assert "Auto-promotion disabled." in package
    for decision in EXPECTED_DECISIONS:
        assert decision in package

    demo_script = (ROOT / "scripts" / "run_first_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "python -m ruff check ." in demo_script
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in demo_script
    assert "python -m broker_agents.cli deal-intakes" in demo_script
    assert "python -m broker_agents.cli run-deals" in demo_script
