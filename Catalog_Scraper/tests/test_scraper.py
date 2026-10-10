import unittest
from unittest.mock import Mock, patch

import requests

from scraper import scrape_catalog


LISTING_HTML = """
<html><body>
<article class="product_pod">
  <h3><a href="book1.html" title="Example Book">Example Book</a></h3>
</article>
</body></html>
"""

PRODUCT_HTML = """
<html><body>
<ul class="breadcrumb">
  <li><a>Home</a></li>
  <li><a>Books</a></li>
  <li><a>Fiction</a></li>
</ul>
<div class="product_main">
  <h1>Example Book</h1>
  <p class="price_color">£12.99</p>
  <p class="availability">In stock</p>
  <p class="star-rating Three"></p>
</div>
</body></html>
"""


class ScraperWorkflowTests(unittest.TestCase):
    @patch("scraper.fetch_page")
    def test_scrapes_book_from_listing(self, mock_fetch):
        listing_response = Mock()
        listing_response.text = LISTING_HTML

        product_response = Mock()
        product_response.text = PRODUCT_HTML

        mock_fetch.side_effect = [listing_response, product_response]

        records, errors, pages = scrape_catalog(
            "https://example.test/catalogue/", max_pages=1, delay=0
        )

        self.assertEqual(pages, 1)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["title"], "Example Book")
        self.assertEqual(records[0]["category"], "Fiction")
        self.assertEqual(errors, [])

    @patch("scraper.fetch_page")
    def test_product_request_failure_is_recorded(self, mock_fetch):
        listing_response = Mock()
        listing_response.text = LISTING_HTML
        mock_fetch.side_effect = [
            listing_response,
            requests.Timeout("Request timed out"),
        ]

        records, errors, pages = scrape_catalog(
            "https://example.test/catalogue/", max_pages=1, delay=0
        )

        self.assertEqual(pages, 1)
        self.assertEqual(records, [])
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["stage"], "product")
        self.assertIn("timed out", errors[0]["error"].lower())


if __name__ == "__main__":
    unittest.main()