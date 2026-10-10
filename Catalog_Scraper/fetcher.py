"""HTTP fetching helpers for the Catalog Scraper."""

import requests


def fetch_page(url: str, timeout: float = 10) -> requests.Response:
    """Fetch one page, raising a Requests exception for network/HTTP errors."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response
