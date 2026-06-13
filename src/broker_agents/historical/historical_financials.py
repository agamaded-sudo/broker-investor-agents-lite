"""Offline parser and point-in-time filter for historical financial CSVs."""

import csv
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

REQUIRED_COLUMNS = (
    "ticker",
    "fiscal_period_end_date",
    "filing_date",
    "accepted_date",
    "statement_type",
    "period_type",
    "metric",
    "value",
    "source_url_or_accession_number",
)
OPTIONAL_COLUMNS = (
    "currency",
    "units",
    "form_type",
    "fiscal_year",
    "fiscal_quarter",
    "data_as_of_date",
    "ingestion_date",
    "source_name",
)


@dataclass(frozen=True)
class HistoricalFinancialRow:
    """One normalized point-in-time financial fact."""

    ticker: str
    fiscal_period_end_date: date
    filing_date: date | None
    accepted_date: date | None
    statement_type: str
    period_type: str
    metric: str
    value: float | str
    source_url_or_accession_number: str
    currency: str | None = None
    units: str | None = None
    form_type: str | None = None
    fiscal_year: str | None = None
    fiscal_quarter: str | None = None
    data_as_of_date: date | None = None
    ingestion_date: date | None = None
    source_name: str | None = None


@dataclass(frozen=True)
class HistoricalFinancialsValidationResult:
    """Structural validation result for one local financials CSV."""

    path: Path
    file_found: bool
    rows_count: int
    required_columns_present: bool
    missing_required_columns: list[str] = field(default_factory=list)
    rows_missing_availability_date_count: int = 0
    rows_missing_source_traceability_count: int = 0
    status: str = "missing_file"
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HistoricalFinancialsFilterResult:
    """Filtered rows and audit metadata for one historical cutoff."""

    rows: list[HistoricalFinancialRow] = field(default_factory=list)
    as_of_date: str = ""
    rows_before_filter: int = 0
    rows_after_filter: int = 0
    future_rows_excluded_count: int = 0
    rows_missing_availability_date_count: int = 0
    max_filing_date_after_filter: str | None = None
    max_accepted_date_after_filter: str | None = None
    status: str = "missing_financials_data"
    warnings: list[str] = field(default_factory=list)


def historical_financials_path(root: Path, ticker: str) -> Path:
    """Return the conventional local historical-financials file path."""
    return Path(root) / f"{ticker.strip().lower()}_financials_as_of.csv"


def _parse_required_date(value: str, field_name: str, row_number: int) -> date:
    """Parse one required ISO date or timestamp."""
    parsed = _parse_optional_date(value, field_name, row_number)
    if parsed is None:
        raise ValueError(f"Row {row_number}: {field_name} is required.")
    return parsed


def _parse_optional_date(
    value: str | None,
    field_name: str,
    row_number: int,
) -> date | None:
    """Parse an optional ISO date or timestamp into a calendar date."""
    text = str(value or "").strip()
    if not text:
        return None
    try:
        if "T" in text or " " in text:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(
            f"Row {row_number}: {field_name} must use an ISO date or timestamp."
        ) from exc


def _parse_value(value: str) -> float | str:
    """Return a numeric value where possible, preserving other fixture text."""
    text = str(value).strip()
    try:
        return float(text)
    except ValueError:
        return text


def _optional_text(row: dict[str, str], key: str) -> str | None:
    """Return stripped optional text or None."""
    value = str(row.get(key) or "").strip()
    return value or None


