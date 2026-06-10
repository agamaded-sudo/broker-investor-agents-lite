"""Tests for the documented four-company trial workflow."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "docs" / "trial_run_checklist.md"
RESULTS_TEMPLATE = ROOT / "docs" / "trial_run_results_template.md"
BASH_SCRIPT = ROOT / "scripts" / "run_trial_demo.sh"
POWERSHELL_SCRIPT = ROOT / "scripts" / "run_trial_demo.ps1"
README = ROOT / "README.md"


def test_trial_run_files_exist() -> None:
    for path in (CHECKLIST, RESULTS_TEMPLATE, BASH_SCRIPT, POWERSHELL_SCRIPT):
        assert path.exists(), f"Missing trial-run artifact: {path}"


def test_trial_run_checklist_contains_required_sections() -> None:
    checklist = CHECKLIST.read_text(encoding="utf-8")

    for text in (
        "Trial Run Checklist",
        "Scope of This Trial",
        "Companies for Trial",
        "Run Commands",
        "Broker Review Checklist",
        "Pass / Fail Criteria",
        "Safety Reminder",
    ):
        assert text in checklist
    for ticker in ("MSFT", "AAPL", "NVDA", "COST"):
        assert ticker in checklist


def test_trial_results_template_covers_all_companies() -> None:
    template = RESULTS_TEMPLATE.read_text(encoding="utf-8")

    assert "Trial Run Results" in template
    assert "Overall Result" in template
    assert "Cross-System Observations" in template
    assert "Ready for first manual user trial? Yes/No" in template
    for ticker in ("MSFT", "AAPL", "NVDA", "COST"):
        assert f"### {ticker}" in template


def test_demo_scripts_run_only_the_documented_trial_workflow() -> None:
    scripts = [
        BASH_SCRIPT.read_text(encoding="utf-8"),
        POWERSHELL_SCRIPT.read_text(encoding="utf-8"),
    ]

    for script in scripts:
        assert "MSFT,AAPL,NVDA,COST" in script
        assert "ruff check ." in script
        assert "pytest" in script
        assert "deal-intakes" in script
        assert "run-deals" in script
        for forbidden_command in (
            "portfolio-readiness",
            "human-review-queue",
            "audit-candidates",
            "buy-order",
            "sell-order",
            "rebalance",
        ):
            assert forbidden_command not in script


def test_readme_links_to_trial_run_demo() -> None:
    readme = README.read_text(encoding="utf-8")

    assert "Trial Run / Demo" in readme
    assert "docs/trial_run_checklist.md" in readme
    assert "docs/trial_run_results_template.md" in readme
    assert "bash scripts/run_trial_demo.sh" in readme
    assert "scripts/run_trial_demo.ps1" in readme
