"""Tests for investor persona research evidence attribution."""

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.backtesting.investor_persona_attribution import (
    build_investor_persona_attribution,
    load_research_gatekeeper_manifest,
    write_investor_persona_attribution_report,
)
from broker_agents.cli import app


def _gatekeeper() -> dict:
    return {
        "gatekeeper_run_id": "gate",
        "scorecard_run_id": "scorecard",
        "analysis_run_id": "analysis",
        "expanded_trial_run_id": "expanded",
        "backtest_run_id": "backtest",
        "gatekeeper_decision": "hold",
        "progression_allowed": False,
        "hold_bias": True,
        "research_progression_status": "held_for_deeper_research",
    }


def _write_fixture(
    outputs: Path,
    *,
    include_scorecard: bool = True,
    include_analysis: bool = True,
) -> dict:
    gate_folder = outputs / "research_gatekeepers" / "gate"
    gate_folder.mkdir(parents=True)
    gate_path = gate_folder / "research_gatekeeper_report.json"
    gate_path.write_text(json.dumps(_gatekeeper()), encoding="utf-8")
    latest = outputs / "research_gatekeepers"
    (latest / "latest_research_gatekeeper_manifest.json").write_text(
        json.dumps(
            {
                "gatekeeper_run_id": "gate",
                "scorecard_run_id": "scorecard",
                "analysis_run_id": "analysis",
            }
        ),
        encoding="utf-8",
    )
    if include_scorecard:
        folder = outputs / "research_evidence_scorecards" / "scorecard"
        folder.mkdir(parents=True)
        (folder / "research_evidence_scorecard_report.json").write_text(
            json.dumps(
                {
                    "scorecard_run_id": "scorecard",
                    "research_evidence_classification": (
                        "unstable_research_evidence"
                    ),
                    "research_decision": "hold_for_deeper_analysis",
                }
            ),
            encoding="utf-8",
        )
    if include_analysis:
        folder = outputs / "expanded_trial_analyses" / "analysis"
        folder.mkdir(parents=True)
        (folder / "expanded_trial_analysis_report.json").write_text(
            json.dumps(
                {
                    "analysis_run_id": "analysis",
                    "expanded_trial_instability_explanation": {
                        "primary_instability_drivers": [
                            "benchmark_underperformance",
                            "period_sensitivity",
                        ]
                    },
                }
            ),
            encoding="utf-8",
        )
    return {"gate_path": gate_path}


def test_loads_latest_and_explicit_gatekeeper_manifest(
    tmp_path: Path,
) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    latest = load_research_gatekeeper_manifest(outputs_root=outputs)
    explicit = load_research_gatekeeper_manifest(
        outputs_root=outputs,
        gatekeeper_run_id="gate",
    )
    assert latest["gatekeeper_run_id"] == "gate"
    assert explicit["gatekeeper_decision"] == "hold"


def test_missing_gatekeeper_manifest_and_report_raise(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    with pytest.raises(FileNotFoundError, match="manifest not found"):
        load_research_gatekeeper_manifest(outputs_root=outputs)
    source = _write_fixture(outputs)
    source["gate_path"].unlink()
    with pytest.raises(FileNotFoundError, match="report not found"):
        write_investor_persona_attribution_report(outputs_root=outputs)


def test_missing_linked_scorecard_is_handled_gracefully(
    tmp_path: Path,
) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs, include_scorecard=False)
    files = write_investor_persona_attribution_report(
        outputs_root=outputs,
        gatekeeper_run_id="gate",
        generated_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
    )
    assert files.report.attribution_status == (
        "persona_progression_blocked_by_gatekeeper_hold"
    )
    assert any(
        "scorecard report was unavailable" in item
        for item in files.report.limitations
    )