def load_historical_financials_csv(path: Path) -> list[HistoricalFinancialRow]:
    """Load a local historical-financials CSV using the required schema."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Historical financials CSV not found: {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing:
            raise ValueError(
                "Historical financials CSV is missing required columns: "
                + ", ".join(missing)
            )
        rows = []
        for row_number, row in enumerate(reader, start=2):
            rows.append(
                HistoricalFinancialRow(
                    ticker=str(row["ticker"]).strip().upper(),
                    fiscal_period_end_date=_parse_required_date(
                        row["fiscal_period_end_date"],
                        "fiscal_period_end_date",
                        row_number,
                    ),
                    filing_date=_parse_optional_date(
                        row["filing_date"], "filing_date", row_number
                    ),
                    accepted_date=_parse_optional_date(
                        row["accepted_date"], "accepted_date", row_number
                    ),
                    statement_type=str(row["statement_type"]).strip(),
                    period_type=str(row["period_type"]).strip(),
                    metric=str(row["metric"]).strip(),
                    value=_parse_value(row["value"]),
                    source_url_or_accession_number=str(
                        row["source_url_or_accession_number"]
                    ).strip(),
                    currency=_optional_text(row, "currency"),
                    units=_optional_text(row, "units"),
                    form_type=_optional_text(row, "form_type"),
                    fiscal_year=_optional_text(row, "fiscal_year"),
                    fiscal_quarter=_optional_text(row, "fiscal_quarter"),
                    data_as_of_date=_parse_optional_date(
                        row.get("data_as_of_date"),
                        "data_as_of_date",
                        row_number,
                    ),
                    ingestion_date=_parse_optional_date(
                        row.get("ingestion_date"),
                        "ingestion_date",
                        row_number,
                    ),
                    source_name=_optional_text(row, "source_name"),
                )
            )
    if not rows:
        raise ValueError(f"Historical financials CSV is empty: {path}")
    return rows


def validate_historical_financials_csv(
    path: Path,
) -> HistoricalFinancialsValidationResult:
    """Validate local schema, dates, availability, and source traceability."""
    path = Path(path)
    if not path.is_file():
        return HistoricalFinancialsValidationResult(
            path=path,
            file_found=False,
            rows_count=0,
            required_columns_present=False,
            status="missing_file",
            warnings=[f"Historical financials CSV not found: {path}"],
        )
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
    missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
    if missing:
        return HistoricalFinancialsValidationResult(
            path=path,
            file_found=True,
            rows_count=0,
            required_columns_present=False,
            missing_required_columns=missing,
            status="missing_required_columns",
            warnings=["Missing required columns: " + ", ".join(missing)],
        )
    try:
        rows = load_historical_financials_csv(path)
    except (OSError, ValueError) as exc:
        return HistoricalFinancialsValidationResult(
            path=path,
            file_found=True,
            rows_count=0,
            required_columns_present=True,
            status="invalid_financials_data",
            warnings=[str(exc)],
        )
    missing_availability = sum(
        row.filing_date is None and row.accepted_date is None for row in rows
    )
    missing_source = sum(
        not row.source_url_or_accession_number for row in rows
    )
    warnings = []
    if missing_availability:
        warnings.append(
            f"{missing_availability} row(s) lack filing_date and accepted_date."
        )
    if missing_source:
        warnings.append(
            f"{missing_source} row(s) lack source traceability."
        )
    return HistoricalFinancialsValidationResult(
        path=path,
        file_found=True,
        rows_count=len(rows),
        required_columns_present=True,
        rows_missing_availability_date_count=missing_availability,
        rows_missing_source_traceability_count=missing_source,
        status="valid_with_warnings" if warnings else "valid",
        warnings=warnings,
    )


def filter_financials_as_of(
    rows: list[HistoricalFinancialRow],
    as_of_date: str | date,
) -> HistoricalFinancialsFilterResult:
    """Keep only facts available by filing or accepted date at the cutoff."""
    try:
        cutoff = (
            as_of_date
            if isinstance(as_of_date, date)
            else date.fromisoformat(str(as_of_date))
        )
    except ValueError as exc:
        raise ValueError("as_of_date must use YYYY-MM-DD format.") from exc

    included = []
    future_count = 0
    missing_availability = 0
    for row in rows:
        availability_dates = [
            value
            for value in (row.filing_date, row.accepted_date)
            if value is not None
        ]
        if not availability_dates:
            missing_availability += 1
            continue
        if any(value <= cutoff for value in availability_dates):
            included.append(row)
        else:
            future_count += 1

    filing_dates = [row.filing_date for row in included if row.filing_date]
    accepted_dates = [row.accepted_date for row in included if row.accepted_date]
    warnings = []
    if missing_availability:
        warnings.append(
            f"{missing_availability} row(s) were excluded because no filing or "
            "accepted date was available."
        )
    status = "as_of_filter_applied" if included else "no_rows_available_as_of_date"
    return HistoricalFinancialsFilterResult(
        rows=included,
        as_of_date=cutoff.isoformat(),
        rows_before_filter=len(rows),
        rows_after_filter=len(included),
        future_rows_excluded_count=future_count,
        rows_missing_availability_date_count=missing_availability,
        max_filing_date_after_filter=(
            max(filing_dates).isoformat() if filing_dates else None
        ),
        max_accepted_date_after_filter=(
            max(accepted_dates).isoformat() if accepted_dates else None
        ),
        status=status,
        warnings=warnings,
    )

def historical_financial_row_to_dict(row: HistoricalFinancialRow) -> dict[str, str]:
    """Serialize one normalized row using the public CSV schema."""
    return {
        "ticker": row.ticker,
        "fiscal_period_end_date": row.fiscal_period_end_date.isoformat(),
        "filing_date": row.filing_date.isoformat() if row.filing_date else "",
        "accepted_date": (
            row.accepted_date.isoformat() if row.accepted_date else ""
        ),
        "statement_type": row.statement_type,
        "period_type": row.period_type,
        "metric": row.metric,
        "value": str(row.value),
        "source_url_or_accession_number": (
            row.source_url_or_accession_number
        ),
        "currency": row.currency or "",
        "units": row.units or "",
        "form_type": row.form_type or "",
        "fiscal_year": row.fiscal_year or "",
        "fiscal_quarter": row.fiscal_quarter or "",
        "data_as_of_date": (
            row.data_as_of_date.isoformat() if row.data_as_of_date else ""
        ),
        "ingestion_date": (
            row.ingestion_date.isoformat() if row.ingestion_date else ""
        ),
        "source_name": row.source_name or "",
    }


def write_historical_financials_csv(
    path: Path,
    rows: list[HistoricalFinancialRow],
) -> Path:
    """Write filtered rows as a lightweight run-local CSV snapshot."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [*REQUIRED_COLUMNS, *OPTIONAL_COLUMNS]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(historical_financial_row_to_dict(row))
    return path
