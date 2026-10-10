"""HTML parsing and book-field extraction."""

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup


def parse_listing(html: str, listing_url: str) -> tuple[list[dict[str, str]], str | None]:
    """Return book stubs from a listing page and the next-page URL, if present."""
    soup = BeautifulSoup(html, "html.parser")
    books = []

    for card in soup.select("article.product_pod"):
        link = card.select_one("h3 a")
        if link is None:
            continue

        relative_url = link.get("href")
        if not relative_url:
            continue

        books.append({
            "listing_title": (link.get("title") or link.get_text(strip=True)).strip(),
            "product_url": urljoin(listing_url, relative_url),
        })

    next_link = soup.select_one("li.next a")
    next_url = urljoin(listing_url, next_link["href"]) if next_link and next_link.get("href") else None
    return books, next_url


def parse_product(html: str, product_url: str) -> dict[str, str]:
    """Extract the requested fields from one product page."""
    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.select_one(".product_main h1")
    price_tag = soup.select_one(".product_main .price_color")
    availability_tag = soup.select_one(".product_main .availability")
    rating_tag = soup.select_one(".product_main .star-rating")
    breadcrumb_links = soup.select("ul.breadcrumb li a")

    missing = [
        name for name, tag in (
            ("title", title_tag),
            ("price", price_tag),
            ("availability", availability_tag),
            ("rating", rating_tag),
        )
        if tag is None
    ]
    if len(breadcrumb_links) < 3:
        missing.append("category")
    if missing:
        raise ValueError(f"Missing required product fields: {', '.join(missing)}")

    raw_price = price_tag.get_text(strip=True)
    # Keep the numeric part as text so CSV/JSON output is consistent.
    price = re.sub(r"^[^\d]+", "", raw_price).strip()

    rating_classes = rating_tag.get("class", [])
    rating = next((item for item in rating_classes if item != "star-rating"), "Unknown")

    return {
        "title": title_tag.get_text(strip=True),
        "price": price,
        "availability": " ".join(availability_tag.get_text(" ", strip=True).split()),
        "rating": rating,
        "category": breadcrumb_links[2].get_text(strip=True),
        "product_url": product_url,
    }
