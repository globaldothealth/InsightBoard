import os
import json
import shutil
import sqlite3
import pandas as pd
import pyarrow.parquet as pq

from pathlib import Path
from pyarrow import Table
from datetime import datetime
from tempfile import NamedTemporaryFile

from InsightBoard.database.db_base import (
    DatabaseBackend,
    WritePolicy,
    BackupPolicy,
    DatabaseBase,
)


DATABASE_PARQUET_VERSION = ("1.0.0",)
DATABASE_PARQUET_VERSIONED_VERSION = "1.0.0"


class DatabaseParquet(DatabaseBase):
    def __init__(self, data_folder: str = ""):
        super().__init__(DatabaseBackend.PARQUET, data_folder)
        self.suffix = "parquet"
        self.db_version = DATABASE_PARQUET_VERSION

    # override
    def db_metadata(self):
        return {
            "version": self.db_version,
            "last_updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }

    # override
    def get_tables_list(self):
        if not os.path.exists(self.data_folder):
            return []
        return [
            f[: -len(self.suffix) - 1]
            for f in os.listdir(self.data_folder)
            if f.endswith(f".{self.suffix}")
        ]

    # override
    def read_table(self, table_name: str) -> pd.DataFrame:
        file_path = f"{self.data_folder}/{table_name}.{self.suffix}"
        table = pq.read_table(file_path)
        return table.to_pandas()

    # override
    def read_table_column(self, table_name: str, column_name: str) -> pd.Series:
        file_path = f"{self.data_folder}/{table_name}.{self.suffix}"
        table = pq.read_table(file_path)
        return table[column_name].to_pandas()

    # override
    def commit_table(self, table_name: str, df: pd.DataFrame):
        self.write_table_parquet(table_name, df)

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

    def write_table_parquet(
        self,
        table_name: str,
        df: pd.DataFrame,
        write_policy: WritePolicy = None,
        backup_policy: BackupPolicy = None,
    ):
        """Plain Parquet writer, no version history"""
        write_policy = write_policy or self.write_policy
        backup_policy = backup_policy or self.backup_policy
        if len(df) == 0:
            return
        file_path = Path(self.data_folder) / f"{table_name}.{self.suffix}"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        primary_key = self.get_primary_key(table_name)
        if primary_key and primary_key not in df.columns:
            raise ValueError(
                f"Primary key '{primary_key}' not found in new DataFrame columns."
            )
        if file_path.exists():
            old_df = pq.read_table(file_path).to_pandas()
            if not primary_key:
                # No primary key, just append the new data
                combined_df = self.dataframe_append(df, old_df, primary_key=None)
            else:
                match write_policy:
                    case WritePolicy.APPEND:
                        combined_df = self.dataframe_append(df, old_df, primary_key)
                    case WritePolicy.UPSERT:
                        combined_df = self.dataframe_upsert(df, old_df, primary_key)
                    case _:
                        raise ValueError(
                            f"Requested WritePolicy '{write_policy}' is not supported."
                        )
        else:
            # First time writing to the file
            combined_df = self.dataframe_new(df)
        # Write the updated DataFrame to the Parquet file
        table = Table.from_pandas(combined_df)
        table = table.replace_schema_metadata(self.db_metadata())  # Add metadata
        pq.write_table(table, file_path)
        # Create a timestamped version of the database as a backup
        self.backup(file_path)

    def dataframe_new(self, df):
        # Create a new DataFrame
        return df.copy()

    def dataframe_append(self, df, old_df, primary_key=None):
        if not primary_key:
            # Combine old and new DataFrames (no duplicate primary keys)
            return pd.concat([old_df, df], ignore_index=True)
        # Remove matching keys from the new DataFrame
        df = df[~df[primary_key].isin(old_df[primary_key])]
        # Combine old and new DataFrames (no duplicate primary keys)
        return pd.concat([old_df, df], ignore_index=True)

    def dataframe_upsert(self, df, old_df, primary_key):
        # Remove matching keys from old DataFrame
        old_df = old_df[~old_df[primary_key].isin(df[primary_key])]
        # Combine old and new DataFrames (no duplicate primary keys)
        return pd.concat([old_df, df], ignore_index=True)

    # override (DatabaseBase)
    def sql_query(self, query: str, tablename: str) -> pd.DataFrame:
        # Read the Parquet file into a Pandas DataFrame and transfer to SQLite
        #  (inefficient, but proof of concept)
        data = self.read_table(tablename)
        with NamedTemporaryFile(suffix=".db", delete=False) as tempfile:
            Path(tempfile.name).unlink()  # Remove the file if it exists
            conn = sqlite3.connect(tempfile.name)  # Create or connect
            data.to_sql(tablename, conn, if_exists="replace", index=False)
            # Run a SQL query on the SQLite database and close the connection
            df = pd.read_sql_query(query, conn)
            conn.close()
        Path(tempfile.name).unlink()
        return df


class DatabaseParquetVersioned(DatabaseParquet):
    def __init__(self, data_folder: str = ""):
        super().__init__(data_folder)
        self.BACKEND = DatabaseBackend.PARQUET_VERSIONED
        self.suffix = "ver.parquet"
        self.db_version = DATABASE_PARQUET_VERSIONED_VERSION

    # override (DatabaseBase)
    def read_table(self, table_name: str) -> pd.DataFrame:
        # Use DatabaseParquet implementation to read the table
        table = super().read_table(table_name)
        # Remove deleted records
        table = table[table["_deleted"] == False]  # noqa: E712
        # Return only the most recent version of each record
        table = table.sort_values(by=["_version"]).drop_duplicates(
            subset=self.get_primary_key(table_name), keep="last"
        )
        # Remove metadata columns
        table = table.drop(columns=["_version", "_deleted", "_metadata"])
        # Restore ordering
        table = table.sort_index()
        return table

    # override (DatabaseBase)
    def read_table_column(self, table_name: str, column_name: str) -> pd.Series:
        return self.read_table(table_name)[column_name]

    # Utility function
    def row_metadata(self, data: dict = None):
        # Convert metadata to JSON string
        if not data:
            data = {}
        data_required = {
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }
        data = {**data_required, **data}
        return json.dumps(data)

    # override (DatabaseParquet)
    def dataframe_new(self, df):
        # Add metadata columns to the new DataFrame
        df = df.copy()
        df.loc[:, ["_version"]] = 1
        df.loc[:, ["_deleted"]] = False
        df.loc[:, ["_metadata"]] = self.row_metadata()
        return df

    # override (DatabaseParquet)
    def dataframe_append(self, df, old_df, primary_key):
        # Remove matching keys from the new DataFrame
        df = df.copy()
        if primary_key:
            df = df[~df[primary_key].isin(old_df[primary_key])]
        # Combine old and new DataFrames (no duplicate primary keys)
        df.loc[:, ["_version"]] = 1
        df.loc[:, ["_deleted"]] = False
        df.loc[:, ["_metadata"]] = self.row_metadata()
        return pd.concat([old_df, df], ignore_index=True)

    # override (DatabaseParquet)
    def dataframe_upsert(self, df, old_df, primary_key):
        # Create new versions of existing records
        df = df.copy()
        #
        # Make a copy of the old data frame returning only the most recent version of each record
        filtered_old_df = old_df.sort_values(by=["_version"]).drop_duplicates(
            subset=primary_key, keep="last"
        )
        # Remove deleted records
        filtered_old_df = filtered_old_df[filtered_old_df["_deleted"] == False]  # noqa: E712
        # Remove new rows where:
        #  1. the primary key is already in the filtered (most recent) old DataFrame
        #  2. there is no change to the remaining row data
        data_columns = df.columns.difference(["_version", "_deleted", "_metadata"])
        for key in df[primary_key]:
            if key in filtered_old_df[primary_key].values:
                df1 = df.loc[df[primary_key] == key].reset_index(drop=True)
                df2 = filtered_old_df.loc[
                    filtered_old_df[primary_key] == key, data_columns
                ].reset_index(drop=True)
                if df1.equals(df2):
                    df = df[df[primary_key] != key]
        # Add metadata columns to the remaining DataFrame
        df.loc[:, ["_version"]] = 1
        df.loc[:, ["_deleted"]] = False
        df.loc[:, ["_metadata"]] = self.row_metadata()
        # Index on old_df (not filtered_old_df) to prevent skipping deleted records
        for key in df[primary_key]:
            if key in old_df[primary_key].values:
                df.loc[df[primary_key] == key, "_version"] = (
                    old_df.loc[old_df[primary_key] == key, "_version"].max() + 1
                )
        # Combine old and new DataFrames (versioned)
        return pd.concat([old_df, df], ignore_index=True)
