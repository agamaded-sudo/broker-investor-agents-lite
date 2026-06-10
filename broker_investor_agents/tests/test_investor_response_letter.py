"""Tests for broker-facing investor response letters."""

from pathlib import Path

import pytest

from broker_agents.deals.investor_interest_response import (
    derive_investor_interest_response,
)
from broker_agents.reports.investor_response_letter import (
    generate_investor_response_letter,
    save_investor_response_letters,
)


def _response(interest_decision: str, candidate: str):
    return derive_investor_interest_response(
        ticker="MSFT",
        investor="Buffett",
        final_decision=interest_decision,
        candidate_decision=candidate,
        report_text="## Confidence Level\nMedium",
    )


@pytest.mark.parametrize(
    ("decision", "candidate", "expected"),
    [
        (
            "Buy Gradually",
            "Buy Gradually Candidate",
            "I am conditionally interested, but only through a gradual and evidence-gated approach.",
        ),
        (
            "Prefer Broad Index",
            "Index Preferred Candidate",
            "I would prefer broad index exposure rather than a separate individual position at this stage.",
        ),
        (
            "Needs More Evidence",
            "Needs More Evidence Candidate",
            "I cannot express serious interest until the missing evidence is provided.",
        ),
    ],
)
def test_response_letter_final_wording(
    decision: str,
    candidate: str,
    expected: str,
) -> None:
    letter = generate_investor_response_letter(
        "MSFT",
        "Microsoft Corporation",
        _response(decision, candidate),
    )

    for section in (
        "Dear Broker",
        "Interest Response",
        "Independent View",
        "Broker Follow-Up Required",
        "Boundary Statement",
        "Final Response",
    ):
        assert section in letter
    assert expected in letter
    assert "independent investor-agent research response" in letter
    assert "cannot be combined with other responses" in letter


def test_save_response_letters_creates_five_files(tmp_path: Path) -> None:
    responses = [
        derive_investor_interest_response(
            ticker="MSFT",
            investor=investor,
            final_decision=decision,
            candidate_decision=candidate,
        )
        for investor, decision, candidate in (
            ("Buffett", "Wait", "Wait Candidate"),
            ("Munger", "Buy Gradually", "Buy Gradually Candidate"),
            ("Fisher", "Needs More Evidence", "Needs More Evidence Candidate"),
            ("Lynch", "Follow / Watch", "Follow / Watch Candidate"),
            ("Bogle", "Prefer Broad Index", "Index Preferred Candidate"),
        )
    ]

    paths = save_investor_response_letters(
        "MSFT",
        "Microsoft Corporation",
        responses,
        tmp_path,
    )

    assert len(paths) == 5
    assert {path.name for path in paths} == {
        "msft_buffett_response_letter.md",
        "msft_munger_response_letter.md",
        "msft_fisher_response_letter.md",
        "msft_lynch_response_letter.md",
        "msft_bogle_response_letter.md",
    }
    assert all(path.exists() for path in paths)
