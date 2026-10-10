# Catalog Scraper

A small, modular Python web-scraping project for the practice site [Books to Scrape](https://books.toscrape.com/).

## What it does

- Fetches listing pages with `requests`.
- Parses book cards with Beautiful Soup.
- Follows pagination links.
- Visits each book's product page to extract its full title, price, availability, rating, category, and URL.
- Writes results to CSV and JSON.
- Writes request/extraction failures to `errors.json`.
- Uses sequential requests and a small delay rather than concurrent scraping.

## Setup

Python 3.10+ is recommended.

```bash
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS**
```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run

Scrape only the homepage (20 books):

```bash
python scraper.py
```

Scrape three listing pages:

```bash
python scraper.py --max-pages 3
```

Scrape all listing pages:

```bash
python scraper.py --max-pages 0
```

Use a longer delay between product requests:

```bash
python scraper.py --max-pages 2 --delay 0.5
```

Choose another output folder:

```bash
python scraper.py --output-dir results
```

Outputs are `books.csv`, `books.json`, and `errors.json` inside the selected output directory.

## Data fields

- `title`
- `price` (numeric text without the currency symbol)
- `availability`
- `rating`
- `category`
- `product_url`

## Scope and limitations

This is a learning/portfolio project, not a general-purpose crawler. It follows the site's visible next-page link and processes pages sequentially. It does not use browser automation, concurrency, proxies, or CAPTCHA workarounds. Check the site's current usage rules before running large scrapes.

## Suggested validation

1. Run the default command and verify around 20 records.
2. Open both CSV and JSON and compare a few records.
3. Inspect `errors.json`.
4. Try `--max-pages 2`.
5. Test the parsing functions using saved HTML fixtures before making further network requests.
