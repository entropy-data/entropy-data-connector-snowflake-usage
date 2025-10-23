"""Parser for extracting Snowflake output port information."""

from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class SnowflakeServerConfig:
    """Snowflake server configuration extracted from output port."""

    account: str
    database: str
    schema: str
    data_product_id: str
    output_port_name: str
    output_port_version: str


class OutputPortParser:
    """Parser for extracting Snowflake configuration from data product output ports."""

    @staticmethod
    def get_snowflake_output_ports(data_product: dict[str, Any]) -> list[dict[str, Any]]:
        """Filter output ports to only Snowflake ports.

        Args:
            data_product: Data product dictionary

        Returns:
            List of Snowflake output ports
        """
        output_ports = data_product.get("outputPorts", [])
        return [port for port in output_ports if port.get("type") == "snowflake"]

    @staticmethod
    def extract_server_config(
        data_product: dict[str, Any],
        output_port: dict[str, Any]
    ) -> Optional[SnowflakeServerConfig]:
        """Extract Snowflake server configuration from output port.

        Args:
            data_product: Data product dictionary
            output_port: Output port dictionary

        Returns:
            SnowflakeServerConfig if valid configuration found, None otherwise
        """
        custom_properties = output_port.get("customProperties", [])

        # Find the 'server' property
        server_value = None
        for prop in custom_properties:
            if prop.get("property") == "server":
                server_value = prop.get("value")
                break

        if not server_value:
            return None

        # Extract required fields
        account = server_value.get("account")
        database = server_value.get("database")
        schema = server_value.get("schema")

        if not all([account, database, schema]):
            return None

        return SnowflakeServerConfig(
            account=account,
            database=database,
            schema=schema,
            data_product_id=data_product.get("id", ""),
            output_port_name=output_port.get("name", ""),
            output_port_version=output_port.get("version", "")
        )

    @staticmethod
    def get_all_snowflake_configs(data_product: dict[str, Any]) -> list[SnowflakeServerConfig]:
        """Get all valid Snowflake configurations from a data product.

        Args:
            data_product: Data product dictionary

        Returns:
            List of SnowflakeServerConfig objects
        """
        configs = []
        snowflake_ports = OutputPortParser.get_snowflake_output_ports(data_product)

        for port in snowflake_ports:
            config = OutputPortParser.extract_server_config(data_product, port)
            if config:
                configs.append(config)

        return configs
