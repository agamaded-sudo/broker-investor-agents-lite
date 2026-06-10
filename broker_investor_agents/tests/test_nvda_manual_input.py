"""Tests for the manual NVIDIA semiconductor example."""

from pathlib import Path

import yaml

from broker_agents.agents.fisher_agent import FisherAgent
from broker_agents.agents.lynch_agent import LynchAgent
from broker_agents.agents.munger_agent import MungerAgent
from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.backoffice.data_validator import validate_backoffice_pack
from broker_agents.cli import run_full_pipeline


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "examples" / "nvda_input.yaml"


def _load_nvda() -> dict:
    return yaml.safe_load(INPUT_PATH.read_text(encoding="utf-8"))


def _report(agent_class: type, method_name: str) -> str:
    return agent_class(
        pack=_load_nvda(),
        method_path=ROOT / "methods" / method_name,
    ).generate_report()


def test_nvda_manual_input_validates() -> None:
    assert validate_backoffice_pack(_load_nvda()) == []


def test_nvda_is_classified_as_semiconductor() -> None:
    signals = extract_company_signals(_load_nvda())

    assert signals["business_model_type"] == "semiconductor"
    assert "semiconductor" in signals["primary_growth_engine"].lower()


def test_nvda_fisher_report_uses_semiconductor_wording() -> None:
    report = _report(FisherAgent, "fisher_method.yaml")

    assert "semiconductor" in report.lower()
    assert "customer concentration" in report.lower()
    assert "product roadmap" in report.lower()


def test_nvda_lynch_report_uses_semiconductor_cycle_wording() -> None:
    report = _report(LynchAgent, "lynch_method.yaml")

    assert "semiconductor cycle" in report.lower()
    assert "ai/data-center demand" in report.lower()


def test_nvda_munger_report_uses_semiconductor_inversion_risks() -> None:
    report = _report(MungerAgent, "munger_method.yaml")

    assert "semiconductor cycle" in report.lower()
    assert "customer concentration" in report.lower()
    assert "inventory / capacity mismatch" in report.lower()
    assert "valuation reflects peak earnings" in report.lower()


def test_nvda_pipeline_writes_all_expected_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "data" / "outputs" / "NVDA"

    results = run_full_pipeline(_load_nvda(), output_dir)
    output_names = {Path(result["output_file"]).name for result in results}

    assert output_names == {
        "nvda_backoffice_data_pack.md",
        "nvda_buffett_report.md",
        "nvda_munger_report.md",
        "nvda_fisher_report.md",
        "nvda_lynch_report.md",
        "nvda_bogle_report.md",
        "nvda_agents_summary.md",
    }
    assert all((output_dir / name).exists() for name in output_names)
