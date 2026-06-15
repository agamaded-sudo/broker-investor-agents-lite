"""Tests for Backoffice evidence quality attribution."""

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.backtesting.backoffice_evidence_quality_attribution import (
    build_backoffice_evidence_quality_attribution,
    load_investor_persona_attribution_manifest,
    write_backoffice_evidence_quality_report,
)
from broker_agents.cli import app


def _factor(code: str, status: str, evidence: dict | None = None) -> dict:
    return {
        "factor_code": code,
        "status": status,
        "evidence": evidence or {},
        "interpretation": f"{code} evidence.",
    }


def _persona_report() -> dict:
    needs = {
        "Buffett Agent": ["owner earnings", "intrinsic value"],
        "Munger Agent": ["inversion", "hidden risks"],
        "Fisher Agent": ["management", "growth runway"],
        "Lynch Agent": ["category", "PEG"],
        "Bogle Agent": ["benchmark", "index overlap"],
    }
    return {
        "attribution_run_id": "persona",
        "gatekeeper_run_id": "gate",
        "scorecard_run_id": "scorecard",
        "analysis_run_id": "analysis",
        "expanded_trial_run_id": "expanded",
        "backtest_run_id": "backtest",
        "gatekeeper_decision": "hold",
        "progression_allowed": False,
        "attribution_status": (
            "persona_progression_blocked_by_gatekeeper_hold"
        ),
        "cross_persona_summary": {
            "persona_specific_evidence_needs": needs
        },
    }


def _scorecard() -> dict:
    return {
        "scorecard_run_id": "scorecard",
        "factor_results": [
            _factor(
                "benchmark_relative_performance",
                "negative",
                {"median_relative_return_12m": -0.05},
            ),
            _factor("walk_forward_stability", "negative"),
            _factor("expanded_cohort_effect", "negative"),
            _factor("period_sensitivity", "negative"),
            _factor(
                "outlier_dependence",
                "negative",
                {"outlier_dependence_status": "result_sensitive_to_nvda"},
            ),
            _factor("delayed_anchor_effect", "negative"),
        ],
    }


def _analysis() -> dict:
    return {
        "analysis_run_id": "analysis",
        "metadata_diversity_recheck": {
            "metadata_diversity_status": "partially_concentrated",
            "low_diversity_fields": [
                "buffett_interest_level",
                "munger_interest_level",
            ],
        },
    }


def _write_fixture(outputs: Path) -> dict:
    persona_folder = outputs / "investor_persona_attributions" / "persona"
    persona_folder.mkdir(parents=True)
    persona_path = persona_folder / "investor_persona_attribution_report.json"
    persona_path.write_text(json.dumps(_persona_report()), encoding="utf-8")
    (outputs / "investor_persona_attributions" / (
        "latest_investor_persona_attribution_manifest.json"
    )).write_text(
        json.dumps({"attribution_run_id": "persona"}),
        encoding="utf-8",
    )
    gate_folder = outputs / "research_gatekeepers" / "gate"
    gate_folder.mkdir(parents=True)
    (gate_folder / "research_gatekeeper_report.json").write_text(
        json.dumps(
            {
                "gatekeeper_run_id": "gate",
                "gatekeeper_decision": "hold",
                "progression_allowed": False,
            }
        ),
        encoding="utf-8",
    )
    score_folder = outputs / "research_evidence_scorecards" / "scorecard"
    score_folder.mkdir(parents=True)
    (score_folder / "research_evidence_scorecard_report.json").write_text(
        json.dumps(_scorecard()), encoding="utf-8"
    )
    analysis_folder = outputs / "expanded_trial_analyses" / "analysis"
    analysis_folder.mkdir(parents=True)
    (analysis_folder / "expanded_trial_analysis_report.json").write_text(
        json.dumps(_analysis()), encoding="utf-8"
    )
    return {"persona_path": persona_path}


def test_loads_latest_and_explicit_persona_manifest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    latest = load_investor_persona_attribution_manifest(
        outputs_root=outputs
    )
    explicit = load_investor_persona_attribution_manifest(
        outputs_root=outputs, attribution_run_id="persona"
    )
    assert latest["attribution_run_id"] == "persona"
    assert explicit["gatekeeper_decision"] == "hold"


