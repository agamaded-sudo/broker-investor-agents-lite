"""Consolidated Backoffice work orders for broker deal evidence collection."""

from dataclasses import asdict, dataclass
from pathlib import Path

from broker_agents.deals.investor_interest_response import InvestorInterestResponse
from broker_agents.reports.investor_follow_up_memo_report import (
    INVESTOR_MEMO_SPECS,
    INVESTOR_KEYS,
)

INVESTOR_ORDER = ["Buffett", "Munger", "Fisher", "Lynch", "Bogle"]
SOURCE_CATEGORY_ORDER = [
    "official_financials",
    "market_data",
    "historical_valuation",
    "growth_peg",
    "scuttlebutt",
    "management_incentives",
    "index_overlap",
]
ARTIFACT_BY_CATEGORY = {
    "official_financials": "Verified financial evidence update",
    "market_data": "Validated market-data snapshot",
    "historical_valuation": "Validated historical valuation worksheet",
    "growth_peg": "Validated growth and PEG worksheet",
    "scuttlebutt": "Scuttlebutt evidence pack",
    "management_incentives": "Management incentives and ownership evidence pack",
    "index_overlap": "Index overlap and benchmark-risk worksheet",
}


@dataclass(frozen=True)
class BackofficeWorkOrder:
    """One evidence collection or verification task."""

    work_order_id: str
    evidence_item: str
    source_type_needed: str
    related_investors: list[str]
    related_source_verification_category: str
    priority: str
    blocks_promotion: bool
    suggested_backoffice_action: str
    expected_output_artifact: str
    rerun_required_after_completion: bool

    def to_dict(self) -> dict:
        """Serialize one work order."""
        return asdict(self)


@dataclass(frozen=True)
class BackofficeWorkOrderPlan:
    """Consolidated work-order plan for one broker deal."""

    ticker: str
    company_name: str
    enriched_pack_path: Path
    source_verification_status: str
    readiness_label: str
    work_orders: list[BackofficeWorkOrder]
    total_work_orders: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    promotion_blocking_count: int
    investors_affected: list[str]
    source_verification_categories_affected: list[str]
    promotion_blocking_categories: list[str]

    def to_dict(self) -> dict:
        """Serialize the work-order plan."""
        return {
            **asdict(self),
            "enriched_pack_path": str(self.enriched_pack_path),
            "work_orders": [item.to_dict() for item in self.work_orders],
        }


def _investor_key(investor: str) -> str:
    """Normalize an investor display name to its memo specification key."""
    return INVESTOR_KEYS.get(investor.lower(), investor.lower().replace(" ", "_"))


def _ordered_unique(values: list[str], preferred_order: list[str]) -> list[str]:
    """Return unique values with known values in a stable preferred order."""
    unique = set(values)
    ordered = [value for value in preferred_order if value in unique]
    ordered.extend(sorted(unique - set(ordered)))
    return ordered


def build_backoffice_work_order_plan(
    ticker: str,
    company_name: str,
    enriched_pack_path: Path,
    source_verification_status: str,
    readiness_label: str,
    investor_responses: list[InvestorInterestResponse],
    source_verification_summary: dict,
) -> BackofficeWorkOrderPlan:
    """Consolidate investor memo checklist items into stable work orders."""
    matrix = {
        item.get("category"): item
        for item in source_verification_summary.get("categories", [])
    }
    consolidated: dict[tuple[str, str], dict] = {}
    for response in investor_responses:
        spec = INVESTOR_MEMO_SPECS.get(_investor_key(response.investor), {})
        for evidence, source_type, why, category, priority in spec.get(
            "checklist", []
        ):
            key = (evidence, category)
            if key not in consolidated:
                consolidated[key] = {
                    "evidence": evidence,
                    "source_type": source_type,
                    "why": why,
                    "category": category,
                    "priority": priority,
                    "investors": [],
                }
            consolidated[key]["investors"].append(response.investor)
            if priority == "high":
                consolidated[key]["priority"] = "high"

    work_orders: list[BackofficeWorkOrder] = []
    for index, item in enumerate(consolidated.values(), start=1):
        category = str(item["category"])
        matrix_item = matrix.get(category, {})
        work_orders.append(
            BackofficeWorkOrder(
                work_order_id=f"WO-{ticker.upper()}-{index:03d}",
                evidence_item=str(item["evidence"]),
                source_type_needed=str(item["source_type"]),
                related_investors=_ordered_unique(
                    list(item["investors"]),
                    INVESTOR_ORDER,
                ),
                related_source_verification_category=category,
                priority=str(item["priority"]),
                blocks_promotion=bool(matrix_item.get("blocks_promotion")),
                suggested_backoffice_action=(
                    f"Collect and validate {str(item['evidence']).lower()} using "
                    f"{str(item['source_type']).lower()}."
                ),
                expected_output_artifact=ARTIFACT_BY_CATEGORY.get(
                    category,
                    "Verified evidence update",
                ),
                rerun_required_after_completion=True,
            )
        )

    priorities = [item.priority for item in work_orders]
    blocking_categories = _ordered_unique(
        [
            item.related_source_verification_category
            for item in work_orders
            if item.blocks_promotion
        ],
        SOURCE_CATEGORY_ORDER,
    )
    return BackofficeWorkOrderPlan(
        ticker=ticker.upper(),
        company_name=company_name,
        enriched_pack_path=Path(enriched_pack_path),
        source_verification_status=source_verification_status,
        readiness_label=readiness_label,
        work_orders=work_orders,
        total_work_orders=len(work_orders),
        high_priority_count=priorities.count("high"),
        medium_priority_count=priorities.count("medium"),
        low_priority_count=priorities.count("low"),
        promotion_blocking_count=sum(
            item.blocks_promotion for item in work_orders
        ),
        investors_affected=_ordered_unique(
            [
                investor
                for item in work_orders
                for investor in item.related_investors
            ],
            INVESTOR_ORDER,
        ),
        source_verification_categories_affected=_ordered_unique(
            [
                item.related_source_verification_category
                for item in work_orders
            ],
            SOURCE_CATEGORY_ORDER,
        ),
        promotion_blocking_categories=blocking_categories,
    )


