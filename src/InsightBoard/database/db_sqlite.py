import sqlite3
import logging

from pathlib import Path

from InsightBoard.database.db_sql import DatabaseSQL
from InsightBoard.database.db_base import DatabaseBackend

DATABASE_SQLITE_VERSION = "1.0.0"


class DatabaseSQLite(DatabaseSQL):
    def __init__(self, data_folder: str = ""):
        super().__init__(DatabaseBackend.SQLITE, data_folder)
        self.suffix = "db"
        self.db_version = DATABASE_SQLITE_VERSION
        self.db_filename = Path(self.data_folder) / "db.sqlite"
        self.db_backend = sqlite3

    # override
    def json_type_to_sql(self, props):
        if "enum" in props:
            return "TEXT"
        json_types = props.get("type", ["string"])
        if not isinstance(json_types, list):
            json_types = [json_types]

        def base_type(json_types):
            if "string" in json_types:
                # Note that SQLite does not support json string 'format's (e.g. 'date-time')
                return "TEXT"
            elif "integer" in json_types:
                return "INTEGER"
            elif "number" in json_types:
                return "REAL"
            elif "boolean" in json_types:
                return "TEXT"  # SQLite does not have a native boolean type
            elif "array" in json_types:
                return "TEXT"  # SQLite does not have a native array type
            else:
                logging.warn(f"Unsupported JSON type: {json_types}, defaulting to TEXT")
                return "TEXT"

        # Check for nullability
        sql_type = base_type(json_types)
        if self.field_is_nullable(props):
            sql_type = f"{sql_type} NULL"
        return sql_type
