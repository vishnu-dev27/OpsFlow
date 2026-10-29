"""Initial test suite (first pass): valid rows, invalid amounts,
missing columns and malformed rows.

tmp_path is a pytest feature: a fresh, empty temporary folder for each test,
so the tests never touch your real files.
"""

import csv

import pytest

from csv_processor import CsvProcessingError, process_file

HEADER = "order_id,customer_name,amount,order_date\n"


def write_input(folder, body, header=HEADER):
    """Helper: create an input CSV inside the test's temporary folder."""
    path = folder / "input.csv"
    path.write_text(header + body, encoding="utf-8-sig")
    return path


def read_rows(path):
    """Helper: read a CSV back as a list of dictionaries."""
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


# --- valid records ----------------------------------------------------------

def test_valid_rows_are_cleaned_and_written(tmp_path):
    source = write_input(
        tmp_path,
        "1,  alice   johnson ,250,2026-01-05\n"
        "2,Bob Smith,19.99,2026-01-06\n",
    )
    out = tmp_path / "out"

    result = process_file(source, out)

    assert (result.rows_read, result.valid_rows, result.rejected_rows) == (2, 2, 0)
    assert read_rows(out / "clean_output.csv") == [
        {"order_id": "1", "customer_name": "Alice Johnson", "amount": "250.00", "order_date": "2026-01-05"},
        {"order_id": "2", "customer_name": "Bob Smith", "amount": "19.99", "order_date": "2026-01-06"},
    ]
    assert read_rows(out / "error_report.csv") == []   # header only, no errors


# --- invalid amounts --------------------------------------------------------

@pytest.mark.parametrize(
    "bad_amount",
    # '"1,200"' is quoted, as a real CSV export would write a number with a
    # thousands separator. Unquoted, the comma would split it into two fields.
    ["abc", "-5", "0", "12.345", "NaN", "inf", '"1,200"', ""],
)
def test_invalid_amounts_are_rejected_with_a_reason(tmp_path, bad_amount):
    source = write_input(
        tmp_path,
        "1,Good Row,10.00,2026-01-05\n"
        f"2,Bad Row,{bad_amount},2026-01-06\n",
    )
    out = tmp_path / "out"

    result = process_file(source, out)

    assert (result.valid_rows, result.rejected_rows) == (1, 1)
    errors = read_rows(out / "error_report.csv")
    assert errors[0]["line_number"] == "3"            # header is line 1
    assert "amount" in errors[0]["reasons"]


# --- missing columns --------------------------------------------------------

def test_missing_column_stops_the_run_and_writes_nothing(tmp_path):
    source = write_input(
        tmp_path,
        "1,Alice,2026-01-05\n",
        header="order_id,customer_name,order_date\n",
    )
    out = tmp_path / "out"

    with pytest.raises(CsvProcessingError, match="amount"):
        process_file(source, out)

    assert not out.exists()                            # no half-finished output


# --- malformed rows ---------------------------------------------------------

def test_rows_with_wrong_field_count_are_rejected(tmp_path):
    source = write_input(
        tmp_path,
        "1,Alice,10.00,2026-01-05\n"
        "2,Bob,20.00\n"                               # too few fields
        "3,Carol,30.00,2026-01-07,EXTRA\n"            # too many fields
        "4,Dev,40.00,2026-01-08\n",
    )
    out = tmp_path / "out"

    result = process_file(source, out)

    assert (result.rows_read, result.valid_rows, result.rejected_rows) == (4, 2, 2)
    errors = read_rows(out / "error_report.csv")
    assert "expected 4 fields, found 3" in errors[0]["reasons"]
    assert "expected 4 fields, found 5" in errors[1]["reasons"]
    # Valid rows around the bad ones must still be kept.
    assert [r["order_id"] for r in read_rows(out / "clean_output.csv")] == ["1", "4"]


# --- extra column preservation ----------------------------------------------

def test_extra_columns_are_preserved(tmp_path):
    source = write_input(
        tmp_path,
        "1,asha rao,150,2026-02-01,IT\n",
        header="order_id,customer_name,amount,order_date,department\n",
    )
    out = tmp_path / "out"

    result = process_file(source, out)

    assert result.valid_rows == 1
    assert result.extra_columns == ["department"]

    rows = read_rows(out / "clean_output.csv")
    assert rows[0]["department"] == "IT"