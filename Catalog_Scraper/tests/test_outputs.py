import csv
import json
import tempfile
import unittest
from pathlib import Path

from scraper import write_outputs, write_errors, FIELDS


class OutputTests(unittest.TestCase):
    def test_writes_matching_csv_and_json(self):
        records = [{
            "title": "Example Book",
            "price": "12.99",
            "availability": "In stock",
            "rating": "Three",
            "category": "Fiction",
            "product_url": "https://example.test/book",
        }]

        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path, json_path = write_outputs(records, Path(temp_dir))

            with csv_path.open(newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                rows = list(reader)
                self.assertEqual(reader.fieldnames, FIELDS)

            with json_path.open(encoding="utf-8") as file:
                json_records = json.load(file)

            self.assertEqual(rows, records)
            self.assertEqual(json_records, records)

    def test_writes_valid_empty_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path, json_path = write_outputs([], Path(temp_dir))

            with csv_path.open(newline="", encoding="utf-8") as file:
                self.assertEqual(list(csv.DictReader(file)), [])

            with json_path.open(encoding="utf-8") as file:
                self.assertEqual(json.load(file), [])

    def test_writes_error_report(self):
        errors = [{
            "url": "https://example.test/book",
            "stage": "product",
            "error": "Request timed out",
        }]

        with tempfile.TemporaryDirectory() as temp_dir:
            error_path = write_errors(errors, Path(temp_dir))

            with error_path.open(encoding="utf-8") as file:
                self.assertEqual(json.load(file), errors)


if __name__ == "__main__":
    unittest.main()