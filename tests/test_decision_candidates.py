"""Tests for provisional investor decision candidates."""

from pathlib import Path

import yaml

from broker_agents.agents.bogle_agent import BogleAgent
from broker_agents.agents.buffett_agent import BuffettAgent
from broker_agents.agents.fisher_agent import FisherAgent
from broker_agents.agents.lynch_agent import LynchAgent
from broker_agents.agents.munger_agent import MungerAgent
from broker_agents.calculators.decision_candidates import build_decision_candidate
from broker_agents.cli import run_full_pipeline
from broker_agents.reports.multi_company_comparison_report import (
    generate_multi_company_comparison,
)


ROOT = Path(__file__).resolve().parents[1]


def _load(ticker: str) -> dict:
    path = ROOT / "examples" / f"{ticker.lower()}_input.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_buffett_candidates_reflect_preliminary_intrinsic_value_gap() -> None:
    assert build_decision_candidate(_load("AAPL"), "buffett")["candidate_decision"] == (
        "Wait Candidate"
    )
    assert build_decision_candidate(_load("MSFT"), "buffett")["candidate_decision"] == (
        "Wait Candidate"
    )
    assert build_decision_candidate(_load("NVDA"), "buffett")["candidate_decision"] == (
        "Wait Candidate"
    )


def test_nvda_munger_candidate_has_cycle_and_concentration_blockers() -> None:
    candidate = build_decision_candidate(_load("NVDA"), "munger")
    blockers = " ".join(candidate["decision_blockers"]).lower()

    assert "cycle-normalized earnings" in blockers
    assert "customer concentration" in blockers


def test_nvda_fisher_candidate_has_semiconductor_evidence_blockers() -> None:
    candidate = build_decision_candidate(_load("NVDA"), "fisher")
    blockers = " ".join(candidate["decision_blockers"]).lower()

    assert "customer concentration" in blockers
    assert "product roadmap" in blockers
    assert "demand durability" in blockers
    assert "supply constraint" in blockers


def test_bogle_candidate_requires_portfolio_context() -> None:
    candidate = build_decision_candidate(_load("MSFT"), "bogle")

    assert candidate["candidate_decision"] == "Portfolio Context Required Candidate"


def test_all_investor_reports_include_candidate_layer() -> None:
    pack = _load("MSFT")
    agent_specs = [
        (BuffettAgent, "buffett_method.yaml"),
        (MungerAgent, "munger_method.yaml"),
        (FisherAgent, "fisher_method.yaml"),
        (LynchAgent, "lynch_method.yaml"),
        (BogleAgent, "bogle_method.yaml"),
    ]

    for agent_class, method_name in agent_specs:
        report = agent_class(
            pack=pack,
            method_path=ROOT / "methods" / method_name,
        ).generate_report()
        assert "Decision Candidate Layer" in report


def test_multi_company_comparison_contains_candidate_comparison() -> None:
    report = generate_multi_company_comparison(
        ["MSFT", "AAPL", "NVDA"],
        ROOT / "data" / "outputs",
        ROOT / "examples",
    )

    assert "Decision Candidate Comparison" in report
    assert "Wait Candidate" in report
    assert "Buy Gradually Candidate" in report
    assert (
        "Wait for Better Price / Complete Intrinsic Value Work / Medium"
        in report
    )


def test_pipeline_summary_keeps_official_decisions_unchanged(tmp_path: Path) -> None:
    output_dir = tmp_path / "MSFT"
    run_full_pipeline(_load("MSFT"), output_dir)
    summary = (output_dir / "msft_agents_summary.md").read_text(encoding="utf-8")

    assert "Wait for Better Price / Complete Intrinsic Value Work" in summary
    assert "Buy Gradually / Wait for Better Evidence on AI Capex Returns" in summary
    assert "Needs More Scuttlebutt / Watch Closely" in summary
    assert "Follow / Watch" in summary
    assert "Prefer Broad Index" in summary
    assert "Decision Candidate Snapshot" in summary
