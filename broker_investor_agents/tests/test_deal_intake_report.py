"""Tests for deal intake reporting and CLI output."""

import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.deals.deal_intake import build_deal_intake_status
from broker_agents.reports.deal_intake_report import generate_deal_intake_report

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
PORTFOLIO_CONTEXT = EXAMPLES / "portfolio_context.yaml"


def test_deal_intake_report_contains_required_sections(tmp_path: Path) -> None:
    status = build_deal_intake_status(
        ticker="MSFT",
        examples_root=EXAMPLES,
        outputs_root=tmp_path / "outputs",
        fixtures_root=FIXTURES,
        portfolio_context_path=PORTFOLIO_CONTEXT,
    )
    report = generate_deal_intake_report(status)

    for heading in (
        "Deal Intake Report",
        "Intake Summary",
        "Required Files",
        "Missing Requirements",
        "Optional Missing Sources",
        "Backoffice Next Actions",
        "Safety Check",
    ):
        assert heading in report
    assert "not a recommendation" in report
    assert "No ranking" in report
    assert "No consensus" in report
    assert "No allocation" in report
    assert "No trade signal" in report
    assert "Auto-promotion disabled" in report


def test_deal_intake_cli_writes_markdown_and_json(tmp_path: Path) -> None:
    output = tmp_path / "msft_intake.md"
    json_output = tmp_path / "msft_intake.json"
    result = CliRunner().invoke(
        app,
        [
            "deal-intake",
            "--ticker",
            "MSFT",
            "--examples-root",
            str(EXAMPLES),
            "--outputs-root",
            str(tmp_path / "outputs"),
            "--fixtures-root",
            str(FIXTURES),
            "--portfolio-context",
            str(PORTFOLIO_CONTEXT),
            "--market",
            "US",
            "--company-name",
            "Microsoft Corporation",
            "--output",
            str(output),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output.exists()
    payload = json.loads(json_output.read_text(encoding="utf-8"))
    assert payload["intake_status"] == "Ready for Deal Workflow"
    assert payload["can_run_deal"] is True
    assert "no_auto_promotion" in payload["safety_flags"]


def test_deal_intakes_cli_writes_known_tickers_without_running_agents(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    result = CliRunner().invoke(
        app,
        [
            "deal-intakes",
            "--tickers",
            "MSFT,AAPL,NVDA",
            "--examples-root",
            str(EXAMPLES),
            "--outputs-root",
            str(outputs_root),
            "--fixtures-root",
            str(FIXTURES),
            "--portfolio-context",
            str(PORTFOLIO_CONTEXT),
        ],
    )

    assert result.exit_code == 0, result.output
    for ticker in ("MSFT", "AAPL", "NVDA"):
        report_path = outputs_root / ticker / "deal_intake_report.md"
        json_path = outputs_root / ticker / "deal_intake_report.json"
        assert report_path.exists()
        assert json_path.exists()
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert payload["intake_status"] == "Ready for Deal Workflow"
        assert not (outputs_root / ticker / "deal_package").exists()
        assert not list((outputs_root / ticker).glob("*_agents_summary.md"))
