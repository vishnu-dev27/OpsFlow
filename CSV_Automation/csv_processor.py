"""csv_processor.py - OpsFlow Part 3: CSV Automation.

Reads, validates, cleans, and separates valid and rejected CSV rows.
Extra columns are preserved in valid output rows.
"""

import argparse
import csv
import re
import string
import sys
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = ["order_id", "customer_name", "amount", "order_date"]
CLEAN_OUTPUT_NAME = "clean_output.csv"
ERROR_REPORT_NAME = "error_report.csv"
ERROR_REPORT_COLUMNS = ["line_number", "reasons", "original_row"]

AMOUNT_PATTERN = re.compile(r"^-?[0-9]+(\.[0-9]+)?$")
DATE_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


class CsvProcessingError(Exception):
    """A file-level problem that prevents safe processing."""


@dataclass
class ProcessingResult:
    """Summary of a completed processing run."""

    input_path: Path
    clean_path: Path
    error_path: Path
    rows_read: int = 0
    valid_rows: int = 0
    rejected_rows: int = 0
    blank_lines_skipped: int = 0
    extra_columns: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Step 1: Reading the CSV
# ---------------------------------------------------------------------------

def is_blank_line(row):
    """Return True for a completely empty CSV line."""
    return len(row) == 0 or (len(row) == 1 and row[0].strip() == "")


def read_csv_file(path):
    """Read and validate the CSV structure.

    Returns:
        column_positions, extra_columns, data_rows, blank_lines, header_width
    """
    path = Path(path)

    if not path.is_file():
        raise CsvProcessingError(f"Input file not found: {path}")

    header = None
    data_rows = []
    blank_lines = 0

    try:
        with open(path, newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle, strict=True)
            previous_line = 0

            for row in reader:
                line_number = previous_line + 1
                previous_line = reader.line_num

                if is_blank_line(row):
                    blank_lines += 1
                    continue

                if header is None:
                    header = row
                else:
                    data_rows.append((line_number, row))

    except csv.Error as error:
        raise CsvProcessingError(
            f"The file is not valid CSV near line {reader.line_num}: {error}"
        ) from error
    except UnicodeDecodeError as error:
        raise CsvProcessingError(
            "The file could not be read as UTF-8 text. "
            "In Excel, use 'Save As > CSV UTF-8'."
        ) from error

    if header is None:
        raise CsvProcessingError("The file is empty: it has no header row.")

    # Normalize header names, e.g. " Amount " becomes "amount".
    names = [name.strip().lower() for name in header]

    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise CsvProcessingError(
            f"Duplicate column names in the header: {', '.join(duplicates)}"
        )

    missing = [col for col in REQUIRED_COLUMNS if col not in names]
    if missing:
        raise CsvProcessingError(
            f"Missing required column(s): {', '.join(missing)}. "
            f"Columns found: {', '.join(names)}"
        )

    if not data_rows:
        raise CsvProcessingError(
            "The file has a header but no data rows, so there is nothing to process."
        )

    # Map every header to its position, including extra columns.
    column_positions = {name: index for index, name in enumerate(names)}
    extra_columns = [name for name in names if name not in REQUIRED_COLUMNS]

    return column_positions, extra_columns, data_rows, blank_lines, len(names)


# ---------------------------------------------------------------------------
# Step 2: Validating individual values
# ---------------------------------------------------------------------------

def tidy_customer_name(name):
    """Trim extra spaces and standardize capitalization."""
    return string.capwords(name)


def check_amount(text):
    """Return (Decimal value or None, validation reason or None)."""
    if not text:
        return None, "amount is missing"

    if not AMOUNT_PATTERN.fullmatch(text):
        return None, (
            f"amount '{text}' is not a valid number "
            "(use digits and an optional decimal point, e.g. 1234.50)"
        )

    value = Decimal(text)

    if value <= 0:
        return None, f"amount '{text}' must be greater than 0"

    decimals = text.split(".")[1].rstrip("0") if "." in text else ""
    if len(decimals) > 2:
        return None, f"amount '{text}' has more than 2 decimal places"

    return value, None


def check_date(text):
    """Return (normalized date or None, validation reason or None)."""
    if not text:
        return None, "order_date is missing"

    if not DATE_PATTERN.fullmatch(text):
        return None, f"order_date '{text}' is not in YYYY-MM-DD format"

    try:
        parsed = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None, f"order_date '{text}' is not a real calendar date"

    return parsed.isoformat(), None


