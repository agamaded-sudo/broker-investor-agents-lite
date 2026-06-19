from broker_agents.limited_preparation.limited_preparation_gatekeeper_review import (
    build_limited_preparation_gatekeeper_review,
)


def _validation_fixture() -> dict:
    return {
        "limited_preparation_package_validation_summary": {
            "limited_preparation_package_validation_run_id": "20260619_164454",
            "limited_preparation_package_run_id": "20260619_162233",
            "limited_preparation_artifact_inventory_run_id": "20260619_120518",
            "limited_preparation_plan_run_id": "20260619_112306",
            "phase_18_closure_run_id": "20260619_095701",
            "validation_status": "complete_with_warnings",
            "blocking_findings_total": 0,
            "warning_findings_total": 8,
        }
    }


def test_build_limited_preparation_gatekeeper_review_core_fields() -> None:
    review = build_limited_preparation_gatekeeper_review(
        review_run_id="review_001",
        generated_at="2026-06-19T00:00:00+00:00",
        validation=_validation_fixture(),
    )

    assert review.current_phase == "19 - Limited Preparation Governance Layer"
    assert review.current_task == "Gatekeeper Review of Limited Preparation Package"
    assert review.source_package_validation_status == "complete_with_warnings"
    assert review.source_blocking_findings_total == 0
    assert review.source_warning_findings_total == 8
    assert (
        review.gatekeeper_review_outcome
        == "limited_preparation_package_accepted_with_warnings"
    )
    assert review.post_review_progression_status == "phase_19_closure_only"
    assert review.actual_persona_review_allowed is False
    assert review.investor_agents_allowed is False
    assert review.recommendations_allowed is False
    assert review.rankings_allowed is False
    assert review.trade_signals_allowed is False
    assert review.auto_promotion_status == "disabled"
    assert (
        review.recommended_next_task
        == "Task 143 - Phase 19 Closure & Next-Step Decision"
    )


def test_limited_preparation_gatekeeper_review_to_dict_includes_safety_notice() -> None:
    review = build_limited_preparation_gatekeeper_review(
        review_run_id="review_001",
        generated_at="2026-06-19T00:00:00+00:00",
        validation=_validation_fixture(),
    )

    payload = review.to_dict()

    assert payload["safety_notice"]
    assert "does not run investor agents" in payload["safety_notice"]
    assert "trade signals" in payload["safety_notice"]
