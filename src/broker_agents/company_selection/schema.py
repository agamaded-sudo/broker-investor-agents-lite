from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


JsonObject = dict[str, Any]


FORBIDDEN_DECISION_FIELDS = frozenset(
    {
        "recommendation",
        "buy_recommendation",
        "sell_recommendation",
        "rating",
        "rank",
        "ranking",
        "investment_rank",
        "target_price",
        "position_size",
        "allocation",
        "portfolio_weight",
        "trade_signal",
        "entry_price",
        "exit_price",
        "stop_loss",
        "execution_instruction",
        "investor_decision",
        "auto_promotion",
    }
)

REQUIRED_MANUAL_LIST_FIELDS = (
    "list_id",
    "as_of_date",
    "source_type",
    "candidates",
    "safety_boundary",
)

REQUIRED_CANDIDATE_FIELDS = (
    "company_name",
    "ticker",
    "exchange",
    "listing_country",
)

REQUIRED_SELECTION_RECORD_FIELDS = (
    "record_id",
    "as_of_date",
    "company_name",
    "ticker",
    "exchange",
    "listing_country",
    "selection_reason",
    "pipeline_ready_intake_payload",
    "safety_boundary",
)

REQUIRED_PIPELINE_PAYLOAD_FIELDS = (
    "company_name",
    "ticker",
    "exchange",
    "listing_country",
    "as_of_date",
    "requested_output",
)

PREPARATION_ONLY_OUTPUTS = frozenset({"package_readiness"})
ALLOWED_USER_PRIORITIES = frozenset({"high", "medium", "low"})


class CandidateSelectionError(ValueError):
    """Raised when Company Selection Agent input violates safety rules."""


def _require_mapping(value: object, *, context: str) -> JsonObject:
    if not isinstance(value, dict):
        raise CandidateSelectionError(f"{context} must be a JSON object.")
    return value


def _require_required_fields(
    payload: JsonObject,
    required_fields: tuple[str, ...],
    *,
    context: str,
) -> None:
    for field_name in required_fields:
        if field_name not in payload:
            raise CandidateSelectionError(
                f"{context} is missing required field: {field_name}."
            )


