from json import loads
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.cli import app


runner = CliRunner()


def test_intake_to_package_cli_writes_artifacts(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "intake-to-package",
            "--company-name",
            "Microsoft Corporation",
            "--ticker",
            "MSFT",
            "--exchange",
            "NASDAQ",
            "--listing-country",
            "United States",
            "--as-of-date",
            "2026-06-24",
            "--output-root",
            str(tmp_path),
            "--run-id",
            "cli_run",
        ],
    )

    assert result.exit_code == 0
    assert (tmp_path / "cli_run" / "package_readiness_report.md").is_file()
    assert (tmp_path / "cli_run" / "package_readiness_report.json").is_file()
    assert (tmp_path / "latest_package_readiness_manifest.json").is_file()


def test_intake_to_package_cli_preserves_safety_boundary(
    tmp_path: Path,
) -> None:
    result = runner.invoke(
        app,
        [
            "intake-to-package",
            "--company-name",
            "Microsoft Corporation",
            "--ticker",
            "MSFT",
            "--exchange",
            "NASDAQ",
            "--listing-country",
            "United States",
            "--as-of-date",
            "2026-06-24",
            "--output-root",
            str(tmp_path),
            "--run-id",
            "safety_cli_run",
        ],
    )

    assert result.exit_code == 0
    assert "No investor-agent execution" in result.output
    assert "recommendation" in result.output
    assert "trade signal" in result.output
    assert "auto-promotion" in result.output


def test_intake_to_package_cli_keeps_human_review_required(
    tmp_path: Path,
) -> None:
    result = runner.invoke(
        app,
        [
            "intake-to-package",
            "--company-name",
            "Microsoft Corporation",
            "--ticker",
            "MSFT",
            "--exchange",
            "NASDAQ",
            "--listing-country",
            "United States",
            "--as-of-date",
            "2026-06-24",
            "--output-root",
            str(tmp_path),
            "--run-id",
            "human_review_cli_run",
        ],
    )

    assert result.exit_code == 0

    report = loads(
        (tmp_path / "human_review_cli_run" / "package_readiness_report.json").read_text(
            encoding="utf-8"
        )
    )

    assert report["human_review_required"] is True


def test_intake_to_package_cli_blocks_investment_requested_output(
    tmp_path: Path,
) -> None:
    result = runner.invoke(
        app,
        [
            "intake-to-package",
            "--company-name",
            "Microsoft Corporation",
            "--ticker",
            "MSFT",
            "--exchange",
            "NASDAQ",
            "--listing-country",
            "United States",
            "--as-of-date",
            "2026-06-24",
            "--requested-output",
            "recommendation",
            "--output-root",
            str(tmp_path),
            "--run-id",
            "blocked_output_cli_run",
        ],
    )

    assert result.exit_code == 0

    report = loads(
        (tmp_path / "blocked_output_cli_run" / "package_readiness_report.json").read_text(
            encoding="utf-8"
        )
    )

    assert report["readiness_label"] == "not_ready"
    assert any(
        blocker["related_field"] == "requested_output"
        for blocker in report["blockers"]
    )


def test_intake_to_package_cli_output_is_preparation_only(
    tmp_path: Path,
) -> None:
    result = runner.invoke(
        app,
        [
            "intake-to-package",
            "--company-name",
            "Microsoft Corporation",
            "--ticker",
            "MSFT",
            "--exchange",
            "NASDAQ",
            "--listing-country",
            "United States",
            "--as-of-date",
            "2026-06-24",
            "--output-root",
            str(tmp_path),
            "--run-id",
            "prep_only_cli_run",
        ],
    )

    assert result.exit_code == 0
    assert "readiness_label:" in result.output
    assert "human_review_required: True" in result.output
    assert "allowed_next_step:" in result.output
    assert "buy_signal" not in result.output
    assert "sell_signal" not in result.output
    assert "portfolio_weight" not in result.output



