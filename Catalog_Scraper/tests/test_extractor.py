import unittest

from extractor import parse_listing, parse_product


LISTING_HTML = """
<html><body>
<article class="product_pod">
  <h3>
    <a href="example-book_1/index.html" title="Example Book">Example...</a>
  </h3>
</article>
<ul class="pager">
  <li class="next"><a href="page-2.html">next</a></li>
</ul>
</body></html>
"""

PRODUCT_HTML = """
<html><body>
<ul class="breadcrumb">
  <li><a>Home</a></li><li><a>Books</a></li><li><a>Poetry</a></li><li>Example Book</li>
</ul>
<div class="product_main">
  <h1>Example Book</h1>
  <p class="price_color">£12.34</p>
  <p class="star-rating Three"><i>Rating</i></p>
  <p class="instock availability"> In stock (5 available) </p>
</div>
</body></html>
"""


class ExtractorTests(unittest.TestCase):
    def test_listing_extracts_absolute_product_and_next_urls(self):
        books, next_url = parse_listing(LISTING_HTML, "https://example.test/catalogue/page-1.html")
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0]["product_url"],
                         "https://example.test/catalogue/example-book_1/index.html")
        self.assertEqual(next_url, "https://example.test/catalogue/page-2.html")

    def test_product_extracts_six_fields(self):
        book = parse_product(PRODUCT_HTML, "https://example.test/book")
        self.assertEqual(book["title"], "Example Book")
        self.assertEqual(book["price"], "12.34")
        self.assertEqual(book["availability"], "In stock (5 available)")
        self.assertEqual(book["rating"], "Three")
        self.assertEqual(book["category"], "Poetry")
        self.assertEqual(book["product_url"], "https://example.test/book")

    def test_missing_required_fields_raise_clear_error(self):
        with self.assertRaisesRegex(ValueError, "Missing required product fields"):
            parse_product("<html><body></body></html>", "https://example.test/book")


if __name__ == "__main__":
    unittest.main()
