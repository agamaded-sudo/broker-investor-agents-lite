"""Validated as-of-date metadata for historical analysis readiness."""

from dataclasses import dataclass
from datetime import date
import re

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
POINT_IN_TIME_ENFORCEMENT = "readiness_only"
HISTORICAL_DATA_CUTOFF_NOTE = (
    "Historical mode records an as_of_date but does not yet guarantee full "
    "point-in-time data enforcement unless a provider explicitly supports it."
)
HISTORICAL_LEAKAGE_WARNING = (
    "Full point-in-time data enforcement is not yet guaranteed for all data "
    "sources. Data dated after the as_of_date may still be present in fixture "
    "or manual inputs."
)


@dataclass(frozen=True)
class AsOfContext:
    """Governance metadata for a current or historical-readiness run."""

    as_of_date: date | None
    historical_mode: bool
    point_in_time_enforcement: str
    data_cutoff_note: str
    leakage_warning: str | None

    def to_dict(self) -> dict:
        """Serialize the context for snapshots, manifests, and ledgers."""
        return {
            "as_of_date": (
                self.as_of_date.isoformat() if self.as_of_date else None
            ),
            "historical_mode": self.historical_mode,
            "point_in_time_enforcement": self.point_in_time_enforcement,
            "data_cutoff_note": self.data_cutoff_note,
            "leakage_warning": self.leakage_warning,
        }


def build_as_of_context(
    value: str | date | None,
    *,
    system_date: date | None = None,
) -> AsOfContext:
    """Validate an optional as-of date and build readiness metadata."""
    if value in {None, ""}:
        return AsOfContext(
            as_of_date=None,
            historical_mode=False,
            point_in_time_enforcement=POINT_IN_TIME_ENFORCEMENT,
            data_cutoff_note=(
                "Current analysis mode; no historical as_of_date was supplied."
            ),
            leakage_warning=None,
        )
    if isinstance(value, date):
        parsed = value
    else:
        text = str(value).strip()
        if not DATE_PATTERN.fullmatch(text):
            raise ValueError("as_of_date must use YYYY-MM-DD format.")
        try:
            parsed = date.fromisoformat(text)
        except ValueError as exc:
            raise ValueError(
                "as_of_date must be a valid calendar date in YYYY-MM-DD format."
            ) from exc
    today = system_date or date.today()
    if parsed > today:
        raise ValueError(
            f"as_of_date cannot be in the future relative to {today.isoformat()}."
        )
    return AsOfContext(
        as_of_date=parsed,
        historical_mode=True,
        point_in_time_enforcement=POINT_IN_TIME_ENFORCEMENT,
        data_cutoff_note=HISTORICAL_DATA_CUTOFF_NOTE,
        leakage_warning=HISTORICAL_LEAKAGE_WARNING,
    )
