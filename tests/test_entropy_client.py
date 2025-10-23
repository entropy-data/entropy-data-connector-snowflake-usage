"""Tests for Entropy API client."""

import pytest
from unittest.mock import Mock, patch
from entropydata_connector.entropy_client import EntropyClient
from entropydata_connector.config import EntropyConfig


@pytest.fixture
def entropy_config():
    """Create test Entropy configuration."""
    return EntropyConfig(host="https://api.entropy-data.com", api_key="test-key")


@pytest.fixture
def entropy_client(entropy_config):
    """Create test Entropy client."""
    return EntropyClient(entropy_config)


def test_get_data_products_single_page(entropy_client):
    """Test fetching data products with a single page."""
    mock_response = Mock()
    mock_response.json.return_value = [
        {"kind": "DataProduct", "id": "dp-1", "name": "Product 1"},
        {"kind": "DataProduct", "id": "dp-2", "name": "Product 2"}
    ]
    mock_response.raise_for_status = Mock()

    with patch("requests.get", return_value=mock_response) as mock_get:
        products = list(entropy_client.get_data_products())

        assert len(products) == 2
        assert products[0]["id"] == "dp-1"
        assert products[1]["id"] == "dp-2"
        mock_get.assert_called_once()


def test_get_data_products_multiple_pages(entropy_client):
    """Test fetching data products with multiple pages."""
    page_1 = [{"kind": "DataProduct", "id": f"dp-{i}"} for i in range(100)]
    page_2 = [{"kind": "DataProduct", "id": f"dp-{i}"} for i in range(100, 150)]

    mock_responses = [Mock(), Mock()]
    mock_responses[0].json.return_value = page_1
    mock_responses[1].json.return_value = page_2

    for resp in mock_responses:
        resp.raise_for_status = Mock()

    with patch("requests.get", side_effect=mock_responses) as mock_get:
        products = list(entropy_client.get_data_products())

        assert len(products) == 150
        assert mock_get.call_count == 2


def test_filter_data_products(entropy_client):
    """Test filtering data products by kind."""
    data_products = [
        {"kind": "DataProduct", "id": "dp-1"},
        {"kind": "DataContract", "id": "dc-1"},
        {"kind": "DataProduct", "id": "dp-2"},
        {"kind": "Other", "id": "other-1"}
    ]

    filtered = list(entropy_client.filter_data_products(iter(data_products)))

    assert len(filtered) == 2
    assert filtered[0]["id"] == "dp-1"
    assert filtered[1]["id"] == "dp-2"


def test_send_traces(entropy_client):
    """Test sending traces to Entropy API."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()

    traces_payload = {
        "resourceSpans": [
            {
                "resource": {"attributes": []},
                "scopeSpans": [{"spans": []}]
            }
        ]
    }

    with patch("requests.post", return_value=mock_response) as mock_post:
        entropy_client.send_traces(traces_payload)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"] == traces_payload
        assert call_args[1]["headers"]["x-api-key"] == "test-key"
