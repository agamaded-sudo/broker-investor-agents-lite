"""Tests for filesystem-based broker deal intake readiness."""

from pathlib import Path

from broker_agents.deals.deal_intake import build_deal_intake_status

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
PORTFOLIO_CONTEXT = EXAMPLES / "portfolio_context.yaml"


def test_msft_is_ready_for_deal_workflow(tmp_path: Path) -> None:
    status = build_deal_intake_status(
        ticker="msft",
        examples_root=EXAMPLES,
        outputs_root=tmp_path / "outputs",
        fixtures_root=FIXTURES,
        portfolio_context_path=PORTFOLIO_CONTEXT,
    )

    assert status.normalized_ticker == "MSFT"
    assert status.intake_status == "Ready for Deal Workflow"
    assert status.can_run_deal is True
    assert status.manual_input_exists is True
    assert status.sec_fixture_exists is True
    assert status.market_fixture_exists is True
    assert status.historical_valuation_fixture_exists is True
    assert status.growth_peg_fixture_exists is True
    assert status.company_name == "Microsoft Corporation"


def test_missing_manual_pack_blocks_deal_workflow(tmp_path: Path) -> None:
    status = build_deal_intake_status(
        ticker="NEW",
        examples_root=EXAMPLES,
        outputs_root=tmp_path / "outputs",
        fixtures_root=FIXTURES,
    )

    assert status.intake_status == "Manual Pack Required"
    assert status.can_run_deal is False
    assert any("Manual Backoffice input pack" in item for item in status.missing_requirements)
    assert any(
        "Create manual Backoffice input pack" in action
        for action in status.backoffice_next_actions
    )


def test_missing_fixtures_are_optional_when_manual_pack_exists(
    tmp_path: Path,
) -> None:
    examples = tmp_path / "examples"
    fixtures = tmp_path / "fixtures"
    examples.mkdir()
    fixtures.mkdir()
    (examples / "test_input.yaml").write_text(
        "company_identity:\n"
        "  ticker: TEST\n"
        "  company_name: Test Company\n"
        "  market: USA\n",
        encoding="utf-8",
    )

    status = build_deal_intake_status(
        ticker="TEST",
        examples_root=examples,
        outputs_root=tmp_path / "outputs",
        fixtures_root=fixtures,
    )

    assert status.intake_status == "Ready with Missing Optional Sources"
    assert status.can_run_deal is True
    assert len(status.optional_missing_sources) == 4


def test_invalid_ticker_is_insufficient_for_deal_workflow(tmp_path: Path) -> None:
    status = build_deal_intake_status(
        ticker="",
        examples_root=EXAMPLES,
        outputs_root=tmp_path / "outputs",
        fixtures_root=FIXTURES,
    )

    assert status.intake_status == "Insufficient for Deal Workflow"
    assert status.can_run_deal is False
    assert status.normalized_ticker == ""


def test_deal_intake_always_includes_governance_flags(tmp_path: Path) -> None:
    status = build_deal_intake_status(
        ticker="MSFT",
        examples_root=EXAMPLES,
        outputs_root=tmp_path / "outputs",
        fixtures_root=FIXTURES,
    )

    assert set(status.safety_flags) == {
        "intake_only",
        "no_recommendation",
        "no_investor_decision",
        "no_ranking",
        "no_consensus",
        "no_allocation",
        "no_trade_signal",
        "no_auto_promotion",
    }
    assert (EXAMPLES / "deal_intake_template.yaml").exists()
