"""Client for Entropy Data API."""

import requests
from typing import Iterator, Optional, Any
from .config import EntropyConfig


class EntropyClient:
    """Client for interacting with Entropy Data API."""

    def __init__(self, config: EntropyConfig):
        """Initialize the Entropy API client.

        Args:
            config: Entropy API configuration
        """
        self.config = config
        self.base_url = config.host.rstrip("/")
        self.headers = {
            "x-api-key": config.api_key,
            "Content-Type": "application/json"
        }

    def get_data_products(self, page_size: int = 100) -> Iterator[dict[str, Any]]:
        """Fetch all data products with pagination.

        Args:
            page_size: Number of items per page (default: 100)

        Yields:
            Data product dictionaries
        """
        page = 0
        while True:
            response = requests.get(
                f"{self.base_url}/api/dataproducts",
                headers=self.headers,
                params={"p": page},
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            # Handle both array response and paginated response
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict) and "items" in data:
                items = data["items"]
            else:
                items = [data] if data else []

            if not items:
                break

            for item in items:
                yield item

            # If we got fewer items than page_size, we've reached the end
            if len(items) < page_size:
                break

            page += 1

    def filter_data_products(self, data_products: Iterator[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        """Filter data products to only include kind='DataProduct'.

        Args:
            data_products: Iterator of data product dictionaries

        Yields:
            Filtered data product dictionaries
        """
        for dp in data_products:
            if dp.get("kind") == "DataProduct":
                yield dp

    def send_traces(self, traces_payload: dict[str, Any]) -> None:
        """Send traces to Entropy Data API.

        Args:
            traces_payload: OTLP traces payload

        Raises:
            requests.HTTPError: If the request fails
        """
        response = requests.post(
            f"{self.base_url}/api/v1/traces",
            headers=self.headers,
            json=traces_payload,
            timeout=30
        )
        response.raise_for_status()
