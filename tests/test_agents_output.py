"""Tests for investor agent output contracts."""

from pathlib import Path

import yaml

from broker_agents.agents.bogle_agent import BogleAgent
from broker_agents.agents.buffett_agent import BuffettAgent
from broker_agents.agents.fisher_agent import FisherAgent
from broker_agents.agents.lynch_agent import LynchAgent
from broker_agents.agents.munger_agent import MungerAgent
from broker_agents.cli import run_all_agent_reports, run_full_pipeline
from broker_agents.storage.file_paths import output_dir_for_ticker


def test_buffett_agent_generate_report_contains_required_terms() -> None:
    pack = {
        "metadata": {"company_name": "Microsoft Corporation", "ticker": "MSFT"},
        "company_identity": {
            "company_name": "Microsoft Corporation",
            "ticker": "MSFT",
            "exchange": "NASDAQ",
            "market": "USA",
            "currency": "USD",
        },
        "business_model": {"business_summary": "Software, cloud, and AI infrastructure."},
        "financial_statements_summary": {
            "annual": {
                "revenue": 281700,
                "operating_income": 128500,
                "net_income": 101800,
                "operating_cash_flow": 136200,
                "capex": 64600,
                "free_cash_flow": 71600,
            }
        },
        "calculated_financial_metrics": {},
        "capex_owner_earnings_proxy": {
            "capex": 64600,
            "free_cash_flow": 71600,
            "caveat": "Maintenance versus growth capex is not disclosed.",
        },
        "historical_valuation": {"current_snapshot_only": True},
        "sources_confidence_data_gaps": {
            "known_gaps": [
                "Historical valuation ranges missing.",
                "Maintenance vs growth capex not disclosed.",
            ]
        },
    }
    method_path = Path(__file__).resolve().parents[1] / "methods" / "buffett_method.yaml"

    report = BuffettAgent(pack=pack, method_path=method_path).generate_report()

    assert "Warren Buffett" in report
    assert "Microsoft Corporation" in report
    assert "MSFT" in report
    assert "Decision" in report
    assert "Margin of Safety" in report
    assert "Data Quality Rating" in report
    assert "Evidence Map" in report
    assert "Business Model Type" in report
    assert "Capex Profile" in report


def test_munger_agent_generate_report_contains_required_terms() -> None:
    pack = {
        "metadata": {"company_name": "Microsoft Corporation", "ticker": "MSFT"},
        "company_identity": {
            "company_name": "Microsoft Corporation",
            "ticker": "MSFT",
            "exchange": "NASDAQ",
            "market": "USA",
            "currency": "USD",
        },
        "business_model": {"business_summary": "Software, cloud, and AI infrastructure."},
        "financial_statements_summary": {
            "annual": {
                "revenue": 281700,
                "operating_income": 128500,
                "net_income": 101800,
                "operating_cash_flow": 136200,
                "capex": 64600,
                "free_cash_flow": 71600,
            }
        },
        "calculated_financial_metrics": {"free_cash_flow_margin": 0.254},
        "capex_owner_earnings_proxy": {
            "capex": 64600,
            "caveat": "Maintenance versus growth capex is not disclosed.",
        },
        "historical_valuation": {"current_snapshot_only": True},
        "peer_comparison": {"status": "incomplete"},
        "sector_specific_operating_kpis": {
            "software": {"retention_churn": "unavailable"},
            "cloud": {},
        },
        "sources_confidence_data_gaps": {
            "known_gaps": [
                "Historical valuation ranges missing.",
                "Management compensation details missing.",
            ]
        },
    }
    method_path = Path(__file__).resolve().parents[1] / "methods" / "munger_method.yaml"

    report = MungerAgent(pack=pack, method_path=method_path).generate_report()

    assert "Charlie Munger" in report
    assert "Microsoft Corporation" in report
    assert "Inversion Analysis" in report
    assert "Hidden Stupidity Risk" in report
    assert "Decision" in report


