"""Tests for Munger inversion risk matrices."""

from pathlib import Path

import yaml

from broker_agents.agents.munger_agent import MungerAgent
from broker_agents.calculators.munger_inversion import build_munger_inversion_matrix
from broker_agents.reports.agents_comparison_report import generate_agents_comparison
from broker_agents.reports.backoffice_report import generate_backoffice_report


def _load_example(filename: str) -> dict:
    path = Path(__file__).resolve().parents[1] / "examples" / filename
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_msft_munger_matrix_includes_ai_infrastructure_capex() -> None:
    matrix = build_munger_inversion_matrix(_load_example("msft_input.yaml"))
    text = " ".join(row["failure_mode"] for row in matrix)

    assert "AI infrastructure capex" in text


def test_aapl_munger_matrix_includes_iphone_dependence() -> None:
    matrix = build_munger_inversion_matrix(_load_example("aapl_input.yaml"))
    text = " ".join(row["failure_mode"] for row in matrix)

    assert "product dependence" in text.lower()


def test_munger_report_contains_inversion_risk_matrix() -> None:
    pack = _load_example("msft_input.yaml")
    method_path = Path(__file__).resolve().parents[1] / "methods" / "munger_method.yaml"

    report = MungerAgent(pack=pack, method_path=method_path).generate_report()

    assert "Munger Inversion Risk Matrix" in report


def test_munger_inversion_has_no_ticker_specific_branching() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "broker_agents"
        / "calculators"
        / "munger_inversion.py"
    )
    source = source_path.read_text(encoding="utf-8")

    assert 'ticker == "MSFT"' not in source
    assert 'ticker == "AAPL"' not in source


def test_semiconductor_pack_uses_semiconductor_inversion_risks() -> None:
    pack = {
        "company_identity": {"industry": "Semiconductors / GPU"},
        "business_model": {"summary": "Designs chips and data center accelerators."},
    }

    matrix = build_munger_inversion_matrix(pack)

    assert any("Semiconductor cycle" in row["failure_mode"] for row in matrix)


def test_retail_pack_uses_retail_inversion_risks() -> None:
    pack = {
        "company_identity": {"industry": "Retail"},
        "sector_specific_operating_kpis": {"same_store_sales": 0.03},
    }

    matrix = build_munger_inversion_matrix(pack)

    assert any("Same-store sales" in row["failure_mode"] for row in matrix)


def test_comparison_contains_munger_inversion_risk_comparison(tmp_path: Path) -> None:
    left_dir = tmp_path / "MSFT"
    right_dir = tmp_path / "AAPL"
    left_dir.mkdir()
    right_dir.mkdir()
    left_summary = left_dir / "msft_agents_summary.md"
    right_summary = right_dir / "aapl_agents_summary.md"
    summary_table = """| Investor | Decision | Confidence | Report File |
| --- | --- | --- | --- |
| Warren Buffett | Wait for Better Price / Complete Intrinsic Value Work | Medium | report.md |
| Charlie Munger | Buy Gradually / Wait for Better Evidence on AI Capex Returns | Medium | report.md |
| Philip Fisher | Needs More Scuttlebutt / Watch Closely | Medium | report.md |
| Peter Lynch | Follow / Watch | Medium | report.md |
| John Bogle | Prefer Broad Index | Medium | report.md |
"""
    left_summary.write_text(summary_table, encoding="utf-8")
    right_summary.write_text(summary_table, encoding="utf-8")
    for directory, ticker, pack_file in [
        (left_dir, "msft", "msft_input.yaml"),
        (right_dir, "aapl", "aapl_input.yaml"),
    ]:
        pack = _load_example(pack_file)
        (directory / f"{ticker}_backoffice_data_pack.md").write_text(
            generate_backoffice_report(pack),
            encoding="utf-8",
        )
        method_path = Path(__file__).resolve().parents[1] / "methods" / "munger_method.yaml"
        (directory / f"{ticker}_munger_report.md").write_text(
            MungerAgent(pack=pack, method_path=method_path).generate_report(),
            encoding="utf-8",
        )

    comparison = generate_agents_comparison("MSFT", "AAPL", left_summary, right_summary)

    assert "Munger Inversion Risk Comparison" in comparison
