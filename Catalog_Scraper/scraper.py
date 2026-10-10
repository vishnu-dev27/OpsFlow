"""CLI entry point for scraping Books to Scrape."""

import argparse
import json
import time
from pathlib import Path

from fetcher import fetch_page
from extractor import parse_listing, parse_product

DEFAULT_URL = "https://books.toscrape.com/"
FIELDS = ["title", "price", "availability", "rating", "category", "product_url"]


def scrape_catalog(start_url: str, max_pages: int | None = None, delay: float = 0.25):
    """Scrape listing pages and each product page sequentially."""
    results = []
    errors = []
    visited_listing_urls = set()
    current_url = start_url
    pages_processed = 0

    while current_url and current_url not in visited_listing_urls:
        if max_pages is not None and pages_processed >= max_pages:
            break

        visited_listing_urls.add(current_url)
        print(f"Fetching listing page: {current_url}")

        try:
            response = fetch_page(current_url)
        except Exception as exc:
            errors.append({"url": current_url, "stage": "listing", "error": str(exc)})
            print(f"  ERROR fetching listing: {exc}")
            break

        page_books, next_url = parse_listing(response.text, current_url)
        pages_processed += 1
        print(f"  Found {len(page_books)} book cards.")

        for index, stub in enumerate(page_books, start=1):
            product_url = stub["product_url"]
            try:
                if delay:
                    time.sleep(delay)
                product_response = fetch_page(product_url)
                book = parse_product(product_response.text, product_url)
                results.append(book)
                print(f"  [{len(results)}] {book['title']}")
            except Exception as exc:
                errors.append({
                    "url": product_url,
                    "stage": "product",
                    "title": stub["listing_title"],
                    "error": str(exc),
                })
                print(f"  ERROR on book '{stub['listing_title']}': {exc}")

        current_url = next_url

    return results, errors, pages_processed


def write_outputs(records: list[dict[str, str]], output_dir: Path):
    """Write the same records to CSV and JSON."""
    import csv

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "books.csv"
    json_path = output_dir / "books.json"

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)

    return csv_path, json_path


def write_errors(errors: list[dict[str, str]], output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    error_path = output_dir / "errors.json"
    with error_path.open("w", encoding="utf-8") as file:
        json.dump(errors, file, ensure_ascii=False, indent=2)
    return error_path


def main():
    parser = argparse.ArgumentParser(
        description="Scrape book details from the Books to Scrape practice website."
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="Starting listing-page URL")
    parser.add_argument("--max-pages", type=int, default=1,
                        help="Maximum listing pages to scrape; use 0 for all pages (default: 1)")
    parser.add_argument("--delay", type=float, default=0.25,
                        help="Seconds to pause between product requests (default: 0.25)")
    parser.add_argument("--output-dir", default="output", help="Directory for output files")
    args = parser.parse_args()

    if args.max_pages < 0:
        parser.error("--max-pages must be 0 or greater")
    if args.delay < 0:
        parser.error("--delay cannot be negative")

    max_pages = None if args.max_pages == 0 else args.max_pages
    output_dir = Path(args.output_dir)

    records, errors, pages = scrape_catalog(args.url, max_pages, args.delay)
    csv_path, json_path = write_outputs(records, output_dir)
    error_path = write_errors(errors, output_dir)

    print("\n--- Summary ---")
    print(f"Listing pages processed: {pages}")
    print(f"Books successfully scraped: {len(records)}")
    print(f"Errors: {len(errors)}")
    print(f"CSV: {csv_path}")
    print(f"JSON: {json_path}")
    print(f"Error report: {error_path}")


if __name__ == "__main__":
    main()