def validate_row(fields, column_positions, header_width, accepted_ids):
    """Validate a row and return (clean row or None, reasons)."""

    if len(fields) != header_width:
        return None, [
            f"expected {header_width} fields, found {len(fields)}"
        ]

    reasons = []

    def get(column):
        return fields[column_positions[column]].strip()

    order_id = get("order_id")

    if not order_id:
        reasons.append("order_id is missing")
    elif order_id in accepted_ids:
        reasons.append(
            f"duplicate order_id '{order_id}' "
            f"(already used on line {accepted_ids[order_id]})"
        )

    customer_name = tidy_customer_name(get("customer_name"))
    if not customer_name:
        reasons.append("customer_name is missing")

    amount, amount_problem = check_amount(get("amount"))
    if amount_problem:
        reasons.append(amount_problem)

    order_date, date_problem = check_date(get("order_date"))
    if date_problem:
        reasons.append(date_problem)

    if reasons:
        return None, reasons

    # Clean the required fields.
    clean_row = {
        "order_id": order_id,
        "customer_name": customer_name,
        "amount": f"{amount:.2f}",
        "order_date": order_date,
    }

    # Preserve every extra column's value in the same row.
    for column, position in column_positions.items():
        if column not in REQUIRED_COLUMNS:
            clean_row[column] = fields[position].strip()

    return clean_row, []


# ---------------------------------------------------------------------------
# Step 3: Writing the results
# ---------------------------------------------------------------------------

def write_clean_csv(path, rows, extra_columns):
    """Write valid rows, retaining any additional input columns."""
    fieldnames = REQUIRED_COLUMNS + extra_columns

    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_error_report(path, rejected):
    """Write rejected rows with their line numbers and validation reasons."""
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(ERROR_REPORT_COLUMNS)

        for line_number, reasons, original in rejected:
            writer.writerow([
                line_number,
                "; ".join(reasons),
                " | ".join(original),
            ])


def count_data_rows(path):
    """Count data rows in a generated CSV, excluding its header."""
    with open(path, newline="", encoding="utf-8") as handle:
        return max(sum(1 for _ in csv.reader(handle)) - 1, 0)


# ---------------------------------------------------------------------------
# Step 4: The complete workflow
# ---------------------------------------------------------------------------

def process_file(input_path, output_dir, overwrite=False):
    """Process the input CSV and return a ProcessingResult."""
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    clean_path = output_dir / CLEAN_OUTPUT_NAME
    error_path = output_dir / ERROR_REPORT_NAME

    # Never overwrite the input file with an output.
    if input_path.resolve() in (clean_path.resolve(), error_path.resolve()):
        raise CsvProcessingError(
            "An output file would overwrite the input file."
        )

    (
        column_positions,
        extra_columns,
        data_rows,
        blank_lines,
        header_width,
    ) = read_csv_file(input_path)

    valid = []
    rejected = []
    accepted_ids = {}

    for line_number, fields in data_rows:
        clean_row, reasons = validate_row(
            fields,
            column_positions,
            header_width,
            accepted_ids,
        )

        if reasons:
            rejected.append((line_number, reasons, fields))
        else:
            valid.append(clean_row)
            accepted_ids[clean_row["order_id"]] = line_number

    # Every input data row must be accounted for.
    if len(valid) + len(rejected) != len(data_rows):
        raise CsvProcessingError(
            "Internal error: some rows were neither accepted nor rejected. "
            "Nothing was written."
        )

    # Protect previous output files unless overwrite was requested.
    existing = [p.name for p in (clean_path, error_path) if p.exists()]
    if existing and not overwrite:
        raise CsvProcessingError(
            f"Output already exists in {output_dir}: {', '.join(existing)}. "
            "Use --overwrite to replace it, or choose another --output-dir."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    write_clean_csv(clean_path, valid, extra_columns)
    write_error_report(error_path, rejected)

    # Count rows from the files actually written.
    result = ProcessingResult(
        input_path=input_path,
        clean_path=clean_path,
        error_path=error_path,
        rows_read=len(data_rows),
        valid_rows=count_data_rows(clean_path),
        rejected_rows=count_data_rows(error_path),
        blank_lines_skipped=blank_lines,
        extra_columns=extra_columns,
    )

    if result.valid_rows + result.rejected_rows != result.rows_read:
        raise CsvProcessingError(
            "The written files do not add up to the rows read. "
            "Do not trust this output."
        )

    return result


def print_summary(result):
    print(f"Input file     : {result.input_path}")
    print(f"Rows read      : {result.rows_read}")
    print(f"Valid rows     : {result.valid_rows}  -> {result.clean_path}")
    print(f"Rejected rows  : {result.rejected_rows}  -> {result.error_path}")

    if result.blank_lines_skipped:
        print(f"Blank lines skipped: {result.blank_lines_skipped}")

    if result.extra_columns:
        print(
            "Extra column(s) preserved: "
            f"{', '.join(result.extra_columns)}"
        )


# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate and clean an orders CSV file."
    )
    parser.add_argument("input_csv", help="path to the input CSV file")
    parser.add_argument(
        "--output-dir",
        default="output",
        help="where to write results (default: output)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace existing output files",
    )

    args = parser.parse_args(argv)

    try:
        result = process_file(
            args.input_csv,
            args.output_dir,
            overwrite=args.overwrite,
        )
    except CsvProcessingError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print_summary(result)
    return 2 if result.rejected_rows else 0


if __name__ == "__main__":
    sys.exit(main())