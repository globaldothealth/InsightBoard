from InsightBoard.database.db_base import (  # noqa: F401
    DatabaseBackend,
    DatabaseBackendVersion,
    WritePolicy,
    BackupPolicy,
    DatabaseBase,
)
from InsightBoard.database.db_parquet import DatabaseParquet, DatabaseParquetVersioned


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
            case _:
                raise ValueError(f"Backend '{backend}' not supported.")
