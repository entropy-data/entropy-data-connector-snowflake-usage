"""Client for querying Snowflake query history."""

import snowflake.connector
from datetime import datetime, timedelta
from typing import Iterator, Optional, Any
from .config import SnowflakeConfig, FilterConfig
from .output_port_parser import SnowflakeServerConfig


class SnowflakeClient:
    """Client for querying Snowflake query history."""

    QUERY_HISTORY_SQL = """
        SELECT
            QUERY_ID,
            QUERY_TEXT,
            QUERY_TYPE,
            QUERY_TAG,
            DATABASE_ID,
            DATABASE_NAME,
            SCHEMA_ID,
            SCHEMA_NAME,
            SESSION_ID,
            USER_NAME,
            ROLE_NAME,
            WAREHOUSE_ID,
            WAREHOUSE_NAME,
            WAREHOUSE_SIZE,
            WAREHOUSE_TYPE,
            START_TIME,
            END_TIME,
            TOTAL_ELAPSED_TIME,
            BYTES_SCANNED,
            ROWS_PRODUCED,
            ROWS_INSERTED,
            ROWS_UPDATED,
            ROWS_DELETED,
            ROWS_UNLOADED,
            CREDITS_USED_CLOUD_SERVICES,
            EXECUTION_STATUS,
            ERROR_CODE,
            ERROR_MESSAGE
        FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
        WHERE DATABASE_NAME = %s
            AND SCHEMA_NAME = %s
            AND START_TIME >= TO_TIMESTAMP_LTZ(%s)
        ORDER BY START_TIME DESC
        LIMIT 10000
    """

    def __init__(self, config: SnowflakeConfig, filter_config: FilterConfig):
        """Initialize the Snowflake client.

        Args:
            config: Snowflake connection configuration
            filter_config: Configuration for filtering queries
        """
        self.config = config
        self.filter_config = filter_config

    def get_query_history(
        self,
        server_config: SnowflakeServerConfig
    ) -> Iterator[dict[str, Any]]:
        """Fetch query history for a specific database/schema.

        Args:
            server_config: Snowflake server configuration

        Yields:
            Query history records as dictionaries
        """
        # Calculate start time (convert to epoch seconds for Snowflake)
        start_time = datetime.now() - timedelta(days=self.filter_config.days_back)
        start_time_epoch = int(start_time.timestamp())

        # Connect to Snowflake
        conn = snowflake.connector.connect(
            user=self.config.user,
            password=self.config.password,
            account=server_config.account,
            role=self.config.role,
            warehouse=self.config.warehouse
        )

        try:
            cursor = conn.cursor(snowflake.connector.DictCursor)
            cursor.execute(
                self.QUERY_HISTORY_SQL,
                (server_config.database, server_config.schema, start_time_epoch)
            )

            for row in cursor:
                # Apply filters
                if self._should_exclude_query(row):
                    continue

                yield dict(row)

        finally:
            conn.close()

    def _should_exclude_query(self, query: dict[str, Any]) -> bool:
        """Check if a query should be excluded based on filters.

        Args:
            query: Query record dictionary

        Returns:
            True if query should be excluded, False otherwise
        """
        user_name = query.get("USER_NAME", "")
        role_name = query.get("ROLE_NAME", "")
        warehouse_name = query.get("WAREHOUSE_NAME", "")

        if user_name in self.filter_config.exclude_users:
            return True

        if role_name in self.filter_config.exclude_roles:
            return True

        if warehouse_name in self.filter_config.exclude_warehouses:
            return True

        return False