def generate_backoffice_work_order_report(
    plan: BackofficeWorkOrderPlan,
) -> str:
    """Render one consolidated Backoffice operating plan."""
    lines = [
        f"# Backoffice Work Orders - {plan.ticker}",
        "",
        "## 1. Purpose",
        "",
        (
            "This document converts investor-specific evidence gaps into "
            "actionable Backoffice collection and verification tasks."
        ),
        "",
        "## 2. Company Context",
        "",
        f"- Ticker: {plan.ticker}",
        f"- Company Name: {plan.company_name}",
        f"- Enriched Pack Path: {plan.enriched_pack_path}",
        f"- Source Verification Status: {plan.source_verification_status}",
        f"- Readiness Label: {plan.readiness_label}",
        "",
        "## 3. Work Order Summary",
        "",
        f"- Total Work Orders: {plan.total_work_orders}",
        f"- High Priority Count: {plan.high_priority_count}",
        f"- Medium Priority Count: {plan.medium_priority_count}",
        f"- Low Priority Count: {plan.low_priority_count}",
        f"- Promotion-Blocking Count: {plan.promotion_blocking_count}",
        f"- Investors Affected: {', '.join(plan.investors_affected)}",
        (
            "- Source Verification Categories Affected: "
            f"{', '.join(plan.source_verification_categories_affected)}"
        ),
        "",
        "## 4. Work Orders Table",
        "",
        "| Work Order ID | Evidence Item | Source Type Needed | Related Investors | Related Source Verification Category | Priority | Blocks Promotion | Suggested Backoffice Action | Expected Output Artifact | Rerun Required After Completion |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in plan.work_orders:
        lines.append(
            f"| {item.work_order_id} | {item.evidence_item} | "
            f"{item.source_type_needed} | {', '.join(item.related_investors)} | "
            f"{item.related_source_verification_category} | {item.priority} | "
            f"{'Yes' if item.blocks_promotion else 'No'} | "
            f"{item.suggested_backoffice_action} | "
            f"{item.expected_output_artifact} | "
            f"{'Yes' if item.rerun_required_after_completion else 'No'} |"
        )

    lines.extend(
        [
            "",
            "## 5. Investor Coverage Map",
            "",
            "| Investor | Work Orders |",
            "| --- | --- |",
        ]
    )
    for investor in INVESTOR_ORDER:
        identifiers = [
            item.work_order_id
            for item in plan.work_orders
            if investor in item.related_investors
        ]
        lines.append(f"| {investor} | {', '.join(identifiers) or 'None'} |")

    lines.extend(
        [
            "",
            "## 6. Category Coverage Map",
            "",
            "| Source Verification Category | Work Orders |",
            "| --- | --- |",
        ]
    )
    for category in SOURCE_CATEGORY_ORDER:
        identifiers = [
            item.work_order_id
            for item in plan.work_orders
            if item.related_source_verification_category == category
        ]
        lines.append(f"| {category} | {', '.join(identifiers) or 'None'} |")

    lines.extend(
        [
            "",
            "## 7. Promotion-Blocking Work Orders",
            "",
            (
                "- Promotion-Blocking Categories: "
                f"{', '.join(plan.promotion_blocking_categories) or 'None'}"
            ),
        ]
    )
    blocking = [item for item in plan.work_orders if item.blocks_promotion]
    if blocking:
        lines.extend(
            f"- {item.work_order_id}: {item.evidence_item} "
            f"({item.related_source_verification_category})"
            for item in blocking
        )
    else:
        lines.append("- No work orders are marked as promotion blocking.")

    lines.extend(
        [
            "",
            "## 8. Backoffice Execution Sequence",
            "",
            "1. Collect official / financial evidence first if missing.",
            "2. Validate market and valuation methodology.",
            "3. Collect investor-specific evidence.",
            "4. Update enriched pack.",
            "5. Re-run deal workflow.",
            "6. Re-run investor agents independently.",
            "7. Refresh broker deal package and follow-up memos.",
            "",
            "## 9. Safety Note",
            "",
            (
                "This work order file is not a recommendation, ranking, vote, "
                "average score, consensus, allocation instruction, rebalancing "
                "instruction, or trade signal."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def save_backoffice_work_order_report(
    plan: BackofficeWorkOrderPlan,
    output_path: Path,
) -> Path:
    """Save a Backoffice work-order report."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        generate_backoffice_work_order_report(plan),
        encoding="utf-8",
    )
    return output_path
