"""Final handoff validation for expanded ticker coverage artifacts."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

import yaml

SAFETY_NOTICE = (
    "This expanded ticker coverage output validation is a research handoff "
    "artifact. It does not rank or recommend tickers, validate investor "
    "agents, create trade signals, or provide allocation, rebalancing, or "
    "execution instructions."
)
CORE_TICKERS = {"MSFT", "AAPL", "NVDA", "COST"}
EXPANDED_TICKERS = {
    "GOOGL",
    "AMZN",
    "META",
    "AVGO",
    "ORCL",
    "CRM",
    "ADBE",
    "NFLX",
}
CHECK_FIELDS = ("check", "status", "evidence", "interpretation")


@dataclass(frozen=True)
class ExpandedCoverageOutputValidationReport:
    """Structured validation of Task 101 handoff artifacts."""

    validation_check_run_id: str
    generated_at: str
    source_validation_run_id: str
    source_validation_status: str | None
    output_validation_status: str
    checks: list[dict]
    pass_count: int
    warn_count: int
    fail_count: int
    eligible_tickers: list[str]
    clean_record_total: int
    usable_record_total: int
    unsupported_record_total: int
    readiness_for_expanded_trial: bool
    next_research_action: str | None
    limitations: list[str]
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready representation."""
        return asdict(self)


