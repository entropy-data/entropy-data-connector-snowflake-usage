"""Main orchestrator for Entropy Data Connector."""

import logging
from .config import Config
from .entropy_client import EntropyClient
from .snowflake_client import SnowflakeClient
from .output_port_parser import OutputPortParser
from .trace_mapper import TraceMapper
from .batch_processor import BatchProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EntropyConnector:
    """Main orchestrator for collecting and sending Snowflake usage data."""

    def __init__(self, config: Config):
        """Initialize the connector.

        Args:
            config: Configuration object
        """
        self.config = config
        self.entropy_client = EntropyClient(config.entropy)
        self.snowflake_client = SnowflakeClient(config.snowflake, config.filters)

    def run(self) -> None:
        """Execute the main connector workflow."""
        logger.info("Starting Entropy Data Connector")

        # Step 1: Fetch data products
        logger.info("Fetching data products from Entropy API")
        data_products = self.entropy_client.get_data_products(page_size=100)

        # Step 2: Filter to only DataProduct kind
        data_products = self.entropy_client.filter_data_products(data_products)

        # Step 3: Process each data product
        total_queries = 0
        total_batches = 0

        for data_product in data_products:
            data_product_id = data_product.get("id", "unknown")
            logger.info(f"Processing data product: {data_product_id}")

            # Step 4: Extract Snowflake configurations
            snowflake_configs = OutputPortParser.get_all_snowflake_configs(data_product)

            if not snowflake_configs:
                logger.debug(f"No Snowflake output ports found for {data_product_id}")
                continue

            # Step 5: Process each Snowflake output port
            for server_config in snowflake_configs:
                logger.info(
                    f"Querying Snowflake: {server_config.account}/{server_config.database}/{server_config.schema}"
                )

                try:
                    # Step 6: Fetch query history
                    queries = list(self.snowflake_client.get_query_history(server_config))
                    query_count = len(queries)
                    total_queries += query_count

                    logger.info(f"Found {query_count} queries for {server_config.output_port_name}")

                    if not queries:
                        continue

                    # Step 7: Batch queries (max 1000 per batch)
                    for batch in BatchProcessor.batch_list(queries, 1000):
                        # Step 8: Map to OTLP format
                        resource_spans = TraceMapper.create_resource_spans(batch, server_config)
                        traces_payload = TraceMapper.create_traces_payload([resource_spans])

                        # Step 9: Send to Entropy API
                        logger.info(f"Sending batch of {len(batch)} traces to Entropy API")
                        self.entropy_client.send_traces(traces_payload)
                        total_batches += 1

                except Exception as e:
                    logger.error(
                        f"Error processing {server_config.account}/{server_config.database}/{server_config.schema}: {e}",
                        exc_info=True
                    )
                    continue

        logger.info(f"Completed: Processed {total_queries} queries in {total_batches} batches")


def main():
    """Main entry point."""
    try:
        config = Config()
        connector = EntropyConnector(config)
        connector.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
