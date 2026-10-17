# CSV Automation (OpsFlow Part 3)

Reads an orders CSV, validates every row, writes the good rows to a clean
CSV, and writes the bad rows to a separate error report with a plain-English
reason for each rejection.

**Status: first working version.** The core workflow is complete and tested
for four areas (see "What is tested"). More tests and edge cases come in the
second pass.

## Quick start

From inside the `CSV_Automation` folder:

```bash
python3 -m venv .venv            # optional but recommended
source .venv/bin/activate
pip install -r requirements.txt  # installs pytest (the program itself needs nothing)

python3 csv_processor.py sample_data/orders_mixed.csv --output-dir output
python3 -m pytest -v
```

Results appear in `output/clean_output.csv` and `output/error_report.csv`.

Options:

| Option | Meaning |
|---|---|
| `--output-dir DIR` | where to write results (default `output`) |
| `--overwrite` | replace output files from an earlier run (without it, the program refuses) |

## Input format

Required columns (any order, case and surrounding spaces are ignored):
`order_id`, `customer_name`, `amount`, `order_date`.

## Rules

**File-level problems** stop the run and write nothing:

- file not found, or completely empty
- header but no data rows
- a required column is missing (the message names it)
- duplicate column names
- broken CSV quoting, or the file is not UTF-8

**Row-level problems** reject only that row (all reasons are listed together):

| Field | Rule |
|---|---|
| field count | must match the header |
| `order_id` | not blank, not used by an earlier accepted row |
| `customer_name` | not blank |
| `amount` | plain number, greater than 0, at most 2 decimal places |
| `order_date` | a real date written `YYYY-MM-DD` |

**Cleaning of valid rows:** spaces trimmed, customer names capitalised
(`  carol   white ` becomes `Carol White`), amounts written with exactly 2
decimals (`1200` becomes `1200.00`).

**Extra columns** are not copied to the output; the summary prints a warning
naming them. **Completely blank lines** are skipped and counted in the summary.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | every row valid |
| 2 | finished, but some rows were rejected (check `error_report.csv`) |
| 1 | fatal problem, nothing written |

## Files

| File | Purpose |
|---|---|
| `csv_processor.py` | the whole program |
| `tests/test_csv_processor.py` | pytest tests |
| `sample_data/` | example inputs: valid, mixed good and bad rows, missing column, empty, header only, malformed |
| `pytest.ini` | lets the tests import `csv_processor` |
| `requirements.txt` | pytest only |

## How the code is organised

Read `csv_processor.py` top to bottom; each step is one small function.

- `read_csv_file()` reads the file, finds the header, and checks file-level
  rules. It remembers each row's **line number** so errors point to the exact
  place in the original file.
- `validate_row()` checks one row and returns either a cleaned row or a list
  of reasons. It collects *all* reasons instead of stopping at the first.
- `check_amount()` / `check_date()` hold the number and date rules.
- `process_file()` runs the whole workflow and does the safety checks.

## Design decisions

- **`Decimal`, not `float`, for money.** `float` cannot store 0.1 exactly.
  `Decimal` keeps `19.99` as exactly `19.99`.
- **Amounts are never silently rounded.** `12.345` is rejected rather than
  turned into `12.35` or `12.34`; the user decides what the right value is.
- **Strict regex before converting.** Python's `Decimal("1_000")` or
  `Decimal("NaN")` would be accepted, so the text is checked against a plain
  number pattern first.
- **File problems stop the run; row problems do not.** A missing column
  affects every row, so nothing can be trusted. One bad amount affects one row.
- **No silent data loss.** The program checks `valid + rejected = rows read`
  twice: once in memory, then again by counting the rows actually written to
  disk. The summary prints the on-disk numbers.
- **No overwriting by accident.** Existing output files are never replaced
  unless you pass `--overwrite`, and an output can never overwrite the input.
- **The error report is always written**, even when empty (header only), so
  you never read a stale one from an earlier run.
- **`original_row` in the error report** shows the raw fields joined with
  ` | ` for easy reading in a spreadsheet; it is not meant to be re-imported.

## What is tested (first pass)

`python3 -m pytest -v` covers: valid records, invalid amounts (8 variants),
a missing column, and malformed rows (too few and too many fields).

Implemented but **not yet covered by automated tests**: empty files,
header-only files, existing output files, duplicate IDs, dates, blank lines,
extra columns, exit codes. These are planned for the second pass.

## Known limitations

- `McDonald` becomes `Mcdonald` because of the simple capitalisation rule.
  Change `tidy_customer_name()` if you prefer to keep original capitals.
- The two output files are written one after the other (no all-or-nothing
  transaction yet). If the program is killed between them, you could get one
  new file and one old one. Planned improvement.
- Only UTF-8 files with comma delimiters are supported.