def test_intake_to_package_cli_accepts_json_input_file(
    tmp_path: Path,
) -> None:
    input_file = tmp_path / "msft_intake.json"
    input_file.write_text(
        "{\n"
        + '  "company_name": "Microsoft Corporation",\n'
        + '  "ticker": "MSFT",\n'
        + '  "exchange": "NASDAQ",\n'
        + '  "listing_country": "United States",\n'
        + '  "as_of_date": "2026-06-24",\n'
        + '  "requested_output": ["package_readiness"]\n'
        + "}\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "intake-to-package",
            "--input-file",
            str(input_file),
            "--output-root",
            str(tmp_path / "outputs"),
            "--run-id",
            "json_input_cli_run",
        ],
    )

    assert result.exit_code == 0
    assert (
        tmp_path
        / "outputs"
        / "json_input_cli_run"
        / "package_readiness_report.md"
    ).is_file()
    assert (
        tmp_path
        / "outputs"
        / "json_input_cli_run"
        / "package_readiness_report.json"
    ).is_file()


def test_intake_to_package_cli_json_input_blocks_investment_output(
    tmp_path: Path,
) -> None:
    input_file = tmp_path / "blocked_intake.json"
    input_file.write_text(
        "{\n"
        + '  "company_name": "Microsoft Corporation",\n'
        + '  "ticker": "MSFT",\n'
        + '  "exchange": "NASDAQ",\n'
        + '  "listing_country": "United States",\n'
        + '  "as_of_date": "2026-06-24",\n'
        + '  "requested_output": ["recommendation"]\n'
        + "}\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "intake-to-package",
            "--input-file",
            str(input_file),
            "--output-root",
            str(tmp_path / "outputs"),
            "--run-id",
            "blocked_json_input_cli_run",
        ],
    )

    assert result.exit_code == 0

    report = loads(
        (
            tmp_path
            / "outputs"
            / "blocked_json_input_cli_run"
            / "package_readiness_report.json"
        ).read_text(encoding="utf-8")
    )

    assert report["readiness_label"] == "not_ready"
    assert any(
        blocker["related_field"] == "requested_output"
        for blocker in report["blockers"]
    )


def test_intake_to_package_cli_json_input_preserves_safety_boundary(
    tmp_path: Path,
) -> None:
    input_file = tmp_path / "safe_intake.json"
    input_file.write_text(
        "{\n"
        + '  "company_name": "Microsoft Corporation",\n'
        + '  "ticker": "MSFT",\n'
        + '  "exchange": "NASDAQ",\n'
        + '  "listing_country": "United States",\n'
        + '  "as_of_date": "2026-06-24"\n'
        + "}\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "intake-to-package",
            "--input-file",
            str(input_file),
            "--output-root",
            str(tmp_path / "outputs"),
            "--run-id",
            "safe_json_input_cli_run",
        ],
    )

    assert result.exit_code == 0
    assert "No investor-agent execution" in result.output
    assert "recommendation" in result.output
    assert "trade signal" in result.output
    assert "auto-promotion" in result.output



def test_intake_to_package_cli_accepts_utf8_bom_json_input_file(
    tmp_path: Path,
) -> None:
    input_file = tmp_path / "bom_intake.json"
    input_file.write_bytes(
        b"\xef\xbb\xbf"
        b"{\n"
        b'  "company_name": "Microsoft Corporation",\n'
        b'  "ticker": "MSFT",\n'
        b'  "exchange": "NASDAQ",\n'
        b'  "listing_country": "United States",\n'
        b'  "as_of_date": "2026-06-24",\n'
        b'  "requested_output": ["package_readiness"]\n'
        b"}\n"
    )

    result = runner.invoke(
        app,
        [
            "intake-to-package",
            "--input-file",
            str(input_file),
            "--output-root",
            str(tmp_path / "outputs"),
            "--run-id",
            "bom_json_input_cli_run",
        ],
    )

    assert result.exit_code == 0
    assert (
        tmp_path
        / "outputs"
        / "bom_json_input_cli_run"
        / "package_readiness_report.md"
    ).is_file()
    assert (
        tmp_path
        / "outputs"
        / "bom_json_input_cli_run"
        / "package_readiness_report.json"
    ).is_file()

