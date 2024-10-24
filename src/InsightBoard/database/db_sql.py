import shutil
import logging
import numpy as np
import pandas as pd

from pathlib import Path
from datetime import datetime
from abc import abstractmethod

from InsightBoard.database.db_base import (
    DatabaseBase,
    BackupPolicy,
    WritePolicy,
)


# Abstract class for SQL databases
class DatabaseSQL(DatabaseBase):
    def __init__(self, backend, data_folder: str = ""):
        super().__init__(backend, data_folder)
        self.suffix = None
        self.db_version = None
        self.db_filename = None
        self.db_backend = None

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
            conn = self.db_backend.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            return [table[0] for table in tables]

    # override
    def read_table(self, tablename: str) -> pd.DataFrame:
        conn = self.db_backend.connect(self.db_filename)
        df = pd.read_sql_query(f"SELECT * FROM {tablename}", conn)
        conn.close()
        return df

    # override
    def read_table_column(self, tablename: str, column_name: str) -> pd.Series:
        conn = self.db_backend.connect(self.db_filename)
        df = pd.read_sql_query(f'SELECT "{column_name}" FROM {tablename}', conn)
        conn.close()
        return df

    # override
    def commit_table(self, tablename: str, df: pd.DataFrame):
        if len(df) == 0:
            return
        if not self.does_table_exist(tablename):
            # Create the table
            conn = self.db_backend.connect(self.db_filename)
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
            conn = self.db_backend.connect(self.db_filename)
            if self.write_policy == WritePolicy.APPEND:
                self.write_table_append(tablename, df, conn)
            elif self.write_policy == WritePolicy.UPSERT:
                self.write_table_upsert(tablename, df, conn)
            else:
                raise ValueError(f"Invalid write policy: {self.write_policy}")

    # override
    def sql_query(self, query: str, tablename: str) -> pd.DataFrame:
        conn = self.db_backend.connect(self.db_filename)
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
        logging.info("Creating table (no primary key): %s", tablename)
        self.initialise_table(tablename)
        df = df.replace({np.nan: None})
        df.to_sql(tablename, conn, index=False)

    def write_table_create_with_primary_key(
        self, tablename: str, df: pd.DataFrame, primary_key, conn
    ):
        # Create a new table (with a primary key)
        logging.info("Creating table (with primary key): %s", tablename)
        self.initialise_table(tablename)
        df = df.replace({np.nan: None})
        df.to_sql(tablename, conn, index=False, if_exists="append")

    def write_table_append(self, tablename: str, df: pd.DataFrame, conn):
        # Only add primary keys that are not already in the table
        logging.info("Appending to table: %s", tablename)
        df = df.replace({np.nan: None})
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
        logging.info("Upserting into table: %s", tablename)
        primary_key = self.get_primary_key(tablename)
        df = df.replace({np.nan: None})
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

    def initialise_table(self, tablename: str):
        conn = self.db_backend.connect(self.db_filename)
        schema = self.get_table_schema(tablename)
        columns = schema.get("properties", {})
        column_definitions = []
        for col_name, props in columns.items():
            sql_type = self.json_type_to_sql(props)
            col_def = f'"{col_name}" {sql_type}'
            if props.get("PrimaryKey", False):
                col_def += " PRIMARY KEY"
            column_definitions.append(col_def)
        sql_schema = ", ".join(column_definitions)
        conn.execute(f"CREATE TABLE {tablename} ({sql_schema});")
        conn.close()

    @abstractmethod
    def json_type_to_sql(self, props):
        pass  # pragma: no cover
