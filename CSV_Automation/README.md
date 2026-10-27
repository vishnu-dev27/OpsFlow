# CSV Automation (OpsFlow Part 3)

**Messy orders file in. Clean data and a plain-English error report out.**

This tool checks every row of an orders CSV, writes the good rows to a clean file, and writes the bad rows to a separate error report with the exact reason each one was rejected. Nothing is silently dropped or guessed.

## What you send

An orders CSV with these columns (any order; capitalisation and extra spaces in the header are ignored):

`order_id`, `customer_name`, `amount`, `order_date`

Any extra columns you have (region, notes, product code) are kept.

## What you get

| File | Contents |
|---|---|
| `clean_output.csv` | Every valid row, tidied and in a consistent format |
| `error_report.csv` | Every rejected row: its line number in your original file, all reasons it failed, and the original values |
| Run summary | Rows read, valid rows, rejected rows, blank lines skipped |

## How rows are checked

| Field | Rule |
|---|---|
| Field count | Must match the header |
| `order_id` | Not blank, and not already used by an earlier valid row |
| `customer_name` | Not blank |
| `amount` | A plain number, greater than 0, at most 2 decimal places |
| `order_date` | A real calendar date written as YYYY-MM-DD |

All problems with a row are listed together, so you fix a row once instead of finding errors one at a time.

**Cleaning applied to valid rows:** extra spaces trimmed, all-lowercase names capitalised (`carol white` becomes `Carol White`), and amounts written with exactly 2 decimals (`1200` becomes `1200.00`). Names that already contain capitals, such as `McDonald`, are left as typed.

## Problems with the whole file

These stop the run and nothing is written, because no row could be trusted:

- file not found, or completely empty
- a header but no data rows
- a required column is missing (the message names it)
- duplicate column names
- broken CSV quoting, or the file is not UTF-8
- an output file is locked (for example, open in Excel), with a message telling you to close it

## Example

A run prints a summary like this (numbers are illustrative):

```
Rows read      : 120
Valid rows     : 112  -> output/clean_output.csv
Rejected rows  : 8  -> output/error_report.csv
Blank lines skipped: 2
Extra column(s) preserved: region
```

A rejected row in `error_report.csv` looks like this:

```
line_number: 14
reasons: amount 'abc' is not a valid number (use digits and an optional decimal point, e.g. 1234.50); order_date '2026-13-40' is not a real calendar date
original_row: 1042 | carol white | abc | 2026-13-40
```

## Why you can trust the output

- **Money is handled exactly.** Amounts use `Decimal`, not floating-point numbers, so `19.99` stays exactly `19.99`.
- **Amounts are never silently rounded.** `12.345` is rejected for you to decide, not turned into 12.35 or 12.34.
- **Nothing is lost.** The program checks that valid rows plus rejected rows equal the rows read, by counting the rows actually written to disk.
- **No accidental overwriting.** Existing output files are never replaced unless explicitly requested, and the output can never overwrite your input.
- **The error report is always produced**, even when empty, so you never read a stale one from an earlier run.

## Run results

| Code | Meaning |
|---|---|
| 0 | Every row was valid |
| 2 | Finished, but some rows were rejected (see `error_report.csv`) |
| 1 | Fatal problem, nothing written |

## Files in this project

| File | Purpose |
|---|---|
| `csv_processor.py` | The whole program |
| `tests/` | Automated tests |
| `sample_data/` | Example inputs: valid, mixed good and bad rows, missing column, empty, header only, malformed |

## Testing

Automated tests cover valid records, invalid amounts (8 variants), a missing column, and malformed rows (too few and too many fields). Further cases are implemented but not yet covered by automated tests: empty files, header-only files, existing output files, duplicate IDs, dates, blank lines, extra columns, and run result codes.

## Known limitations

- Only UTF-8 files with comma delimiters are supported.
- The two output files are written one after the other, not as one all-or-nothing step. If the program is forcibly stopped between them, one file could be new and the other from an earlier run.
- Names like `o'brien` become `O'brien`, since only the first letter is capitalised.