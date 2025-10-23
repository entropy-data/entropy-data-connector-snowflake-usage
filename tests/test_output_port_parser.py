"""Tests for output port parser."""

import pytest
from entropydata_connector.output_port_parser import OutputPortParser, SnowflakeServerConfig


def test_get_snowflake_output_ports():
    """Test filtering Snowflake output ports."""
    data_product = {
        "id": "dp-1",
        "outputPorts": [
            {"name": "s3", "type": "s3"},
            {"name": "snowflake", "type": "snowflake"},
            {"name": "postgres", "type": "postgres"},
            {"name": "snowflake2", "type": "snowflake"}
        ]
    }

    snowflake_ports = OutputPortParser.get_snowflake_output_ports(data_product)

    assert len(snowflake_ports) == 2
    assert snowflake_ports[0]["name"] == "snowflake"
    assert snowflake_ports[1]["name"] == "snowflake2"


def test_extract_server_config():
    """Test extracting Snowflake server configuration."""
    data_product = {
        "id": "11e8c526-a61a-426f-b2e2-d63b52476ad8",
        "name": "Webshop Orders"
    }

    output_port = {
        "name": "snowflake",
        "version": "1",
        "type": "snowflake",
        "customProperties": [
            {
                "property": "server",
                "value": {
                    "schema": "OP_WEBSHOP_ORDERS_PII_V1",
                    "account": "lmtrwxs-xn14859",
                    "database": "DP_WEBSHOP_ORDERS"
                }
            }
        ]
    }

    config = OutputPortParser.extract_server_config(data_product, output_port)

    assert config is not None
    assert config.account == "lmtrwxs-xn14859"
    assert config.database == "DP_WEBSHOP_ORDERS"
    assert config.schema == "OP_WEBSHOP_ORDERS_PII_V1"
    assert config.data_product_id == "11e8c526-a61a-426f-b2e2-d63b52476ad8"
    assert config.output_port_name == "snowflake"
    assert config.output_port_version == "1"


def test_extract_server_config_missing_server_property():
    """Test extraction when server property is missing."""
    data_product = {"id": "dp-1"}
    output_port = {
        "name": "snowflake",
        "type": "snowflake",
        "customProperties": [
            {"property": "other", "value": "something"}
        ]
    }

    config = OutputPortParser.extract_server_config(data_product, output_port)
    assert config is None


def test_extract_server_config_incomplete_data():
    """Test extraction when server config is incomplete."""
    data_product = {"id": "dp-1"}
    output_port = {
        "name": "snowflake",
        "type": "snowflake",
        "customProperties": [
            {
                "property": "server",
                "value": {
                    "account": "test-account"
                    # Missing database and schema
                }
            }
        ]
    }

    config = OutputPortParser.extract_server_config(data_product, output_port)
    assert config is None


def test_get_all_snowflake_configs():
    """Test getting all Snowflake configurations from a data product."""
    data_product = {
        "id": "dp-1",
        "outputPorts": [
            {
                "name": "snowflake1",
                "version": "1",
                "type": "snowflake",
                "customProperties": [
                    {
                        "property": "server",
                        "value": {
                            "account": "acc1",
                            "database": "db1",
                            "schema": "schema1"
                        }
                    }
                ]
            },
            {
                "name": "s3",
                "type": "s3"
            },
            {
                "name": "snowflake2",
                "version": "2",
                "type": "snowflake",
                "customProperties": [
                    {
                        "property": "server",
                        "value": {
                            "account": "acc2",
                            "database": "db2",
                            "schema": "schema2"
                        }
                    }
                ]
            }
        ]
    }

    configs = OutputPortParser.get_all_snowflake_configs(data_product)

    assert len(configs) == 2
    assert configs[0].account == "acc1"
    assert configs[1].account == "acc2"
