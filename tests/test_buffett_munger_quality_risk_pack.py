"""Tests for BO-009 Buffett/Munger quality and risk pack."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.personas.buffett_munger_quality_risk_pack import (
    build_buffett_munger_evidence_requirements_status,
    build_buffett_munger_quality_risk_pack,
    build_buffett_munger_required_controls,
    build_buffett_quality_summary,
    build_capital_allocation_balance_sheet_matrix,
    build_munger_inversion_risk_matrix,
    build_munger_quality_summary,
    build_owner_earnings_intrinsic_value_requirements,
    build_quality_evidence_matrix,
    load_bogle_benchmark_pack_report,
    load_fisher_growth_pack_manifest,
    load_fisher_growth_pack_report,
    load_persona_evidence_pack_report,
    write_buffett_munger_quality_risk_pack_report,
)


def _fisher_pack() -> dict:
    return {
        "fisher_growth_pack_run_id": "fisher",
        "bogle_benchmark_pack_run_id": "bogle",
        "persona_evidence_pack_run_id": "persona_pack",
        "metadata_diversity_recheck_run_id": "metadata",
        "delayed_anchor_repair_run_id": "delayed",
        "walk_forward_repair_run_id": "walk",
        "outlier_repair_run_id": "outlier",
        "decomposition_run_id": "decomp",
        "backoffice_attribution_run_id": "backoffice",
        "investor_persona_attribution_run_id": "persona",
        "gatekeeper_run_id": "gatekeeper",
        "scorecard_run_id": "scorecard",
        "analysis_run_id": "analysis",
        "expanded_trial_run_id": "expanded",
        "backtest_run_id": "backtest",
    }


def _write_fixture(outputs: Path) -> None:
    fisher_folder = outputs / "fisher_qualitative_growth_packs" / "fisher"
    fisher_folder.mkdir(parents=True)
    (fisher_folder / "fisher_qualitative_growth_evidence_pack.json").write_text(
        json.dumps(_fisher_pack()),
        encoding="utf-8",
    )
    (
        outputs
        / "fisher_qualitative_growth_packs"
        / "latest_fisher_qualitative_growth_pack_manifest.json"
    ).write_text(
        json.dumps({"fisher_growth_pack_run_id": "fisher"}),
        encoding="utf-8",
    )
    linked = (
        (
            outputs / "bogle_benchmark_index_packs" / "bogle",
            "bogle_benchmark_index_comparison_pack.json",
            {"bogle_benchmark_pack_run_id": "bogle"},
        ),
        (
            outputs / "persona_evidence_pack_requirements" / "persona_pack",
            "persona_evidence_pack_requirements_report.json",
            {"persona_evidence_pack_run_id": "persona_pack"},
        ),
        (
            outputs / "metadata_diversity_rechecks" / "metadata",
            "metadata_diversity_recheck_report.json",
            {"metadata_diversity_recheck_run_id": "metadata"},
        ),
        (
            outputs / "delayed_anchor_repairs" / "delayed",
            "delayed_anchor_repair_report.json",
            {"delayed_anchor_repair_run_id": "delayed"},
        ),
        (
            outputs / "walk_forward_repair_plans" / "walk",
            "walk_forward_repair_plan_report.json",
            {"walk_forward_repair_run_id": "walk"},
        ),
        (
            outputs / "outlier_repair_paths" / "outlier",
            "outlier_repair_path_report.json",
            {"outlier_repair_run_id": "outlier"},
        ),
        (
            outputs / "backtest_driver_decompositions" / "decomp",
            "backtest_driver_decomposition_report.json",
            {"decomposition_run_id": "decomp"},
        ),
        (
            outputs / "research_evidence_scorecards" / "scorecard",
            "research_evidence_scorecard_report.json",
            {"scorecard_run_id": "scorecard"},
        ),
        (
            outputs / "expanded_trial_analyses" / "analysis",
            "expanded_trial_analysis_report.json",
            {"analysis_run_id": "analysis"},
        ),
    )
    for folder, filename, payload in linked:
        folder.mkdir(parents=True)
        (folder / filename).write_text(json.dumps(payload), encoding="utf-8")


def test_loads_latest_and_explicit_fisher_manifest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    latest = load_fisher_growth_pack_manifest(outputs_root=outputs)
    explicit = load_fisher_growth_pack_manifest(
        outputs_root=outputs,
        fisher_growth_pack_run_id="fisher",
    )
    assert latest["fisher_growth_pack_run_id"] == "fisher"
    assert explicit["backtest_run_id"] == "backtest"


def test_missing_fisher_manifest_and_report_raise(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    with pytest.raises(FileNotFoundError, match="Fisher growth pack manifest"):
        load_fisher_growth_pack_manifest(outputs_root=outputs)
    _write_fixture(outputs)
    (
        outputs
        / "fisher_qualitative_growth_packs"
        / "fisher"
        / "fisher_qualitative_growth_evidence_pack.json"
    ).unlink()
    with pytest.raises(FileNotFoundError, match="Fisher growth pack report"):
        write_buffett_munger_quality_risk_pack_report(outputs_root=outputs)


def test_loads_linked_bogle_and_persona_reports(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    assert load_fisher_growth_pack_report(
        outputs_root=outputs, fisher_growth_pack_run_id="fisher"
    )
    assert load_bogle_benchmark_pack_report(
        outputs_root=outputs, bogle_benchmark_pack_run_id="bogle"
    )
    assert load_persona_evidence_pack_report(
        outputs_root=outputs, persona_evidence_pack_run_id="persona_pack"
    )


def test_buffett_and_munger_summaries_block_review() -> None:
    buffett = build_buffett_quality_summary(buffett_munger_pack_run_id="pack")
    munger = build_munger_quality_summary(buffett_munger_pack_run_id="pack")
    assert buffett["buffett_review_allowed"] is False
    assert munger["munger_review_allowed"] is False
    assert buffett["gatekeeper_decision"] == "hold"
    assert munger["gatekeeper_decision"] == "hold"


def test_quality_evidence_matrix_includes_required_dimensions() -> None:
    dimensions = {row["evidence_dimension"] for row in build_quality_evidence_matrix()}
    assert {
        "durable_business_quality",
        "moat_or_competitive_advantage",
        "normalized_owner_earnings",
        "intrinsic_value_assumptions",
        "capital_allocation",
        "balance_sheet_resilience",
        "incentives_and_agency_risk",
    } <= dimensions


def test_owner_earnings_intrinsic_value_requirements_include_required_codes() -> None:
    codes = {
        row["requirement_code"]
        for row in build_owner_earnings_intrinsic_value_requirements()
    }
    assert {
        "normalized_owner_earnings_history",
        "intrinsic_value_range_assumptions",
        "margin_of_safety_discussion_without_recommendation",
        "no_price_target_or_buy_signal",
    } <= codes


def test_capital_allocation_balance_sheet_matrix_includes_required_areas() -> None:
    areas = {
        row["evidence_area"]
        for row in build_capital_allocation_balance_sheet_matrix()
    }
    assert {
        "buyback_discipline",
        "acquisition_discipline",
        "debt_maturity_profile",
        "liquidity_resilience",
    } <= areas


def test_munger_inversion_risk_matrix_includes_required_risks() -> None:
    risks = {row["risk_code"] for row in build_munger_inversion_risk_matrix()}
    assert {
        "incentive_misalignment",
        "agency_risk",
        "capital_allocation_error",
        "hidden_stupidity_or_complexity",
        "overreliance_on_outliers",
        "walk_forward_instability",
        "no_persona_review_until_gatekeeper_allows",
    } <= risks


def test_buffett_munger_requirements_include_persona_specific_codes() -> None:
    rows = build_buffett_munger_evidence_requirements_status()
    by_persona = {
        persona: {row["requirement_code"] for row in rows if row["persona"] == persona}
        for persona in ("Buffett", "Munger")
    }
    assert {
        "owner_earnings_evidence",
        "intrinsic_value_assumption_evidence",
        "margin_of_safety_discussion_without_recommendation",
        "no_recommendation_boundary",
    } <= by_persona["Buffett"]
    assert {
        "incentives_agency_risk_evidence",
        "inversion_risk_checklist",
        "hidden_stupidity_failure_mode_checklist",
        "no_recommendation_boundary",
    } <= by_persona["Munger"]
    controls = build_buffett_munger_required_controls()
    assert "No price target." in controls["safety_constraints"]


def test_pack_json_sections_are_created() -> None:
    report = build_buffett_munger_quality_risk_pack(
        buffett_munger_pack_run_id="pack",
        generated_at="2026-06-18T00:00:00+00:00",
        fisher_pack=_fisher_pack(),
        bogle_pack={},
        persona_pack={},
        metadata={},
        delayed_anchor={},
        walk_forward={},
        outlier={},
        decomposition={},
        scorecard={},
        expanded_analysis={},
    )
    payload = report.to_dict()
    assert payload["buffett_quality_summary"]
    assert payload["munger_quality_summary"]
    assert payload["quality_evidence_matrix"]
    assert payload["owner_earnings_intrinsic_value_requirements"]
    assert payload["capital_allocation_balance_sheet_matrix"]
    assert payload["munger_inversion_risk_matrix"]
    assert report.recommended_next_work_order == "BO-010 Research Audit Trail Bundle"


def test_writer_outputs_requested_files_and_latest_manifest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    files = write_buffett_munger_quality_risk_pack_report(
        outputs_root=outputs,
        fisher_growth_pack_run_id="fisher",
    )
    for path in (
        files.markdown_path,
        files.json_path,
        files.buffett_summary_path,
        files.munger_summary_path,
        files.quality_matrix_csv_path,
        files.owner_earnings_csv_path,
        files.capital_allocation_csv_path,
        files.munger_risk_csv_path,
        files.requirements_status_csv_path,
        files.required_controls_path,
        files.latest_manifest_path,
    ):
        assert path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert payload["buffett_quality_summary"]["buffett_review_allowed"] is False
    assert payload["munger_quality_summary"]["munger_review_allowed"] is False
    markdown = files.markdown_path.read_text(encoding="utf-8")
    for section in (
        "Important Boundary",
        "Buffett Quality Summary",
        "Munger Quality Summary",
        "Owner Earnings and Intrinsic Value Requirements",
        "Munger Inversion Risk Matrix",
        "What This Does Not Suggest",
    ):
        assert section in markdown


@pytest.mark.parametrize("auto_latest", [False, True])
def test_cli_explicit_and_auto_latest(tmp_path: Path, auto_latest: bool) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    args = [
        "build-buffett-munger-quality-risk-pack",
        "--outputs-root",
        str(outputs),
    ]
    if auto_latest:
        args.append("--auto-latest")
    else:
        args.extend(["--fisher-growth-pack-run-id", "fisher"])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "Buffett/Munger Quality and Risk Pack" in result.output
    assert "buffett_review_allowed=false" in result.output
    assert "munger_review_allowed=false" in result.output
    assert "gatekeeper_decision=hold" in result.output
    assert "recommended_next_work_order=BO-010 Research Audit Trail Bundle" in result.output