def _validate_non_empty_string(
    value: object,
    *,
    field_name: str,
    context: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CandidateSelectionError(
            f"{context}.{field_name} must be a non-empty string."
        )
    return value.strip()


def _validate_iso_date(value: object, *, field_name: str, context: str) -> str:
    text = _validate_non_empty_string(
        value,
        field_name=field_name,
        context=context,
    )
    try:
        date.fromisoformat(text)
    except ValueError as exc:
        raise CandidateSelectionError(
            f"{context}.{field_name} must be an ISO date."
        ) from exc
    return text


def _check_forbidden_fields(value: object, *, path: str) -> None:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if key in FORBIDDEN_DECISION_FIELDS:
                raise CandidateSelectionError(
                    f"Forbidden decision field at {path}.{key}: {key}."
                )
            _check_forbidden_fields(nested_value, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _check_forbidden_fields(item, path=f"{path}[{index}]")


def _validate_optional_string_list(
    value: object,
    *,
    field_name: str,
    context: str,
) -> tuple[str, ...]:
    if value is None:
        return ()

    if not isinstance(value, list):
        raise CandidateSelectionError(f"{context}.{field_name} must be a list.")

    strings: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise CandidateSelectionError(
                f"{context}.{field_name}[{index}] must be a non-empty string."
            )
        strings.append(item.strip())

    return tuple(strings)


def _validate_safety_boundary(
    value: object,
    *,
    required_flag: str,
    context: str,
) -> JsonObject:
    boundary = _require_mapping(value, context=f"{context}.safety_boundary")

    if boundary.get(required_flag) is not True:
        raise CandidateSelectionError(
            f"{context}.safety_boundary must set {required_flag}=true."
        )

    return dict(boundary)


def _validate_requested_output(value: object, *, context: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise CandidateSelectionError(
            f"{context}.requested_output must be a non-empty list."
        )

    requested_outputs: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise CandidateSelectionError(
                f"{context}.requested_output[{index}] must be a string."
            )
        normalized = item.strip()
        if normalized not in PREPARATION_ONLY_OUTPUTS:
            raise CandidateSelectionError(
                f"{context}.requested_output must remain preparation-only."
            )
        requested_outputs.append(normalized)

    return tuple(requested_outputs)


def _validate_pipeline_ready_intake_payload(value: object) -> JsonObject:
    context = "pipeline_ready_intake_payload"
    payload = _require_mapping(value, context=context)
    _require_required_fields(
        payload,
        REQUIRED_PIPELINE_PAYLOAD_FIELDS,
        context=context,
    )

    for forbidden_multi_company_key in ("candidates", "companies", "universe"):
        if forbidden_multi_company_key in payload:
            raise CandidateSelectionError(
                f"{context} must be single-company and must not include "
                f"{forbidden_multi_company_key}."
            )

    for field_name in REQUIRED_PIPELINE_PAYLOAD_FIELDS:
        if field_name == "requested_output":
            _validate_requested_output(payload[field_name], context=context)
        elif field_name == "as_of_date":
            _validate_iso_date(payload[field_name], field_name=field_name, context=context)
        else:
            _validate_non_empty_string(
                payload[field_name],
                field_name=field_name,
                context=context,
            )

    return dict(payload)


def _require_matching_pipeline_identity(
    *,
    record_payload: JsonObject,
    pipeline_payload: JsonObject,
) -> None:
    for field_name in (
        "company_name",
        "ticker",
        "exchange",
        "listing_country",
        "as_of_date",
    ):
        if pipeline_payload[field_name] != record_payload[field_name]:
            raise CandidateSelectionError(
                "pipeline_ready_intake_payload identity must match "
                f"Candidate Selection Record field: {field_name}."
            )


@dataclass(frozen=True)
class ManualCandidate:
    """One manually supplied discovery candidate."""

    company_name: str
    ticker: str
    exchange: str
    listing_country: str
    sector: str | None = None
    industry: str | None = None
    source_universe: str | None = None
    user_priority: str | None = None
    user_notes: str | None = None
    source_references: JsonObject | list[object] | None = None
    initial_selection_signals: tuple[str, ...] = ()
    initial_eligibility_assumptions: JsonObject | None = None

    @classmethod
    def from_payload(cls, value: object, *, index: int) -> ManualCandidate:
        context = f"candidates[{index}]"
        payload = _require_mapping(value, context=context)
        _check_forbidden_fields(payload, path=context)
        _require_required_fields(
            payload,
            REQUIRED_CANDIDATE_FIELDS,
            context=context,
        )

        user_priority = payload.get("user_priority")
        if user_priority is not None:
            user_priority = _validate_non_empty_string(
                user_priority,
                field_name="user_priority",
                context=context,
            )
            if user_priority not in ALLOWED_USER_PRIORITIES:
                raise CandidateSelectionError(
                    f"{context}.user_priority must be high, medium, or low."
                )

        return cls(
            company_name=_validate_non_empty_string(
                payload["company_name"],
                field_name="company_name",
                context=context,
            ),
            ticker=_validate_non_empty_string(
                payload["ticker"],
                field_name="ticker",
                context=context,
            ),
            exchange=_validate_non_empty_string(
                payload["exchange"],
                field_name="exchange",
                context=context,
            ),
            listing_country=_validate_non_empty_string(
                payload["listing_country"],
                field_name="listing_country",
                context=context,
            ),
            sector=payload.get("sector"),
            industry=payload.get("industry"),
            source_universe=payload.get("source_universe"),
            user_priority=user_priority,
            user_notes=payload.get("user_notes"),
            source_references=payload.get("source_references"),
            initial_selection_signals=_validate_optional_string_list(
                payload.get("initial_selection_signals"),
                field_name="initial_selection_signals",
                context=context,
            ),
            initial_eligibility_assumptions=payload.get(
                "initial_eligibility_assumptions"
            ),
        )


@dataclass(frozen=True)
class ManualCandidateList:
    """Manual candidate list for the first Selection Agent MVP."""

    list_id: str
    as_of_date: str
    source_type: str
    candidates: tuple[ManualCandidate, ...]
    safety_boundary: JsonObject
    description: str | None = None
    created_by: str | None = None
    created_at: str | None = None
    notes: str | None = None

    @classmethod
    def from_payload(cls, value: object) -> ManualCandidateList:
        context = "manual_candidate_list"
        payload = _require_mapping(value, context=context)
        _check_forbidden_fields(payload, path=context)
        _require_required_fields(
            payload,
            REQUIRED_MANUAL_LIST_FIELDS,
            context=context,
        )

        source_type = _validate_non_empty_string(
            payload["source_type"],
            field_name="source_type",
            context=context,
        )
        if source_type != "manual_candidate_list":
            raise CandidateSelectionError(
                "manual_candidate_list.source_type must be manual_candidate_list."
            )

        candidates_payload = payload["candidates"]
        if not isinstance(candidates_payload, list) or not candidates_payload:
            raise CandidateSelectionError(
                "manual_candidate_list.candidates must be a non-empty list."
            )

        candidates = tuple(
            ManualCandidate.from_payload(candidate_payload, index=index)
            for index, candidate_payload in enumerate(candidates_payload)
        )

        return cls(
            list_id=_validate_non_empty_string(
                payload["list_id"],
                field_name="list_id",
                context=context,
            ),
            as_of_date=_validate_iso_date(
                payload["as_of_date"],
                field_name="as_of_date",
                context=context,
            ),
            source_type=source_type,
            candidates=candidates,
            safety_boundary=_validate_safety_boundary(
                payload["safety_boundary"],
                required_flag="manual_discovery_input_only",
                context=context,
            ),
            description=payload.get("description"),
            created_by=payload.get("created_by"),
            created_at=payload.get("created_at"),
            notes=payload.get("notes"),
        )


@dataclass(frozen=True)
class CandidateSelectionRecord:
    """Safe handoff from Selection Agent to Single-Company Pipeline."""

    record_id: str
    as_of_date: str
    company_name: str
    ticker: str
    exchange: str
    listing_country: str
    selection_reason: str
    pipeline_ready_intake_payload: JsonObject
    safety_boundary: JsonObject
    sector: str | None = None
    industry: str | None = None
    source_universe: str | None = None
    selection_signals: tuple[str, ...] = ()
    source_references: JsonObject | list[object] | None = None
    eligibility_filter_results: JsonObject | None = None
    attention_filter_results: JsonObject | None = None
    notes: str | None = None
    created_by: str | None = None
    created_at: str | None = None

    @classmethod
    def from_payload(cls, value: object) -> CandidateSelectionRecord:
        context = "candidate_selection_record"
        payload = _require_mapping(value, context=context)
        _check_forbidden_fields(payload, path=context)
        _require_required_fields(
            payload,
            REQUIRED_SELECTION_RECORD_FIELDS,
            context=context,
        )

        pipeline_payload = _validate_pipeline_ready_intake_payload(
            payload["pipeline_ready_intake_payload"]
        )

        record_payload = {
            "company_name": _validate_non_empty_string(
                payload["company_name"],
                field_name="company_name",
                context=context,
            ),
            "ticker": _validate_non_empty_string(
                payload["ticker"],
                field_name="ticker",
                context=context,
            ),
            "exchange": _validate_non_empty_string(
                payload["exchange"],
                field_name="exchange",
                context=context,
            ),
            "listing_country": _validate_non_empty_string(
                payload["listing_country"],
                field_name="listing_country",
                context=context,
            ),
            "as_of_date": _validate_iso_date(
                payload["as_of_date"],
                field_name="as_of_date",
                context=context,
            ),
        }

        _require_matching_pipeline_identity(
            record_payload=record_payload,
            pipeline_payload=pipeline_payload,
        )

        return cls(
            record_id=_validate_non_empty_string(
                payload["record_id"],
                field_name="record_id",
                context=context,
            ),
            as_of_date=record_payload["as_of_date"],
            company_name=record_payload["company_name"],
            ticker=record_payload["ticker"],
            exchange=record_payload["exchange"],
            listing_country=record_payload["listing_country"],
            selection_reason=_validate_non_empty_string(
                payload["selection_reason"],
                field_name="selection_reason",
                context=context,
            ),
            pipeline_ready_intake_payload=pipeline_payload,
            safety_boundary=_validate_safety_boundary(
                payload["safety_boundary"],
                required_flag="discovery_and_routing_only",
                context=context,
            ),
            sector=payload.get("sector"),
            industry=payload.get("industry"),
            source_universe=payload.get("source_universe"),
            selection_signals=_validate_optional_string_list(
                payload.get("selection_signals"),
                field_name="selection_signals",
                context=context,
            ),
            source_references=payload.get("source_references"),
            eligibility_filter_results=payload.get("eligibility_filter_results"),
            attention_filter_results=payload.get("attention_filter_results"),
            notes=payload.get("notes"),
            created_by=payload.get("created_by"),
            created_at=payload.get("created_at"),
        )
