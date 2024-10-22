import pandas as pd

from InsightBoard.database.db_base import (
    DatabaseBase,
    DatabaseBackend,
)

DATABASE_DUCKDB_VERSION = "1.0.0"


class DatabaseDuckDB(DatabaseBase):
    def __init__(self, data_folder: str = ""):
        super().__init__(DatabaseBackend.DUCKDB, data_folder)
        self.suffix = "db"
        self.db_version = DATABASE_DUCKDB_VERSION

        raise NotImplementedError("DuckDB is not yet implemented.")

    def db_metadata(self):
        pass  # pragma: no cover

    def get_tables_list(self):
        pass  # pragma: no cover

    def read_table(self, table_name: str) -> pd.DataFrame:
        pass  # pragma: no cover

    def read_table_column(self, table_name: str, column_name: str) -> pd.Series:
        pass  # pragma: no cover

    def commit_table(self, table_name: str, df: pd.DataFrame):
        pass  # pragma: no cover

    def sql_query(self, query: str, tablename: str) -> pd.DataFrame:
        pass  # pragma: no cover
