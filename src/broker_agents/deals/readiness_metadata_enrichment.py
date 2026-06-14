"""Structured local metadata enrichment for readiness-only research records."""

from collections import Counter
import json
from pathlib import Path

INVESTORS = ("buffett", "munger", "fisher", "lynch", "bogle")
MISSING_VALUE = "Missing"
CORE_METADATA_FIELDS = (
    "readiness_label",
    "readiness_status",
    "readiness_score",
    "source_verification_status",
    "verified_source_count",
    "partial_source_count",
    "missing_source_count",
    "placeholder_heavy_source_count",
    "promotion_blocking_count",
    "promotion_blocking_bucket",
    *(f"{investor}_interest_level" for investor in INVESTORS),
    *(f"{investor}_decision" for investor in INVESTORS),
)
ENRICHMENT_FIELDS = (
    *CORE_METADATA_FIELDS,
    "metadata_enrichment_status",
    "missing_metadata_fields",
    "metadata_source_paths",
)
GROUPING_METADATA_FIELDS = (
    "readiness_label",
    "source_verification_status",
    *(f"{investor}_interest_level" for investor in INVESTORS),
)


def _present(value: object) -> bool:
    """Return whether a metadata value contains actual evidence."""
    return (
        value is not None
        and str(value).strip().lower()
        not in {"", "missing", "null", "none"}
    )


def _value(value: object) -> object:
    """Normalize unavailable scalar metadata without inventing content."""
    return value if _present(value) else MISSING_VALUE


def normalize_investor_interest_level(value: object) -> str:
    """Normalize an existing investor interest level."""
    return str(_value(value)).strip()


def normalize_source_verification_status(value: object) -> str:
    """Normalize an existing source verification status."""
    return str(_value(value)).strip()


def bucket_promotion_blockers(value: object) -> str:
    """Map an observed blocker count to a conservative research bucket."""
    if value in {None, "", MISSING_VALUE}:
        return "missing"
    try:
        count = int(value)
    except (TypeError, ValueError):
        return "missing"
    if count == 0:
        return "no_blockers"
    if count <= 2:
        return "low_blockers"
    if count <= 5:
        return "moderate_blockers"
    return "high_blockers"


def _load_json_object(path: Path) -> dict:
    """Load one optional structured JSON object."""
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _response_map(package_payload: dict) -> dict[str, dict]:
    """Index structured investor responses by normalized name."""
    return {
        str(response.get("investor") or "").strip().lower(): response
        for response in package_payload.get("investor_responses", [])
        if isinstance(response, dict)
    }


def _verification_counts(package_payload: dict) -> dict:
    """Extract source verification counts from the structured matrix."""
    matrix = package_payload.get("source_verification_matrix", {})
    if not isinstance(matrix, dict) or not matrix:
        return {
            "source_verification_status": MISSING_VALUE,
            "verified_source_count": MISSING_VALUE,
            "partial_source_count": MISSING_VALUE,
            "missing_source_count": MISSING_VALUE,
            "placeholder_heavy_source_count": MISSING_VALUE,
        }
    categories = [
        category
        for category in matrix.get("categories", [])
        if isinstance(category, dict)
    ]
    statuses = Counter(
        str(category.get("status") or "").strip().lower()
        for category in categories
    )
    verified = matrix.get("verified_categories_count")
    partial = matrix.get("partial_categories_count")
    combined_missing = matrix.get("missing_or_placeholder_categories_count")
    missing = statuses.get("missing")
    placeholder = statuses.get("placeholder_heavy")
    return {
        "source_verification_status": matrix.get("overall_status"),
        "verified_source_count": (
            verified if verified is not None else statuses.get("verified")
        ),
        "partial_source_count": (
            partial
            if partial is not None
            else statuses.get("partial", 0)
        ),
        "missing_source_count": (
            missing
            if categories
            else combined_missing
        ),
        "placeholder_heavy_source_count": (
            placeholder if categories else MISSING_VALUE
        ),
    }