@dataclass(frozen=True)
class ExpandedCoverageOutputValidationFiles:
    """Generated output-validation artifact paths."""

    validation_folder: Path
    markdown_path: Path
    json_path: Path
    checks_csv_path: Path
    latest_manifest_path: Path
    report: ExpandedCoverageOutputValidationReport


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _load_csv(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except (OSError, csv.Error):
        return []


def _load_yaml(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return payload if isinstance(payload, dict) else {}


def load_latest_expanded_ticker_coverage_manifest(
    outputs_root: Path,
) -> dict:
    """Load the latest Task 101 manifest or raise a clear error."""
    path = (
        Path(outputs_root)
        / "expanded_ticker_coverage"
        / "latest_expanded_ticker_coverage_manifest.json"
    )
    if not path.is_file():
        raise FileNotFoundError(
            f"Latest expanded ticker coverage manifest not found: {path}"
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Latest expanded ticker coverage manifest is invalid: {path}"
        ) from exc
    payload["_manifest_path"] = str(path)
    return payload


def _source_paths(
    *,
    outputs_root: Path,
    validation_run_id: str,
    latest_manifest: dict | None,
) -> dict[str, Path]:
    folder = (
        Path(outputs_root)
        / "expanded_ticker_coverage"
        / validation_run_id
    )
    manifest = latest_manifest or {}
    is_latest = manifest.get("validation_run_id") == validation_run_id

    def resolved(field: str, filename: str) -> Path:
        value = manifest.get(field) if is_latest else None
        return Path(value) if value else folder / filename

    return {
        "folder": folder,
        "manifest": Path(manifest.get("_manifest_path", "")),
        "report": resolved(
            "report_json_path",
            "expanded_ticker_coverage_report.json",
        ),
        "matrix": resolved(
            "matrix_csv_path",
            "expanded_ticker_coverage_matrix.csv",
        ),
        "eligible": resolved(
            "eligible_universe_path",
            "expanded_ticker_eligible_universe.yaml",
        ),
    }


def validate_eligible_universe_yaml(payload: dict) -> tuple[list[str], bool]:
    """Return normalized eligible tickers and structural validity."""
    values = payload.get("tickers")
    if not isinstance(values, list) or not values:
        return [], False
    tickers = []
    for value in values:
        ticker = (
            value.get("ticker")
            if isinstance(value, dict)
            else value
        )
        normalized = str(ticker or "").strip().upper()
        if not normalized:
            return [], False
        tickers.append(normalized)
    return tickers, len(tickers) == len(set(tickers))


def _counts(rows: list[dict], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(field) or "")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def validate_coverage_matrix_consistency(
    *,
    report: dict,
    matrix: list[dict],
) -> dict:
    """Compare matrix-derived counts and per-ticker summaries to JSON."""
    coverage_counts = _counts(matrix, "coverage_quality")
    eligibility_counts = _counts(matrix, "eligibility")
    summaries = {
        str(item.get("ticker") or "").upper(): item
        for item in report.get("ticker_summaries", [])
    }
    ticker_mismatches = []
    for ticker in report.get("eligible_tickers", []):
        ticker = str(ticker).upper()
        rows = [
            row
            for row in matrix
            if str(row.get("ticker") or "").upper() == ticker
        ]
        clean = sum(
            row.get("eligibility") == "eligible_clean" for row in rows
        )
        usable = sum(
            row.get("eligibility") != "not_eligible" for row in rows
        )
        summary = summaries.get(ticker, {})
        if (
            int(summary.get("clean_records") or 0) != clean
            or int(summary.get("usable_records") or 0) != usable
        ):
            ticker_mismatches.append(ticker)
    return {
        "coverage_counts": coverage_counts,
        "eligibility_counts": eligibility_counts,
        "coverage_counts_match": (
            coverage_counts == report.get("coverage_quality_counts", {})
        ),
        "eligibility_counts_match": (
            eligibility_counts == report.get("eligibility_counts", {})
        ),
        "ticker_summary_mismatches": ticker_mismatches,
    }


def _check(
    name: str,
    status: str,
    evidence: object,
    interpretation: str,
) -> dict:
    return {
        "check": name,
        "status": status,
        "evidence": evidence,
        "interpretation": interpretation,
    }


def validate_expanded_ticker_coverage_outputs(
    *,
    validation_check_run_id: str,
    generated_at: str,
    outputs_root: Path,
    validation_run_id: str,
    latest_manifest: dict | None = None,
) -> ExpandedCoverageOutputValidationReport:
    """Validate Task 101 output completeness and internal consistency."""
    paths = _source_paths(
        outputs_root=outputs_root,
        validation_run_id=validation_run_id,
        latest_manifest=latest_manifest,
    )
    report_payload = _load_json(paths["report"])
    matrix_rows = _load_csv(paths["matrix"])
    eligible_payload = _load_yaml(paths["eligible"])
    eligible_yaml_tickers, eligible_yaml_valid = (
        validate_eligible_universe_yaml(eligible_payload)
    )
    manifest = latest_manifest or {}
    manifest_present = bool(
        manifest.get("validation_run_id") == validation_run_id
        or paths["folder"].is_dir()
    )
    checks = [
        _check(
            "manifest_present",
            "pass" if manifest_present else "fail",
            {"source_folder": str(paths["folder"])},
            "The source validation run is locatable.",
        ),
        _check(
            "report_json_present",
            "pass" if report_payload else "fail",
            {"path": str(paths["report"])},
            "The source report JSON is present and parseable.",
        ),
        _check(
            "matrix_csv_present",
            "pass" if matrix_rows else "fail",
            {"path": str(paths["matrix"]), "rows": len(matrix_rows)},
            "The ticker-date matrix is present and parseable.",
        ),
        _check(
            "eligible_universe_present",
            "pass" if eligible_yaml_valid else "fail",
            {"path": str(paths["eligible"])},
            "The eligible universe YAML is present and parseable.",
        ),
    ]
    eligible_tickers = [
        str(value).upper()
        for value in report_payload.get("eligible_tickers", [])
    ]
    eligible_set = set(eligible_tickers)
    checks.extend(
        [
            _check(
                "eligible_ticker_count",
                "pass" if len(eligible_tickers) >= 8 else "fail",
                {"count": len(eligible_tickers), "minimum": 8},
                "The eligible universe meets the expansion minimum.",
            ),
            _check(
                "current_core_tickers_preserved",
                "pass" if CORE_TICKERS <= eligible_set else "fail",
                {
                    "required": sorted(CORE_TICKERS),
                    "missing": sorted(CORE_TICKERS - eligible_set),
                },
                "The existing core ticker cohort remains present.",
            ),
            _check(
                "expanded_tickers_present",
                "pass" if EXPANDED_TICKERS <= eligible_set else "fail",
                {
                    "required": sorted(EXPANDED_TICKERS),
                    "missing": sorted(EXPANDED_TICKERS - eligible_set),
                },
                "The intended expanded ticker cohort is present.",
            ),
        ]
    )
    excluded = report_payload.get("excluded_tickers", [])
    checks.append(
        _check(
            "no_excluded_tickers",
            "pass" if not excluded else "warn",
            {"excluded_tickers": excluded},
            (
                "No candidate tickers were excluded."
                if not excluded
                else "Excluded candidates remain documented and omitted."
            ),
        )
    )
    summaries = {
        str(item.get("ticker") or "").upper(): item
        for item in report_payload.get("ticker_summaries", [])
    }
    clean_shortfalls = [
        ticker
        for ticker in eligible_tickers
        if int(summaries.get(ticker, {}).get("clean_records") or 0) < 2
    ]
    usable_shortfalls = [
        ticker
        for ticker in eligible_tickers
        if int(summaries.get(ticker, {}).get("usable_records") or 0) < 3
    ]
    checks.extend(
        [
            _check(
                "ticker_clean_record_minimum",
                "pass" if not clean_shortfalls else "fail",
                {"shortfalls": clean_shortfalls, "minimum": 2},
                "Each eligible ticker has at least two clean records.",
            ),
            _check(
                "ticker_usable_record_minimum",
                "pass" if not usable_shortfalls else "fail",
                {"shortfalls": usable_shortfalls, "minimum": 3},
                "Each eligible ticker has at least three usable records.",
            ),
        ]
    )
    consistency = validate_coverage_matrix_consistency(
        report=report_payload,
        matrix=matrix_rows,
    )
    unsupported_rows = [
        row
        for row in matrix_rows
        if row.get("eligibility") == "not_eligible"
    ]
    unsupported_tickers = {
        str(row.get("ticker") or "").upper() for row in unsupported_rows
    }
    unsupported_excluded = (
        not consistency["ticker_summary_mismatches"]
        and all(
            row.get("eligibility") == "not_eligible"
            for row in unsupported_rows
        )
        and unsupported_tickers <= set(report_payload.get("requested_tickers", []))
    )
    checks.extend(
        [
            _check(
                "unsupported_records_excluded",
                "pass" if unsupported_excluded else "fail",
                {
                    "unsupported_records": len(unsupported_rows),
                    "ticker_summary_mismatches": consistency[
                        "ticker_summary_mismatches"
                    ],
                },
                "Unsupported ticker-date rows are excluded from usable counts.",
            ),
            _check(
                "coverage_counts_consistent",
                (
                    "pass"
                    if consistency["coverage_counts_match"]
                    else "fail"
                ),
                {
                    "matrix": consistency["coverage_counts"],
                    "report": report_payload.get(
                        "coverage_quality_counts",
                        {},
                    ),
                },
                "Coverage-quality counts match the matrix.",
            ),
            _check(
                "eligibility_counts_consistent",
                (
                    "pass"
                    if consistency["eligibility_counts_match"]
                    else "fail"
                ),
                {
                    "matrix": consistency["eligibility_counts"],
                    "report": report_payload.get("eligibility_counts", {}),
                },
                "Eligibility counts match the matrix.",
            ),
            _check(
                "eligible_universe_matches_report",
                (
                    "pass"
                    if eligible_yaml_valid
                    and set(eligible_yaml_tickers) == eligible_set
                    else "fail"
                ),
                {
                    "report_tickers": eligible_tickers,
                    "eligible_yaml_tickers": eligible_yaml_tickers,
                },
                "The eligible universe YAML matches the report.",
            ),
        ]
    )
    report_safety = bool(report_payload.get("safety_notice"))
    manifest_safety = bool(manifest.get("safety_notice"))
    checks.extend(
        [
            _check(
                "safety_notice_present",
                "pass" if report_safety and manifest_safety else "fail",
                {
                    "report": report_safety,
                    "latest_manifest": manifest_safety,
                },
                "Safety notices are present in the source report and manifest.",
            ),
            _check(
                "next_action_ready",
                (
                    "pass"
                    if report_payload.get("next_research_action")
                    == "run_expanded_ticker_readiness_trial"
                    else "fail"
                ),
                {
                    "next_research_action": report_payload.get(
                        "next_research_action"
                    )
                },
                "The source output points to expanded trial execution.",
            ),
        ]
    )
    source_status = (
        report_payload.get("validation_status")
        or manifest.get("validation_status")
    )
    if source_status == "valid_with_cautions":
        checks.append(
            _check(
                "source_validation_cautions",
                "warn",
                {
                    "source_validation_status": source_status,
                    "delayed_price_anchor_records": consistency[
                        "coverage_counts"
                    ].get("delayed_price_anchor", 0),
                    "unsupported_records": len(unsupported_rows),
                },
                "Source cautions remain documented for the expanded trial.",
            )
        )
    pass_count = sum(item["status"] == "pass" for item in checks)
    warn_count = sum(item["status"] == "warn" for item in checks)
    fail_count = sum(item["status"] == "fail" for item in checks)
    missing_checks = {
        "manifest_present",
        "report_json_present",
        "matrix_csv_present",
        "eligible_universe_present",
    }
    failed_names = {
        item["check"] for item in checks if item["status"] == "fail"
    }
    if failed_names & missing_checks:
        output_status = "not_ready_missing_outputs"
    elif fail_count:
        output_status = "not_ready_inconsistent_outputs"
    elif warn_count:
        output_status = "ready_with_warnings"
    else:
        output_status = "ready_for_expanded_trial"
    ready = fail_count == 0
    return ExpandedCoverageOutputValidationReport(
        validation_check_run_id=validation_check_run_id,
        generated_at=generated_at,
        source_validation_run_id=validation_run_id,
        source_validation_status=source_status,
        output_validation_status=output_status,
        checks=checks,
        pass_count=pass_count,
        warn_count=warn_count,
        fail_count=fail_count,
        eligible_tickers=eligible_tickers,
        clean_record_total=consistency["eligibility_counts"].get(
            "eligible_clean",
            0,
        ),
        usable_record_total=sum(
            count
            for name, count in consistency["eligibility_counts"].items()
            if name != "not_eligible"
        ),
        unsupported_record_total=len(unsupported_rows),
        readiness_for_expanded_trial=ready,
        next_research_action=report_payload.get("next_research_action"),
        limitations=[
            "Source delayed-anchor cautions remain applicable.",
            "Unsupported ticker-date records must remain excluded.",
            "This validation does not execute or interpret a backtest.",
        ],
    )


def render_expanded_ticker_coverage_output_validation_report(
    report: ExpandedCoverageOutputValidationReport,
) -> str:
    """Render output handoff validation as Markdown."""
    lines = [
        "# Expanded Ticker Coverage Output Validation Report",
        "",
        "## Executive Summary",
        "",
        f"- Output Validation Status: {report.output_validation_status}",
        f"- Source Validation Run: {report.source_validation_run_id}",
        f"- Eligible Tickers: {', '.join(report.eligible_tickers) or 'None'}",
        (
            "- Main Finding: Task 101 outputs are complete and internally "
            "consistent for expanded trial handoff."
            if report.readiness_for_expanded_trial
            else "- Main Finding: Task 101 outputs are not ready for handoff."
        ),
        "",
        "## Validation Checks",
        "",
        "| Check | Status | Evidence | Interpretation |",
        "|---|---|---|---|",
    ]
    for item in report.checks:
        evidence = json.dumps(item["evidence"], sort_keys=True)
        lines.append(
            f"| {item['check']} | {item['status']} | `{evidence}` | "
            f"{item['interpretation']} |"
        )
    lines.extend(
        [
            "",
            "## Eligible Universe Review",
            "",
            f"- Ticker Count: {len(report.eligible_tickers)}",
            (
                "- Core Tickers Preserved: "
                f"{'Yes' if CORE_TICKERS <= set(report.eligible_tickers) else 'No'}"
            ),
            (
                "- Expanded Tickers Present: "
                f"{'Yes' if EXPANDED_TICKERS <= set(report.eligible_tickers) else 'No'}"
            ),
            f"- All Eligible Tickers: {', '.join(report.eligible_tickers)}",
            "",
            "## Coverage Consistency",
            "",
            f"- Clean Record Total: {report.clean_record_total}",
            f"- Usable Record Total: {report.usable_record_total}",
            f"- Unsupported Record Total: {report.unsupported_record_total}",
            "",
            "## Warnings",
            "",
        ]
    )
    warnings = [
        item["interpretation"]
        for item in report.checks
        if item["status"] == "warn"
    ]
    lines.extend(
        (f"- {item}" for item in warnings)
        if warnings
        else ["- No validation warnings were detected."]
    )
    lines.extend(
        [
            "",
            "## Readiness for Expanded Trial",
            "",
            (
                "- Ready for expanded readiness trial: "
                f"{'Yes' if report.readiness_for_expanded_trial else 'No'}"
            ),
            (
                "- The eligible universe file can be used as Task 103 input."
                if report.readiness_for_expanded_trial
                else "- The eligible universe file must not be used yet."
            ),
            "- Unsupported records must remain excluded.",
            "",
            "## What This Suggests",
            "",
            "- Expanded sample execution can proceed when readiness is Yes.",
            "- Coverage validation outputs are internally consistent.",
            "",
            "## What This Does Not Suggest",
            "",
            "- It does not rank tickers.",
            "- It does not recommend tickers.",
            "- It does not validate investor agents.",
            "- It does not create trade signals.",
            "- It does not justify allocation or rebalancing.",
            "",
            "## Next Research Action",
            "",
            f"- Action Code: {report.next_research_action or 'resolve_output_validation_failures'}",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in report.limitations)
    lines.extend(["", "## Safety Notice", "", report.safety_notice, ""])
    return "\n".join(lines)


def _allocate_run_id(root: Path, timestamp: datetime) -> str:
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    candidate = base
    suffix = 2
    while (root / candidate).exists():
        candidate = f"{base}_{suffix:02d}"
        suffix += 1
    return candidate


def write_expanded_ticker_coverage_output_validation_report(
    *,
    outputs_root: Path,
    validation_run_id: str,
    latest_manifest: dict | None = None,
    generated_at: datetime | None = None,
) -> ExpandedCoverageOutputValidationFiles:
    """Validate and persist a Task 101 output handoff bundle."""
    timestamp = generated_at or datetime.now(timezone.utc)
    root = Path(outputs_root) / "expanded_ticker_coverage_validations"
    root.mkdir(parents=True, exist_ok=True)
    check_run_id = _allocate_run_id(root, timestamp)
    folder = root / check_run_id
    folder.mkdir(parents=True, exist_ok=False)
    report = validate_expanded_ticker_coverage_outputs(
        validation_check_run_id=check_run_id,
        generated_at=timestamp.isoformat(),
        outputs_root=outputs_root,
        validation_run_id=validation_run_id,
        latest_manifest=latest_manifest,
    )
    markdown_path = (
        folder / "expanded_ticker_coverage_output_validation_report.md"
    )
    json_path = (
        folder / "expanded_ticker_coverage_output_validation_report.json"
    )
    checks_csv_path = (
        folder / "expanded_ticker_coverage_output_validation_checks.csv"
    )
    latest_manifest_path = (
        root
        / "latest_expanded_ticker_coverage_output_validation_manifest.json"
    )
    markdown_path.write_text(
        render_expanded_ticker_coverage_output_validation_report(report),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )
    with checks_csv_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=CHECK_FIELDS)
        writer.writeheader()
        for item in report.checks:
            writer.writerow(
                {
                    **item,
                    "evidence": json.dumps(
                        item["evidence"],
                        sort_keys=True,
                    ),
                }
            )
    latest_payload = {
        "validation_check_run_id": check_run_id,
        "source_validation_run_id": validation_run_id,
        "output_validation_status": report.output_validation_status,
        "readiness_for_expanded_trial": (
            report.readiness_for_expanded_trial
        ),
        "validation_folder": str(folder),
        "report_path": str(markdown_path),
        "report_json_path": str(json_path),
        "checks_csv_path": str(checks_csv_path),
        "generated_at": timestamp.isoformat(),
        "next_research_action": report.next_research_action,
        "safety_notice": SAFETY_NOTICE,
    }
    latest_manifest_path.write_text(
        json.dumps(latest_payload, indent=2),
        encoding="utf-8",
    )
    return ExpandedCoverageOutputValidationFiles(
        validation_folder=folder,
        markdown_path=markdown_path,
        json_path=json_path,
        checks_csv_path=checks_csv_path,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