def test_missing_persona_manifest_and_report_raise(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    with pytest.raises(FileNotFoundError, match="manifest not found"):
        load_investor_persona_attribution_manifest(outputs_root=outputs)
    source = _write_fixture(outputs)
    source["persona_path"].unlink()
    with pytest.raises(FileNotFoundError, match="report not found"):
        write_backoffice_evidence_quality_report(outputs_root=outputs)


def test_builds_all_required_issue_categories_and_priorities() -> None:
    report = build_backoffice_evidence_quality_attribution(
        backoffice_attribution_run_id="backoffice",
        generated_at="2026-06-15T00:00:00+00:00",
        persona_report=_persona_report(),
        gatekeeper={"gatekeeper_run_id": "gate"},
        scorecard=_scorecard(),
        analysis=_analysis(),
    )
    by_code = {
        issue["issue_code"]: issue for issue in report.evidence_issues
    }
    assert set(by_code) == {
        "benchmark_relative_underperformance",
        "walk_forward_instability",
        "expanded_cohort_underperformance",
        "period_sensitivity",
        "outlier_dependence",
        "delayed_anchor_effect",
        "metadata_diversity_partial_concentration",
        "investor_interest_low_diversity",
        "persona_specific_evidence_gaps",
        "qualitative_depth_gaps",
        "index_comparison_gap",
        "documentation_and_audit_trail",
    }
    assert by_code["benchmark_relative_underperformance"]["priority"] == "P0"
    assert by_code["outlier_dependence"]["priority"] == "P0"
    assert by_code["delayed_anchor_effect"]["priority"] == "P1"
    assert by_code["metadata_diversity_partial_concentration"]["priority"] == "P2"
    assert by_code["documentation_and_audit_trail"]["priority"] == "P3"


def test_builds_all_required_work_orders() -> None:
    report = build_backoffice_evidence_quality_attribution(
        backoffice_attribution_run_id="backoffice",
        generated_at="2026-06-15T00:00:00+00:00",
        persona_report=_persona_report(),
        gatekeeper={},
        scorecard=_scorecard(),
        analysis=_analysis(),
    )
    titles = {order["title"] for order in report.work_orders}
    assert titles == {
        "Backtest Driver Decomposition",
        "Outlier and Ex-NVDA Repair Path",
        "Walk-Forward Stability Repair Plan",
        "Delayed Anchor Exposure Repair",
        "Metadata Diversity Recheck",
        "Persona-Specific Evidence Pack Requirements",
        "Bogle Benchmark / Index Comparison Pack",
        "Fisher Qualitative Growth Evidence Pack",
        "Buffett/Munger Quality and Risk Pack",
        "Research Audit Trail Bundle",
    }
    audit = next(
        order
        for order in report.work_orders
        if order["title"] == "Research Audit Trail Bundle"
    )
    assert audit["status"] == "documentation_only"


def test_status_summary_and_next_action_are_conservative() -> None:
    report = build_backoffice_evidence_quality_attribution(
        backoffice_attribution_run_id="backoffice",
        generated_at="2026-06-15T00:00:00+00:00",
        persona_report=_persona_report(),
        gatekeeper={},
        scorecard=_scorecard(),
        analysis=_analysis(),
    )
    assert report.attribution_status == (
        "backoffice_repair_required_before_progression"
    )
    assert report.progression_allowed is False
    assert report.recommended_next_research_action == (
        "execute_backoffice_repair_work_orders"
    )
    summary = report.backoffice_attribution_summary
    assert summary["total_issues"] == 12
    assert summary["p0_issues"] == 4
    assert summary["p1_issues"] == 4
    assert summary["total_work_orders"] == 10
    assert summary["blocked_work_orders"] == 0


def test_writer_outputs_reports_csvs_and_latest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    files = write_backoffice_evidence_quality_report(
        outputs_root=outputs,
        attribution_run_id="persona",
        generated_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
    )
    for path in (
        files.markdown_path,
        files.json_path,
        files.issues_csv_path,
        files.work_orders_csv_path,
        files.latest_manifest_path,
    ):
        assert path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert payload["evidence_issues"]
    assert payload["work_orders"]
    assert payload["backoffice_attribution_summary"]
    markdown = files.markdown_path.read_text(encoding="utf-8")
    for section in (
        "Important Boundary",
        "Evidence Issue Summary",
        "Backoffice Work Orders",
        "P0 Work Orders",
        "Persona Linkage",
    ):
        assert section in markdown


@pytest.mark.parametrize("auto_latest", [False, True])
def test_cli_explicit_and_auto_latest(
    tmp_path: Path, auto_latest: bool
) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    args = [
        "build-backoffice-evidence-quality-attribution",
        "--outputs-root",
        str(outputs),
    ]
    if auto_latest:
        args.append("--auto-latest")
    else:
        args.extend(["--persona-attribution-run-id", "persona"])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "Backoffice Evidence Quality Attribution" in result.output
    assert "backoffice_repair_required_before_progression" in result.output
    assert "progression_allowed=false" in result.output
