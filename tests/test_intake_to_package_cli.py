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

