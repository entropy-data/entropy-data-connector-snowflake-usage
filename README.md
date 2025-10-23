# Entropy Data Connector - Snowflake Usage Tracking

A Python connector that extracts Snowflake query history and sends usage traces to Entropy Data API.

For more information about usage tracking in Entropy Data, see the [Usage Tracking documentation](https://docs.entropy-data.com/howto/usage).

## Features

- Fetches data products from Entropy Data API with pagination
- Filters for Snowflake output ports
- Queries Snowflake ACCOUNT_USAGE.QUERY_HISTORY for the last 30 days
- Filters queries by users, roles, and warehouses
- Sanitizes sensitive information from queries
- Generates idempotent trace/span IDs from query IDs
- Batches traces (max 1000 per POST request)
- Sends usage data as OpenTelemetry traces to Entropy Data API

## Installation

```bash
# Sync dependencies and install the package
uv sync

# Or install with development dependencies explicitly
uv sync --extra dev
```

## Configuration

### Snowflake Permissions

The Snowflake user needs access to the `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` view. Grant the necessary privileges:

```sql
-- Create a custom role for the connector
CREATE ROLE IF NOT EXISTS ENTROPY_CONNECTOR_ROLE;

-- Grant access to ACCOUNT_USAGE views
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE ENTROPY_CONNECTOR_ROLE;

-- Grant the role to your user
GRANT ROLE ENTROPY_CONNECTOR_ROLE TO USER your_snowflake_username;

-- Optionally, grant access to a warehouse
GRANT USAGE ON WAREHOUSE your_warehouse_name TO ROLE ENTROPY_CONNECTOR_ROLE;
```

**Note**: The `ACCOUNT_USAGE` views have a data latency of 45 minutes to 3 hours and retain query history for 1 year.

### Environment Variables

Create a `.env` file in the project root (see `.env.example`):

```bash
# Entropy Data API Configuration
ENTROPY_HOST=https://api.entropy-data.com
ENTROPY_API_KEY=your-api-key-here

# Snowflake Configuration
SNOWFLAKE_USER=your-snowflake-username
SNOWFLAKE_PASSWORD=your-snowflake-password
SNOWFLAKE_ROLE=ENTROPY_CONNECTOR_ROLE
SNOWFLAKE_WAREHOUSE=your-warehouse-name

# Filtering Configuration (comma-separated)
EXCLUDE_USERS=SYSTEM_USER,ADMIN_USER
EXCLUDE_ROLES=SYSADMIN,SECURITYADMIN
EXCLUDE_WAREHOUSES=

# Query Configuration
QUERY_DAYS_BACK=30
```

## Usage

Run the connector:

```bash
entropydata-connector-snowflake-usage
```

Or run directly with Python:

```bash
python -m entropydata_connector.main
```

## Running Tests

```bash
uv run pytest
```

## How It Works

1. **Fetch Data Products**: Retrieves all data products from Entropy Data API (paginated, 100 per page)
2. **Filter by Kind**: Only processes data products with `kind: "DataProduct"`
3. **Extract Snowflake Configs**: Identifies Snowflake output ports and extracts server configuration (account, database, schema)
4. **Query History**: Connects to each Snowflake account and queries `ACCOUNT_USAGE.QUERY_HISTORY`
5. **Apply Filters**: Excludes queries from specified users, roles, and warehouses
6. **Sanitize Queries**: Removes sensitive information (passwords, API keys, etc.) from query text
7. **Generate IDs**: Creates idempotent `traceId` and `spanId` (both equal) from Snowflake `QUERY_ID`
8. **Batch Processing**: Groups queries into batches of 1000
9. **Send Traces**: Sends batches to Entropy Data API as OpenTelemetry traces

## Project Structure

```
src/entropydata_connector/
├── __init__.py
├── config.py              # Configuration management
├── entropy_client.py      # Entropy Data API client
├── snowflake_client.py    # Snowflake query history client
├── output_port_parser.py  # Parser for extracting Snowflake configs
├── query_sanitizer.py     # Query sanitization
├── trace_mapper.py        # OTLP trace mapping
├── batch_processor.py     # Batching logic
└── main.py               # Main orchestrator

tests/
├── test_entropy_client.py
├── test_output_port_parser.py
├── test_query_sanitizer.py
└── test_trace_mapper.py
```

## Requirements

- Python >= 3.13
- Snowflake connector
- Requests library
- python-dotenv

## License

[Your License Here]
