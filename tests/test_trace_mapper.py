"""Tests for trace mapper."""

import pytest
from datetime import datetime
from entropydata_connector.trace_mapper import TraceMapper
from entropydata_connector.output_port_parser import SnowflakeServerConfig


def test_generate_span_id():
    """Test that span ID generation is idempotent."""
    query_id = "01b2e3f4-5678-90ab-cdef-1234567890ab"

    span_id_1 = TraceMapper.generate_span_id(query_id)
    span_id_2 = TraceMapper.generate_span_id(query_id)

    assert span_id_1 == span_id_2
    assert len(span_id_1) == 16


def test_generate_span_id_different_queries():
    """Test that different query IDs produce different span IDs."""
    span_id_1 = TraceMapper.generate_span_id("query-1")
    span_id_2 = TraceMapper.generate_span_id("query-2")

    assert span_id_1 != span_id_2


def test_datetime_to_unix_nano():
    """Test datetime to Unix nanoseconds conversion."""
    dt = datetime(2024, 10, 15, 12, 0, 0)
    unix_nano = TraceMapper.datetime_to_unix_nano(dt)

    assert unix_nano > 0
    assert unix_nano == int(dt.timestamp() * 1_000_000_000)


def test_datetime_to_unix_nano_none():
    """Test conversion of None datetime."""
    assert TraceMapper.datetime_to_unix_nano(None) == 0


def test_map_query_to_span():
    """Test mapping Snowflake query to OTLP span."""
    query = {
        "QUERY_ID": "test-query-123",
        "QUERY_TEXT": "SELECT * FROM orders WHERE order_id = 1",
        "QUERY_TYPE": "SELECT",
        "USER_NAME": "test_user",
        "ROLE_NAME": "test_role",
        "WAREHOUSE_NAME": "test_warehouse",
        "START_TIME": datetime(2024, 10, 15, 12, 0, 0),
        "END_TIME": datetime(2024, 10, 15, 12, 0, 1),
        "EXECUTION_STATUS": "SUCCESS",
        "ROWS_PRODUCED": 100
    }

    server_config = SnowflakeServerConfig(
        account="test-account",
        database="test-db",
        schema="test-schema",
        data_product_id="dp-123",
        output_port_name="orders",
        output_port_version="1"
    )

    span = TraceMapper.map_query_to_span(query, server_config)

    assert span["name"] == "usage"
    assert span["kind"] == "SPAN_KIND_INTERNAL"
    assert span["traceId"] == span["spanId"]  # Must be equal
    assert span["startTimeUnixNano"] > 0
    assert span["endTimeUnixNano"] > span["startTimeUnixNano"]

    # Check attributes
    attrs = {attr["key"]: attr["value"] for attr in span["attributes"]}
    assert attrs["user"]["stringValue"] == "test_user"
    assert attrs["role"]["stringValue"] == "test_role"
    assert attrs["query.type"]["stringValue"] == "SELECT"
    assert attrs["result"]["stringValue"] == "SUCCESS"
    assert attrs["rows"]["intValue"] == 100


def test_create_resource_spans():
    """Test creating OTLP resourceSpans structure."""
    queries = [
        {
            "QUERY_ID": "query-1",
            "QUERY_TEXT": "SELECT 1",
            "QUERY_TYPE": "SELECT",
            "USER_NAME": "user1",
            "ROLE_NAME": "role1",
            "START_TIME": datetime.now(),
            "END_TIME": datetime.now(),
            "EXECUTION_STATUS": "SUCCESS",
            "ROWS_PRODUCED": 1
        }
    ]

    server_config = SnowflakeServerConfig(
        account="test-account",
        database="test-db",
        schema="test-schema",
        data_product_id="dp-123",
        output_port_name="orders",
        output_port_version="v1"
    )

    resource_spans = TraceMapper.create_resource_spans(queries, server_config)

    assert "resource" in resource_spans
    assert "scopeSpans" in resource_spans

    # Check resource attributes
    res_attrs = {attr["key"]: attr["value"]["stringValue"] for attr in resource_spans["resource"]["attributes"]}
    assert res_attrs["service.name"] == "snowflake"
    assert res_attrs["dataproduct.id"] == "dp-123"
    assert res_attrs["outputport.name"] == "orders"
    assert res_attrs["outputport.version"] == "v1"

    # Check spans
    assert len(resource_spans["scopeSpans"]) == 1
    assert resource_spans["scopeSpans"][0]["scope"]["name"] == "usage"
    assert len(resource_spans["scopeSpans"][0]["spans"]) == 1


def test_create_traces_payload():
    """Test creating complete OTLP traces payload."""
    resource_spans_list = [
        {"resource": {}, "scopeSpans": []},
        {"resource": {}, "scopeSpans": []}
    ]

    payload = TraceMapper.create_traces_payload(resource_spans_list)

    assert "resourceSpans" in payload
    assert len(payload["resourceSpans"]) == 2