def build_readiness_metadata(
    *,
    manifest: dict | None = None,
    package_payload: dict | None = None,
    existing_record: dict | None = None,
    source_paths: list[Path | str] | None = None,
    shared_package_source: bool = False,
) -> dict:
    """Build non-fabricated metadata from structured local artifacts."""
    manifest = manifest or {}
    package_payload = package_payload or {}
    existing_record = existing_record or {}
    responses = _response_map(package_payload)
    verification = _verification_counts(package_payload)
    blockers = manifest.get("promotion_blocking_categories")
    if blockers is None:
        blockers = existing_record.get("promotion_blocking_categories")
    if isinstance(blockers, str):
        blockers = [item for item in blockers.split(";") if item.strip()]
    blocker_count = (
        len(blockers)
        if isinstance(blockers, list)
        else existing_record.get("promotion_blocking_count")
    )
    assembly = manifest.get("historical_enriched_input_assembly", {})
    readiness_status = (
        manifest.get("readiness_status")
        or assembly.get("assembly_status")
        or existing_record.get("readiness_status")
        or existing_record.get("assembly_status")
    )
    metadata = {
        "readiness_label": (
            manifest.get("readiness_label")
            or existing_record.get("readiness_label")
        ),
        "readiness_status": readiness_status,
        "readiness_score": (
            manifest.get("readiness_score")
            or existing_record.get("readiness_score")
        ),
        "source_verification_status": (
            manifest.get("source_verification_status")
            or existing_record.get("source_verification_status")
            or verification.get("source_verification_status")
        ),
        "verified_source_count": (
            existing_record.get("verified_source_count")
            or verification.get("verified_source_count")
        ),
        "partial_source_count": (
            existing_record.get("partial_source_count")
            or verification.get("partial_source_count")
        ),
        "missing_source_count": (
            existing_record.get("missing_source_count")
            or verification.get("missing_source_count")
        ),
        "placeholder_heavy_source_count": (
            existing_record.get("placeholder_heavy_source_count")
            or verification.get("placeholder_heavy_source_count")
        ),
        "promotion_blocking_count": blocker_count,
        "promotion_blocking_bucket": bucket_promotion_blockers(blocker_count),
    }
    for investor in INVESTORS:
        response = responses.get(investor, {})
        metadata[f"{investor}_interest_level"] = (
            existing_record.get(f"{investor}_interest_level")
            or response.get("interest_level")
        )
        metadata[f"{investor}_decision"] = (
            existing_record.get(f"{investor}_decision")
            or response.get("broker_facing_final_decision")
            or response.get("final_decision")
        )
    normalized = {
        field: (
            normalize_investor_interest_level(value)
            if field.endswith("_interest_level")
            else (
                value
                if field == "promotion_blocking_bucket"
                else _value(value)
            )
        )
        for field, value in metadata.items()
    }
    missing_fields = [
        field
        for field in CORE_METADATA_FIELDS
        if not _present(normalized.get(field))
    ]
    available_count = len(CORE_METADATA_FIELDS) - len(missing_fields)
    if available_count == 0:
        enrichment_status = "missing"
    elif missing_fields or shared_package_source:
        enrichment_status = "partial"
    else:
        enrichment_status = "complete"
    paths = [
        str(Path(path))
        for path in source_paths or []
        if path and Path(path).is_file()
    ]
    normalized.update(
        {
            "metadata_enrichment_status": enrichment_status,
            "missing_metadata_fields": ";".join(missing_fields),
            "metadata_source_paths": ";".join(dict.fromkeys(paths)),
        }
    )
    return normalized


def load_readiness_metadata_for_run(
    *,
    run_folder: Path,
    existing_record: dict | None = None,
) -> dict:
    """Load structured run metadata without parsing Markdown or using network."""
    run_folder = Path(run_folder)
    manifest_path = run_folder / "run_manifest.json"
    manifest = _load_json_object(manifest_path)
    package_json_path = Path()
    package_payload = {}
    package_path_value = manifest.get("broker_deal_package_path")
    if package_path_value:
        package_json_path = Path(package_path_value).with_suffix(".json")
        package_payload = _load_json_object(package_json_path)
    sources = [manifest_path]
    if package_payload:
        sources.append(package_json_path)
    return build_readiness_metadata(
        manifest=manifest,
        package_payload=package_payload,
        existing_record=existing_record,
        source_paths=sources,
        shared_package_source=bool(package_payload),
    )


def enrich_historical_readiness_record(record: dict) -> dict:
    """Enrich one ledger row from its recorded local run folder."""
    metadata = load_readiness_metadata_for_run(
        run_folder=Path(str(record.get("run_folder") or "")),
        existing_record=record,
    )
    return {**record, **metadata}


def metadata_status_counts(records: list[dict]) -> dict[str, int]:
    """Count normalized enrichment statuses."""
    counts = Counter(
        str(record.get("metadata_enrichment_status") or "not_available")
        for record in records
    )
    return dict(sorted(counts.items()))


def missing_metadata_field_counts(records: list[dict]) -> dict[str, int]:
    """Count remaining missing fields across exported rows."""
    counts: Counter[str] = Counter()
    for record in records:
        counts.update(
            field
            for field in str(
                record.get("missing_metadata_fields") or ""
            ).split(";")
            if field
        )
    return dict(sorted(counts.items()))
