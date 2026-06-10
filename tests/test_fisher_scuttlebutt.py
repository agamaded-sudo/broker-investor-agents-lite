"""Tests for Fisher's business-model-specific scuttlebutt checklist."""

from pathlib import Path

import yaml

from broker_agents.agents.fisher_agent import FisherAgent
from broker_agents.calculators.fisher_scuttlebutt import (
    build_fisher_scuttlebutt_checklist,
)
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
)
from broker_agents.reports.backoffice_missing_evidence_report import (
    generate_backoffice_missing_evidence_report,
)
from broker_agents.reports.multi_company_comparison_report import (
    generate_multi_company_comparison,
)


ROOT = Path(__file__).resolve().parents[1]


def load_pack(ticker: str) -> dict:
    path = ROOT / "examples" / f"{ticker.lower()}_input.yaml"
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def checklist_text(ticker: str) -> str:
    checklist = build_fisher_scuttlebutt_checklist(load_pack(ticker))
    return " ".join(
        f"{item['evidence_area']} {item['evidence_needed']}"
        for item in checklist["checklist_items"]
    ).lower()


def test_checklists_are_business_model_specific() -> None:
    assert (
        "customer retention" in checklist_text("MSFT")
        or "developer/customer adoption" in checklist_text("MSFT")
    )
    assert (
        "installed base" in checklist_text("AAPL")
        or "customer loyalty" in checklist_text("AAPL")
    )
    assert (
        "customer concentration" in checklist_text("NVDA")
        or "demand durability" in checklist_text("NVDA")
    )


def test_fisher_reports_include_checklist_without_changing_final_decision() -> None:
    method_path = ROOT / "methods" / "fisher_method.yaml"

    for ticker in ("MSFT", "AAPL", "NVDA"):
        report = FisherAgent(load_pack(ticker), method_path).generate_report()
        eligibility = evaluate_promotion_eligibility(load_pack(ticker), "fisher")

        assert "Fisher Scuttlebutt Checklist" in report
        assert "Needs More Scuttlebutt / Watch Closely" in report
        assert eligibility["auto_promotion_allowed"] is False


def test_aggregate_reports_include_fisher_readiness_and_specific_evidence() -> None:
    comparison = generate_multi_company_comparison(
        ["MSFT", "AAPL", "NVDA"],
        ROOT / "data" / "outputs",
        ROOT / "examples",
    )
    worklist = generate_backoffice_missing_evidence_report(
        ["MSFT", "AAPL", "NVDA"],
        ROOT / "data" / "outputs",
        ROOT / "examples",
    )

    assert "Fisher Scuttlebutt Readiness Comparison" in comparison
    assert "Customer retention / churn" in worklist
    assert "Installed base evidence" in worklist
    assert "Customer concentration" in worklist