def test_fisher_agent_generate_report_contains_required_terms() -> None:
    pack = {
        "metadata": {"company_name": "Microsoft Corporation", "ticker": "MSFT"},
        "company_identity": {
            "company_name": "Microsoft Corporation",
            "ticker": "MSFT",
            "exchange": "NASDAQ",
            "market": "USA",
            "currency": "USD",
        },
        "business_model": {"summary": "Microsoft 365, Azure, GitHub, LinkedIn, and Dynamics."},
        "products_customers_revenue_segments": {
            "segments": [
                {"name": "Intelligent Cloud", "examples": ["Azure"]},
                {"name": "Productivity", "examples": ["Microsoft 365", "LinkedIn"]},
            ]
        },
        "financial_statements_summary": {
            "quarterly": {
                "microsoft_cloud_revenue": 54500,
                "microsoft_cloud_growth": 0.29,
                "azure_and_other_cloud_services_growth": 0.40,
            }
        },
        "growth_drivers": {"drivers": ["AI infrastructure and Copilot adoption."]},
        "sector_specific_operating_kpis": {
            "cloud": {
                "microsoft_cloud_revenue_q3_fy26": 54500,
                "microsoft_cloud_growth_q3_fy26": 0.29,
            },
            "software": {"retention_churn": "unavailable"},
        },
        "peer_comparison": {"status": "incomplete"},
        "scuttlebutt": {"status": "weak_unavailable"},
        "valuation_snapshot": {"status": "market_data_placeholder"},
    }
    method_path = Path(__file__).resolve().parents[1] / "methods" / "fisher_method.yaml"

    report = FisherAgent(pack=pack, method_path=method_path).generate_report()

    assert "Philip Fisher" in report
    assert "Microsoft Corporation" in report
    assert "Scuttlebutt" in report
    assert "Needs More Scuttlebutt" in report
    assert "Decision" in report


def test_lynch_agent_generate_report_contains_required_terms() -> None:
    pack = {
        "metadata": {"company_name": "Microsoft Corporation", "ticker": "MSFT"},
        "company_identity": {
            "company_name": "Microsoft Corporation",
            "ticker": "MSFT",
            "exchange": "NASDAQ",
            "market": "USA",
            "currency": "USD",
        },
        "financial_statements_summary": {
            "annual": {
                "revenue": 281700,
                "operating_income": 128500,
                "net_income": 101800,
                "cash_and_short_term_investments": 94600,
                "long_term_debt": 40200,
            },
            "quarterly": {
                "revenue": 82900,
                "operating_income": 38400,
                "net_income": 31800,
                "microsoft_cloud_revenue": 54500,
                "microsoft_cloud_growth": 0.29,
            },
        },
        "calculated_financial_metrics": {"operating_margin": 0.456},
        "historical_valuation": {"current_snapshot_only": True},
        "valuation_snapshot": {"status": "market_data_placeholder"},
        "market_awareness": {"missing_items": ["Analyst expectations."]},
    }
    method_path = Path(__file__).resolve().parents[1] / "methods" / "lynch_method.yaml"

    report = LynchAgent(pack=pack, method_path=method_path).generate_report()

    assert "Peter Lynch" in report
    assert "Microsoft Corporation" in report
    assert "Investment Story" in report
    assert "Follow / Watch" in report
    assert "Decision" in report


def test_bogle_agent_generate_report_contains_required_terms() -> None:
    pack = {
        "metadata": {"company_name": "Microsoft Corporation", "ticker": "MSFT"},
        "company_identity": {
            "company_name": "Microsoft Corporation",
            "ticker": "MSFT",
            "exchange": "NASDAQ",
            "market": "USA",
            "currency": "USD",
        },
        "financial_statements_summary": {
            "annual": {"revenue": 281700},
            "quarterly": {"microsoft_cloud_revenue": 54500},
        },
        "index_benchmark_alternative": {
            "benchmark_candidates": ["SPY", "VTI", "QQQ"],
            "gaps": ["Index weights missing."],
        },
        "portfolio_context_form": {"provided": False, "status": "missing"},
        "market_awareness": {"missing_items": ["Current share price."]},
    }
    method_path = Path(__file__).resolve().parents[1] / "methods" / "bogle_method.yaml"

    report = BogleAgent(pack=pack, method_path=method_path).generate_report()

    assert "John Bogle" in report
    assert "Microsoft Corporation" in report
    assert "Prefer Broad Index" in report
    assert "Individual Stock Acceptable at Limited Weight" in report
    assert "Decision" in report


