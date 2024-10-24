import logging

from pathlib import Path

from InsightBoard.database.db_sql import DatabaseSQL
from InsightBoard.database.db_base import DatabaseBackend

try:
    import duckdb
except ImportError:
    duckdb = None

DATABASE_DUCKDB_VERSION = "1.0.0"


class DatabaseDuckDB(DatabaseSQL):
    def __init__(self, data_folder: str = ""):
        super().__init__(DatabaseBackend.DUCKDB, data_folder)
        self.suffix = "db"
        self.db_version = DATABASE_DUCKDB_VERSION
        self.db_filename = Path(self.data_folder) / "db.duckdb"

        if not duckdb:
            raise ImportError(
                "DuckDB is not installed, "
                "but is available as an optional dependency. "
                "Please install it using 'pip install \"insightboard[duckdb]\"'."
            )
        self.db_backend = duckdb

    # override
    def json_type_to_sql(self, props):
        if "enum" in props:
            return "TEXT"
        json_types = props.get("type", ["string"])
        if not isinstance(json_types, list):
            json_types = [json_types]
        json_format = props.get("format", "")

        def base_type(json_types):
            if "string" in json_types and json_format in ["date"]:
                return "DATE"
            elif "string" in json_types and json_format in ["date-time"]:
                return "TIMESTAMP"
            elif "string" in json_types and json_format in ["time"]:
                return "TIME"
            elif "string" in json_types and json_format in ["uuid"]:
                return "TEXT"
            elif "string" in json_types:
                return "TEXT"
            elif "integer" in json_types:
                return "INTEGER"
            elif "number" in json_types:
                return "REAL"
            elif "boolean" in json_types:
                return "BOOLEAN"
            elif "array" in json_types:
                return "TEXT"  # Could use ARRAY here
            else:
                logging.warn(f"Unsupported JSON type: {json_types}, defaulting to TEXT")
                return "TEXT"

        # Check for nullability
        sql_type = base_type(json_types)
        if "null" in json_types:
            sql_type = f"{sql_type} NULL"
        return sql_type
