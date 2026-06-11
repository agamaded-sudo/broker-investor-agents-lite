"""End-to-end tests for consolidated Backoffice work orders."""

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
EXPECTED_DECISIONS = (
    "Wait for Better Price / Complete Intrinsic Value Work",
    "Buy Gradually / Wait for Better Evidence on Incentives and Long-Term Durability",
    "Needs More Scuttlebutt / Watch Closely",
    "Follow / Watch",
    "Prefer Broad Index",
)
INVESTORS = ("Buffett", "Munger", "Fisher", "Lynch", "Bogle")
CATEGORIES = (
    "official_financials",
    "market_data",
    "historical_valuation",
    "growth_peg",
    "scuttlebutt",
    "management_incentives",
    "index_overlap",
)
BLOCKING_CATEGORIES = (
    "scuttlebutt",
    "management_incentives",
    "index_overlap",
)


@pytest.fixture
def cost_deal(tmp_path: Path) -> BrokerDealWorkflowResult:
    """Generate an isolated COST package and work-order plan."""
    return run_broker_deal_workflow(
        ticker="COST",
        input_pack_path=EXAMPLES / "cost_input.yaml",
        outputs_root=tmp_path / "outputs",
        fixtures_root=FIXTURES,
        portfolio_context_path=PORTFOLIO_CONTEXT,
    )


def test_cost_backoffice_work_orders_are_generated_and_linked(
    cost_deal: BrokerDealWorkflowResult,
) -> None:
    work_orders_path = cost_deal.backoffice_work_orders_path
    assert work_orders_path.exists()
    assert work_orders_path.name == "cost_backoffice_work_orders.md"
    assert work_orders_path.parent.name == "backoffice_work_orders"

    package = cost_deal.broker_deal_package_path.read_text(encoding="utf-8")
    assert "Backoffice Work Orders" in package
    assert "cost_backoffice_work_orders.md" in package
    assert "Total Work Orders" in package
    assert "High Priority Count" in package
    assert "Promotion-Blocking Count" in package
    for decision in EXPECTED_DECISIONS:
        assert decision in package

    payload_path = (
        cost_deal.deal_output_dir / "cost_broker_deal_package.json"
    )
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    assert (
        payload["workflow_result"]["backoffice_work_orders_path"]
        == str(work_orders_path)
    )
    assert payload["backoffice_work_order_plan"]["total_work_orders"] > 0


def test_cost_work_orders_cover_investors_categories_and_blockers(
    cost_deal: BrokerDealWorkflowResult,
) -> None:
    report = cost_deal.backoffice_work_orders_path.read_text(encoding="utf-8")

    for heading in (
        "Work Orders Table",
        "Investor Coverage Map",
        "Category Coverage Map",
        "Promotion-Blocking Work Orders",
        "Backoffice Execution Sequence",
    ):
        assert heading in report
    for investor in INVESTORS:
        assert investor in report
    for category in CATEGORIES:
        assert category in report
    for category in BLOCKING_CATEGORIES:
        assert category in report
        assert any(
            category in line and "| Yes |" in line
            for line in report.splitlines()
        )


def test_work_order_and_package_safety_and_demo_runner_remain(
    cost_deal: BrokerDealWorkflowResult,
) -> None:
    work_orders = cost_deal.backoffice_work_orders_path.read_text(
        encoding="utf-8"
    ).lower()
    package = cost_deal.broker_deal_package_path.read_text(
        encoding="utf-8"
    ).lower()
    for boundary in (
        "not a recommendation",
        "ranking",
        "vote",
        "consensus",
        "allocation instruction",
        "trade signal",
    ):
        assert boundary in work_orders
        assert boundary in package
    assert "auto-promotion disabled" in package

    demo_script = (ROOT / "scripts" / "run_first_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "python -m ruff check ." in demo_script
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in demo_script
    assert "python -m broker_agents.cli deal-intakes" in demo_script
    assert "python -m broker_agents.cli run-deals" in demo_script