def test_run_all_agent_reports_writes_all_expected_files(tmp_path: Path) -> None:
    pack = {
        "metadata": {"company_name": "Microsoft Corporation", "ticker": "MSFT"},
        "company_identity": {
            "company_name": "Microsoft Corporation",
            "ticker": "MSFT",
            "exchange": "NASDAQ",
            "market": "USA",
            "currency": "USD",
        },
        "business_model": {
            "summary": "Microsoft 365, Azure, GitHub, LinkedIn, Dynamics, cloud, and AI."
        },
        "products_customers_revenue_segments": {
            "segments": [{"name": "Intelligent Cloud", "examples": ["Azure"]}]
        },
        "financial_statements_summary": {
            "annual": {
                "revenue": 281700,
                "operating_income": 128500,
                "net_income": 101800,
                "operating_cash_flow": 136200,
                "capex": 64600,
                "free_cash_flow": 71600,
                "cash_and_short_term_investments": 94600,
                "long_term_debt": 40200,
            },
            "quarterly": {
                "revenue": 82900,
                "operating_income": 38400,
                "net_income": 31800,
                "microsoft_cloud_revenue": 54500,
                "microsoft_cloud_growth": 0.29,
                "azure_and_other_cloud_services_growth": 0.40,
            },
        },
        "calculated_financial_metrics": {"operating_margin": 0.456},
        "capex_owner_earnings_proxy": {
            "capex": 64600,
            "free_cash_flow": 71600,
            "caveat": "Maintenance versus growth capex is not disclosed.",
        },
        "growth_drivers": {"drivers": ["AI infrastructure and Copilot adoption."]},
        "sector_specific_operating_kpis": {
            "cloud": {"microsoft_cloud_revenue_q3_fy26": 54500},
            "software": {"retention_churn": "unavailable"},
        },
        "historical_valuation": {"current_snapshot_only": True},
        "peer_comparison": {"status": "incomplete"},
        "scuttlebutt": {"status": "weak_unavailable"},
        "valuation_snapshot": {"status": "market_data_placeholder"},
        "market_awareness": {"missing_items": ["Current share price."]},
        "index_benchmark_alternative": {
            "benchmark_candidates": ["SPY", "VTI", "QQQ"],
            "gaps": ["Index weights missing."],
        },
        "portfolio_context_form": {"provided": False, "status": "missing"},
        "sources_confidence_data_gaps": {
            "known_gaps": [
                "Historical valuation ranges missing.",
                "Maintenance vs growth capex not disclosed.",
                "Management compensation details missing.",
            ]
        },
    }

    results = run_all_agent_reports(pack, tmp_path)
    output_names = {Path(result["output_file"]).name for result in results}

    assert output_names == {
        "msft_buffett_report.md",
        "msft_munger_report.md",
        "msft_fisher_report.md",
        "msft_lynch_report.md",
        "msft_bogle_report.md",
    }
    for output_name in output_names:
        assert (tmp_path / output_name).exists()


