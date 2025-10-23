"""Mapper for converting Snowflake query history to OTLP traces."""

import hashlib
from datetime import datetime
from typing import Any, Optional
from .output_port_parser import SnowflakeServerConfig
from .query_sanitizer import QuerySanitizer


class TraceMapper:
    """Maps Snowflake query history to OTLP trace format."""

    @staticmethod
    def generate_span_id(query_id: str) -> str:
        """Generate idempotent spanId and traceId from QUERY_ID.

        Args:
            query_id: Snowflake QUERY_ID

        Returns:
            16-character hex string for both spanId and traceId
        """
        # Hash the query_id to get a deterministic value
        hash_obj = hashlib.sha256(query_id.encode())
        # Take first 16 hex characters (8 bytes)
        return hash_obj.hexdigest()[:16]

    @staticmethod
    def datetime_to_unix_nano(dt: Optional[datetime]) -> int:
        """Convert datetime to Unix nanoseconds.

        Args:
            dt: Datetime object

        Returns:
            Unix timestamp in nanoseconds
        """
        if not dt:
            return 0
        return int(dt.timestamp() * 1_000_000_000)

    @staticmethod
    def map_query_to_span(
        query: dict[str, Any],
        server_config: SnowflakeServerConfig
    ) -> dict[str, Any]:
        """Map a single Snowflake query to an OTLP span.

        Args:
            query: Query history record
            server_config: Snowflake server configuration

        Returns:
            OTLP span dictionary
        """
        query_id = query.get("QUERY_ID", "")
        span_id = TraceMapper.generate_span_id(query_id)

        # Calculate row count based on query type
        rows = 0
        if query.get("QUERY_TYPE") == "SELECT":
            rows = query.get("ROWS_PRODUCED", 0) or 0
        elif query.get("QUERY_TYPE") == "INSERT":
            rows = query.get("ROWS_INSERTED", 0) or 0
        elif query.get("QUERY_TYPE") == "UPDATE":
            rows = query.get("ROWS_UPDATED", 0) or 0
        elif query.get("QUERY_TYPE") == "DELETE":
            rows = query.get("ROWS_DELETED", 0) or 0

        # Determine result status
        execution_status = query.get("EXECUTION_STATUS", "")
        result = "SUCCESS" if execution_status == "SUCCESS" else execution_status

        # Build span attributes
        attributes = [
            {"key": "user", "value": {"stringValue": query.get("USER_NAME", "")}},
            {"key": "role", "value": {"stringValue": query.get("ROLE_NAME", "")}},
            {"key": "query.type", "value": {"stringValue": query.get("QUERY_TYPE", "")}},
            {
                "key": "query.preview",
                "value": {"stringValue": QuerySanitizer.create_preview(query.get("QUERY_TEXT"))}
            },
            {"key": "result", "value": {"stringValue": result}},
            {"key": "rows", "value": {"intValue": rows}},
        ]

        # Add optional attributes
        if query.get("WAREHOUSE_NAME"):
            attributes.append({
                "key": "warehouse",
                "value": {"stringValue": query.get("WAREHOUSE_NAME")}
            })

        if query.get("ERROR_MESSAGE"):
            attributes.append({
                "key": "error.message",
                "value": {"stringValue": query.get("ERROR_MESSAGE", "")}
            })

        return {
            "traceId": span_id,  # traceId = spanId as per requirements
            "spanId": span_id,
            "name": "usage",
            "kind": "SPAN_KIND_INTERNAL",
            "startTimeUnixNano": TraceMapper.datetime_to_unix_nano(query.get("START_TIME")),
            "endTimeUnixNano": TraceMapper.datetime_to_unix_nano(query.get("END_TIME")),
            "attributes": attributes
        }

    @staticmethod
    def create_resource_spans(
        queries: list[dict[str, Any]],
        server_config: SnowflakeServerConfig
    ) -> dict[str, Any]:
        """Create OTLP resourceSpans structure.

        Args:
            queries: List of query history records
            server_config: Snowflake server configuration

        Returns:
            OTLP resourceSpans dictionary
        """
        # Map all queries to spans
        spans = [
            TraceMapper.map_query_to_span(query, server_config)
            for query in queries
        ]

        return {
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": "snowflake"}},
                    {"key": "dataproduct.id", "value": {"stringValue": server_config.data_product_id}},
                    {"key": "outputport.name", "value": {"stringValue": server_config.output_port_name}},
                    {"key": "outputport.version", "value": {"stringValue": server_config.output_port_version}}
                ]
            },
            "scopeSpans": [
                {
                    "scope": {
                        "name": "usage",
                        "version": "1.0.0"
                    },
                    "spans": spans
                }
            ]
        }

    @staticmethod
    def create_traces_payload(resource_spans_list: list[dict[str, Any]]) -> dict[str, Any]:
        """Create complete OTLP traces payload.

        Args:
            resource_spans_list: List of resourceSpans

        Returns:
            Complete OTLP traces payload
        """
        return {
            "resourceSpans": resource_spans_list
        }