def test_all_personas_have_distinct_required_evidence() -> None:
    report = build_investor_persona_attribution(
        attribution_run_id="attribution",
        generated_at="2026-06-15T00:00:00+00:00",
        gatekeeper=_gatekeeper(),
        scorecard={},
        analysis={},
    )
    by_persona = {
        item["persona"]: item for item in report.persona_attributions
    }
    assert set(by_persona) == {
        "Buffett Agent",
        "Munger Agent",
        "Fisher Agent",
        "Lynch Agent",
        "Bogle Agent",
    }
    joined = {
        name: " ".join(item["evidence_needed_before_persona_review"]).lower()
        for name, item in by_persona.items()
    }
    assert "owner earnings" in joined["Buffett Agent"]
    assert "intrinsic value" in joined["Buffett Agent"]
    assert "margin-of-safety" in joined["Buffett Agent"]
    assert "inversion" in joined["Munger Agent"]
    assert "hidden-risk" in joined["Munger Agent"]
    assert "hidden-stupidity" in joined["Munger Agent"]
    assert "growth runway" in joined["Fisher Agent"]
    assert "management depth" in joined["Fisher Agent"]
    assert "scuttlebutt" in joined["Fisher Agent"]
    assert "category-by-company" in joined["Lynch Agent"]
    assert "peg" in joined["Lynch Agent"]
    assert "earnings-story" in joined["Lynch Agent"]
    assert "benchmark-relative" in joined["Bogle Agent"]
    assert "index" in joined["Bogle Agent"]
    assert "concentration-risk" in joined["Bogle Agent"]


def test_hold_blocks_ready_status_and_builds_summary() -> None:
    report = build_investor_persona_attribution(
        attribution_run_id="attribution",
        generated_at="2026-06-15T00:00:00+00:00",
        gatekeeper=_gatekeeper(),
        scorecard={},
        analysis={},
    )
    assert report.attribution_status == (
        "persona_progression_blocked_by_gatekeeper_hold"
    )
    assert report.progression_allowed is False
    assert all(
        item["persona_readiness_status"] != "persona_review_ready"
        for item in report.persona_attributions
    )
    summary = report.cross_persona_summary
    assert summary["personas_ready_count"] == 0
    assert summary["persona_specific_evidence_needs"]
    assert report.common_holding_factors
    assert report.recommended_next_research_action == (
        "backoffice_evidence_quality_attribution"
    )


def test_report_has_no_aggregation_or_decision_fields() -> None:
    report = build_investor_persona_attribution(
        attribution_run_id="attribution",
        generated_at="2026-06-15T00:00:00+00:00",
        gatekeeper=_gatekeeper(),
        scorecard={},
        analysis={},
    )
    payload = report.to_dict()
    forbidden_keys = {
        "ranking",
        "rankings",
        "consensus",
        "vote",
        "average_agent_score",
        "persona_decision",
    }
    assert forbidden_keys.isdisjoint(payload)
    assert all(forbidden_keys.isdisjoint(item) for item in payload["persona_attributions"])


def test_writer_outputs_json_markdown_csv_and_latest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    files = write_investor_persona_attribution_report(
        outputs_root=outputs,
        gatekeeper_run_id="gate",
        generated_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
    )
    for path in (
        files.markdown_path,
        files.json_path,
        files.matrix_csv_path,
        files.latest_manifest_path,
    ):
        assert path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert len(payload["persona_attributions"]) == 5
    assert payload["cross_persona_summary"]
    assert payload["safety_notice"]
    markdown = files.markdown_path.read_text(encoding="utf-8")
    for section in (
        "Important Boundary",
        "Persona Attribution Matrix",
        "Buffett Agent Attribution",
        "Munger Agent Attribution",
        "Fisher Agent Attribution",
        "Lynch Agent Attribution",
        "Bogle Agent Attribution",
    ):
        assert section in markdown


@pytest.mark.parametrize("auto_latest", [False, True])
def test_cli_explicit_and_auto_latest(
    tmp_path: Path,
    auto_latest: bool,
) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    args = [
        "build-investor-persona-attribution",
        "--outputs-root",
        str(outputs),
    ]
    if auto_latest:
        args.append("--auto-latest")
    else:
        args.extend(["--gatekeeper-run-id", "gate"])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "Investor-Agent Attribution by Persona" in result.output
    assert "persona_progression_blocked_by_gatekeeper_hold" in result.output
    assert "progression_allowed=false" in result.output
