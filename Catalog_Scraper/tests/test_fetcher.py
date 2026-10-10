import unittest
from unittest.mock import Mock, patch

import requests

from fetcher import fetch_page


class FetcherTests(unittest.TestCase):
    @patch("fetcher.requests.get")
    def test_successful_request_returns_response(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        result = fetch_page("https://example.test/page")

        self.assertIs(result, response)
        mock_get.assert_called_once_with(
            "https://example.test/page", timeout=10
        )
        response.raise_for_status.assert_called_once()

    @patch("fetcher.requests.get")
    def test_http_error_is_propagated(self, mock_get):
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = response

        with self.assertRaises(requests.HTTPError):
            fetch_page("https://example.test/missing")

    @patch("fetcher.requests.get")
    def test_timeout_is_propagated(self, mock_get):
        mock_get.side_effect = requests.Timeout("Request timed out")

        with self.assertRaises(requests.Timeout):
            fetch_page("https://example.test/slow")


if __name__ == "__main__":
    unittest.main()