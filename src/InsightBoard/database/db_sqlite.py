import shutil
import sqlite3
import pandas as pd

from pathlib import Path
from datetime import datetime

from InsightBoard.database.db_base import (
    DatabaseBase,
    DatabaseBackend,
    BackupPolicy,
    WritePolicy,
)

DATABASE_SQLITE_VERSION = "1.0.0"


class DatabaseSQLite(DatabaseBase):
    def __init__(self, data_folder: str = ""):
        super().__init__(DatabaseBackend.SQLITE, data_folder)
        self.suffix = "db"
        self.db_version = DATABASE_SQLITE_VERSION
        self.db_filename = Path(self.data_folder) / "db.sqlite"

    # override
    def db_metadata(self):
        return {
            "version": self.db_version,
            "last_updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }

    # override
    def get_tables_list(self):
        if not self.db_filename.exists():
            return []
        else:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            return [table[0] for table in tables]

    # override
    def read_table(self, tablename: str) -> pd.DataFrame:
        conn = sqlite3.connect(self.db_filename)
        df = pd.read_sql_query(f"SELECT * FROM {tablename}", conn)
        conn.close()
        return df

    # override
    def read_table_column(self, tablename: str, column_name: str) -> pd.Series:
        return self.read_table(tablename)[column_name]

    # override
    def commit_table(self, tablename: str, df: pd.DataFrame):
        if len(df) == 0:
            return
        if not self.does_table_exist(tablename):
            # Create the table
            conn = sqlite3.connect(self.db_filename)
            primary_key = self.get_primary_key(tablename)
            if not primary_key:
                # Create a new table (without a primary key)
                self.write_table_create_no_primary_key(tablename, df, conn)
            else:
                # Create a new table (with a primary key)
                self.write_table_create_with_primary_key(
                    tablename, df, primary_key, conn
                )
        else:
            # Append or upsert into an existing table
            self.backup(self.db_filename)
            conn = sqlite3.connect(self.db_filename)
            if self.write_policy == WritePolicy.APPEND:
                self.write_table_append(tablename, df, conn)
            elif self.write_policy == WritePolicy.UPSERT:
                self.write_table_upsert(tablename, df, conn)
            else:
                raise ValueError(f"Invalid write policy: {self.write_policy}")

    # override
    def sql_query(self, query: str, tablename: str) -> pd.DataFrame:
        conn = sqlite3.connect(self.db_filename)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    # Utility functions

    def backup(self, file_path, backup_policy: BackupPolicy = None):
        backup_policy = backup_policy or self.backup_policy
        if backup_policy == BackupPolicy.TIMESTAMPED_COPIES:
            if not isinstance(file_path, Path):
                file_path = Path(file_path)
            backup_folder = Path(self.data_folder) / "backup"
            backup_folder.mkdir(parents=True, exist_ok=True)
            datetime_stamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            file_stem = file_path.stem
            shutil.copy(
                file_path,
                backup_folder / f"{file_stem}_{datetime_stamp}.{self.suffix}",
            )

    def does_table_exist(self, tablename: str):
        return tablename in self.get_tables_list()

    def write_table_create_no_primary_key(self, tablename: str, df: pd.DataFrame, conn):
        # Create a new table (without a primary key)
        df.to_sql(tablename, conn, index=False)

    def write_table_create_with_primary_key(
        self, tablename: str, df: pd.DataFrame, primary_key, conn
    ):
        # Create empty table (only column names and types)
        df_empty = df.iloc[0:0]
        df_empty.to_sql(f"_{tablename}", conn, index=False)
        # Prepare the table schema
        cursor = conn.execute(f"PRAGMA table_info(_{tablename})")
        columns_info = cursor.fetchall()
        columns = []
        for column_info in columns_info:
            col_name = column_info[1]
            col_type = column_info[2]
            if col_name == primary_key:
                columns.append(f'"{col_name}" {col_type} PRIMARY KEY')
            else:
                columns.append(f'"{col_name}" {col_type}')
        # Create the new table
        conn.execute(f"CREATE TABLE {tablename} ({', '.join(columns)})")
        conn.execute(f"DROP TABLE _{tablename}")
        # Populate table
        df.to_sql(tablename, conn, index=False, if_exists="append")

    def write_table_append(self, tablename: str, df: pd.DataFrame, conn):
        # Only add primary keys that are not already in the table
        for index, row in df.iterrows():
            columns = '"' + '", "'.join(row.index) + '"'
            placeholders = ", ".join("?" for _ in row)
            query = f"""
            INSERT OR IGNORE INTO {tablename} ({columns})
            VALUES ({placeholders})
            """
            conn.execute(query, tuple(row))
        conn.commit()

    def write_table_upsert(self, tablename: str, df: pd.DataFrame, conn):
        # Update the table with the new data
        primary_key = self.get_primary_key(tablename)
        for index, row in df.iterrows():
            columns = '"' + '", "'.join(row.index) + '"'
            placeholders = ", ".join("?" for _ in row)
            update_placeholders = ", ".join(
                f'"{col}"=excluded."{col}"' for col in row.index if col != primary_key
            )
            query = f"""
            INSERT INTO {tablename} ({columns})
            VALUES ({placeholders})
            ON CONFLICT("{primary_key}") DO UPDATE SET {update_placeholders}
            """
            conn.execute(query, tuple(row))
        conn.commit()