def test_run_full_pipeline_writes_all_expected_files(tmp_path: Path) -> None:
    pack = {
        "metadata": {
            "company_name": "Microsoft Corporation",
            "ticker": "MSFT",
            "schema_name": "backoffice_data_pack_v2",
        },
        "company_identity": {
            "company_name": "Microsoft Corporation",
            "ticker": "MSFT",
            "exchange": "NASDAQ",
            "market": "USA",
            "currency": "USD",
        },
        "business_model": {
            "summary": "Microsoft 365, Azure, GitHub, LinkedIn, Dynamics, cloud, and AI."
        },
        "products_customers_revenue_segments": {
            "segments": [{"name": "Intelligent Cloud", "examples": ["Azure"]}]
        },
        "financial_statements_summary": {
            "annual": {
                "revenue": 281700,
                "gross_profit": 193900,
                "operating_income": 128500,
                "net_income": 101800,
                "operating_cash_flow": 136200,
                "capex": 64600,
                "free_cash_flow": 71600,
                "cash_and_short_term_investments": 94600,
                "long_term_debt": 40200,
            },
            "quarterly": {
                "revenue": 82900,
                "operating_income": 38400,
                "net_income": 31800,
                "microsoft_cloud_revenue": 54500,
                "microsoft_cloud_growth": 0.29,
                "azure_and_other_cloud_services_growth": 0.40,
            },
        },
        "calculated_financial_metrics": {"operating_margin": 0.456},
        "quality_of_earnings": {"observations": ["OCF exceeds net income."]},
        "capex_owner_earnings_proxy": {
            "capex": 64600,
            "free_cash_flow": 71600,
            "caveat": "Maintenance versus growth capex is not disclosed.",
        },
        "growth_drivers": {"drivers": ["AI infrastructure and Copilot adoption."]},
        "sector_specific_operating_kpis": {
            "cloud": {"microsoft_cloud_revenue_q3_fy26": 54500},
            "software": {"retention_churn": "unavailable"},
        },
        "historical_valuation": {"current_snapshot_only": True},
        "peer_comparison": {"status": "incomplete"},
        "scuttlebutt": {"status": "weak_unavailable"},
        "valuation_snapshot": {"status": "market_data_placeholder"},
        "market_awareness": {"missing_items": ["Current share price."]},
        "index_benchmark_alternative": {
            "benchmark_candidates": ["SPY", "VTI", "QQQ"],
            "gaps": ["Index weights missing."],
        },
        "portfolio_context_form": {"provided": False, "status": "missing"},
        "sources_confidence_data_gaps": {
            "source_log": [],
            "known_gaps": [
                "Historical valuation ranges missing.",
                "Maintenance vs growth capex not disclosed.",
                "Management compensation details missing.",
            ],
        },
    }

    output_dir = tmp_path / "data" / "outputs" / "MSFT"
    results = run_full_pipeline(pack, output_dir)
    output_names = {Path(result["output_file"]).name for result in results}

    assert output_names == {
        "msft_backoffice_data_pack.md",
        "msft_buffett_report.md",
        "msft_munger_report.md",
        "msft_fisher_report.md",
        "msft_lynch_report.md",
        "msft_bogle_report.md",
        "msft_agents_summary.md",
    }
    for output_name in output_names:
        assert (output_dir / output_name).exists()


def test_output_dir_for_ticker_returns_uppercase_data_output_path() -> None:
    assert output_dir_for_ticker("msft").as_posix().endswith("data/outputs/MSFT")


def test_run_full_pipeline_writes_aapl_outputs(tmp_path: Path) -> None:
    input_path = Path(__file__).resolve().parents[1] / "examples" / "aapl_input.yaml"
    pack = yaml.safe_load(input_path.read_text(encoding="utf-8"))
    output_dir = tmp_path / "data" / "outputs" / "AAPL"

    results = run_full_pipeline(pack, output_dir)
    output_names = {Path(result["output_file"]).name for result in results}

    assert output_names == {
        "aapl_backoffice_data_pack.md",
        "aapl_buffett_report.md",
        "aapl_munger_report.md",
        "aapl_fisher_report.md",
        "aapl_lynch_report.md",
        "aapl_bogle_report.md",
        "aapl_agents_summary.md",
    }
    for output_name in output_names:
        assert (output_dir / output_name).exists()
