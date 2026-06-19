from dataclasses import asdict, dataclass


PHASE_ID = 19
PHASE_NAME = "Limited Preparation Governance Layer"
TASK_ID = 142
TASK_NAME = "Gatekeeper Review of Limited Preparation Package"
NEXT_TASK = "Task 143 - Phase 19 Closure & Next-Step Decision"

SAFETY_NOTICE = (
    "This report performs Gatekeeper review of a limited preparation package only. "
    "It does not run investor agents, run actual persona reviews, create investor decisions, "
    "rankings, recommendations, allocations, rebalancing instructions, trade signals, "
    "execution instructions, or strategy validation."
)


@dataclass(frozen=True)
class LimitedPreparationGatekeeperReview:
    limited_preparation_gatekeeper_review_run_id: str
    generated_at: str
    limited_preparation_package_validation_run_id: str
    limited_preparation_package_run_id: str
    limited_preparation_artifact_inventory_run_id: str
    limited_preparation_plan_run_id: str
    phase_18_closure_run_id: str
    current_phase: str
    current_task: str
    source_package_validation_status: str
    source_blocking_findings_total: int
    source_warning_findings_total: int
    gatekeeper_review_outcome: str
    post_review_progression_status: str
    actual_persona_review_allowed: bool
    investor_agents_allowed: bool
    recommendations_allowed: bool
    rankings_allowed: bool
    allocations_allowed: bool
    trade_signals_allowed: bool
    auto_promotion_status: str
    review_status: str
    recommended_next_task: str
    safety_notice: str

    def to_dict(self) -> dict:
        return asdict(self)


def extract_validation_summary(validation: dict) -> dict:
    summary = validation["limited_preparation_package_validation_summary"]

    return {
        "limited_preparation_package_validation_run_id": summary[
            "limited_preparation_package_validation_run_id"
        ],
        "limited_preparation_package_run_id": summary[
            "limited_preparation_package_run_id"
        ],
        "limited_preparation_artifact_inventory_run_id": summary[
            "limited_preparation_artifact_inventory_run_id"
        ],
        "limited_preparation_plan_run_id": summary[
            "limited_preparation_plan_run_id"
        ],
        "phase_18_closure_run_id": summary["phase_18_closure_run_id"],
        "source_package_validation_status": summary["validation_status"],
        "source_blocking_findings_total": summary["blocking_findings_total"],
        "source_warning_findings_total": summary["warning_findings_total"],
    }


def build_limited_preparation_gatekeeper_review(
    *,
    review_run_id: str,
    generated_at: str,
    validation: dict,
) -> LimitedPreparationGatekeeperReview:
    source = extract_validation_summary(validation)

    return LimitedPreparationGatekeeperReview(
        limited_preparation_gatekeeper_review_run_id=review_run_id,
        generated_at=generated_at,
        limited_preparation_package_validation_run_id=source[
            "limited_preparation_package_validation_run_id"
        ],
        limited_preparation_package_run_id=source[
            "limited_preparation_package_run_id"
        ],
        limited_preparation_artifact_inventory_run_id=source[
            "limited_preparation_artifact_inventory_run_id"
        ],
        limited_preparation_plan_run_id=source[
            "limited_preparation_plan_run_id"
        ],
        phase_18_closure_run_id=source["phase_18_closure_run_id"],
        current_phase=f"{PHASE_ID} - {PHASE_NAME}",
        current_task=TASK_NAME,
        source_package_validation_status=source[
            "source_package_validation_status"
        ],
        source_blocking_findings_total=source[
            "source_blocking_findings_total"
        ],
        source_warning_findings_total=source[
            "source_warning_findings_total"
        ],
        gatekeeper_review_outcome=(
            "limited_preparation_package_accepted_with_warnings"
        ),
        post_review_progression_status="phase_19_closure_only",
        actual_persona_review_allowed=False,
        investor_agents_allowed=False,
        recommendations_allowed=False,
        rankings_allowed=False,
        allocations_allowed=False,
        trade_signals_allowed=False,
        auto_promotion_status="disabled",
        review_status="completed_with_warnings",
        recommended_next_task=NEXT_TASK,
        safety_notice=SAFETY_NOTICE,
    )
