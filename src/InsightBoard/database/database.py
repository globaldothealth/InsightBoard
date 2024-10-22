from InsightBoard.database.db_base import (  # noqa: F401
    DatabaseBackend,
    WritePolicy,
    BackupPolicy,
    DatabaseBase,
)
from InsightBoard.database.db_parquet import DatabaseParquet, DatabaseParquetVersioned
from InsightBoard.database.db_sqlite import DatabaseSQLite
from InsightBoard.database.db_duckdb import DatabaseDuckDB


class Database:
    def __new__(
        self,
        backend: DatabaseBackend = DatabaseBackend.PARQUET,
        data_folder: str = "",
    ):
        match backend:
            case DatabaseBackend.PARQUET:
                return DatabaseParquet(data_folder)
            case DatabaseBackend.PARQUET_VERSIONED:
                return DatabaseParquetVersioned(data_folder)
            case DatabaseBackend.SQLITE:
                return DatabaseSQLite(data_folder)
            case DatabaseBackend.DUCKDB:
                return DatabaseDuckDB(data_folder)
            case _:
                raise ValueError(f"Backend '{backend}' not supported.")
