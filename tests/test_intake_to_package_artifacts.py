from json import loads
from pathlib import Path

from broker_agents.intake_to_package import (
    PackageReadinessLabel,
    write_package_readiness_artifacts,
)


def test_write_package_readiness_artifacts_creates_files(tmp_path: Path) -> None:
    bundle = write_package_readiness_artifacts(
        _complete_payload(),
        output_root=tmp_path,
        run_id="test_run_001",
    )

    assert Path(bundle.markdown_path).is_file()
    assert Path(bundle.json_path).is_file()
    assert Path(bundle.manifest_path).is_file()


def test_write_package_readiness_artifacts_uses_requested_run_id(
    tmp_path: Path,
) -> None:
    bundle = write_package_readiness_artifacts(
        _complete_payload(),
        output_root=tmp_path,
        run_id="fixed_run_id",
    )

    assert bundle.run_id == "fixed_run_id"
    assert Path(bundle.output_dir).name == "fixed_run_id"


def test_write_package_readiness_artifacts_writes_markdown(
    tmp_path: Path,
) -> None:
    bundle = write_package_readiness_artifacts(
        _complete_payload(),
        output_root=tmp_path,
        run_id="markdown_run",
    )

    markdown = Path(bundle.markdown_path).read_text(encoding="utf-8")

    assert "# Intake-to-Package Readiness Report" in markdown
    assert "## Safety Boundary" in markdown
    assert "No investor-agent execution" in markdown


def test_write_package_readiness_artifacts_writes_json_report(
    tmp_path: Path,
) -> None:
    bundle = write_package_readiness_artifacts(
        _complete_payload(),
        output_root=tmp_path,
        run_id="json_run",
    )

    report_data = loads(Path(bundle.json_path).read_text(encoding="utf-8"))

    assert report_data["company_name"] == "Microsoft Corporation"
    assert report_data["readiness_label"] == (
        PackageReadinessLabel.READY_FOR_HUMAN_REVIEW.value
    )
    assert report_data["human_review_required"] is True


def test_write_package_readiness_artifacts_updates_latest_manifest(
    tmp_path: Path,
) -> None:
    bundle = write_package_readiness_artifacts(
        _complete_payload(),
        output_root=tmp_path,
        run_id="manifest_run",
    )

    manifest = loads(Path(bundle.manifest_path).read_text(encoding="utf-8"))

    assert manifest["run_id"] == "manifest_run"
    assert manifest["readiness_label"] == (
        PackageReadinessLabel.READY_FOR_HUMAN_REVIEW.value
    )
    assert manifest["markdown_path"] == bundle.markdown_path
    assert manifest["json_path"] == bundle.json_path


def test_write_package_readiness_artifacts_preserves_safety_boundary(
    tmp_path: Path,
) -> None:
    bundle = write_package_readiness_artifacts(
        _complete_payload(),
        output_root=tmp_path,
        run_id="safety_run",
    )

    manifest = loads(Path(bundle.manifest_path).read_text(encoding="utf-8"))

    assert "recommendation" in manifest["safety_boundary"]
    assert "trade signal" in manifest["safety_boundary"]
    assert "auto-promotion" in manifest["safety_boundary"]


def _complete_payload() -> dict[str, object]:
    official_source = {
        "title": "Official annual report",
        "url_or_path": "https://example.com/annual-report",
        "source_type": "annual_report",
        "publication_date": "2026-01-01",
        "access_date": "2026-06-24",
        "reliability_label": "official",
    }
    return {
        "company_name": "Microsoft Corporation",
        "ticker": "MSFT",
        "exchange": "NASDAQ",
        "listing_country": "United States",
        "as_of_date": "2026-06-24",
        "requested_output": ["package_readiness"],
        "official_filings": [official_source],
        "financial_statement_sources": [official_source],
    }

