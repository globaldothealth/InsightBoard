import os
import json
import shutil
import pandas as pd
import pyarrow.parquet as pq

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from pyarrow import Table
from datetime import datetime
from cachetools import cached, TTLCache


class DatabaseBackend(Enum):
    PARQUET = "parquet"


class WritePolicy(Enum):
    APPEND = "append"  # Append new data, do not overwrite existing records
    UPSERT = "upsert"  # Update existing records, insert new records


class BackupPolicy(Enum):
    NONE = "none"
    VERSIONED = "versioned"  # Versioned records are kept in the tables
    BACKUP = "backup"  # Backup the table before writing new data


class DatabaseBase(ABC):
    def __init__(
        self,
        backend: DatabaseBackend = DatabaseBackend.PARQUET,
        data_folder: str = "",
    ):
        self.BACKEND = backend
        self.data_folder = data_folder
        self.write_policy = WritePolicy.UPSERT
        self.backup_policy = BackupPolicy.NONE

    def set_write_policy(self, policy: WritePolicy):
        self.write_policy = policy

    def set_backup_policy(self, policy: BackupPolicy):
        self.backup_policy = policy

    def commit_tables_dict(self, table_names: [str], datasets: [dict]):
        if not isinstance(table_names, list):
            table_names = [table_names]
        if not isinstance(datasets, list):
            datasets = [datasets]
        if len(table_names) != len(datasets):
            raise ValueError(
                f"Length of table_names ({len(table_names)}) does not match length of "
                "datasets ({len(datasets)})"
            )
        for idx, data in enumerate(datasets):
            datasets[idx] = pd.DataFrame(data)
        self.commit_tables(table_names, datasets)

    def commit_tables(self, table_names: [str], datasets: [pd.DataFrame]):
        if not isinstance(table_names, list):
            table_names = [table_names]
        if not isinstance(datasets, list):
            datasets = [datasets]
        if len(table_names) != len(datasets):
            raise ValueError(
                f"Length of table_names ({len(table_names)}) does not match length of "
                "datasets ({len(datasets)})"
            )
        for table_name, df in zip(table_names, datasets, strict=True):
            self.commit_table(table_name, df)

    @cached(TTLCache(maxsize=1, ttl=10))
    def get_primary_key(self, table_name: str):
        schema = self.get_table_schema(table_name)
        # Find field that has the 'PrimaryKey' set to 'True'
        primary_key = None
        primary_key_count = 0
        for field_name, d in schema.get("properties", {}).items():
            if d.get("PrimaryKey", None):
                primary_key = field_name
                primary_key_count = primary_key_count + 1
        if primary_key_count > 1:
            raise ValueError(f"Table '{table_name}' has more than one primary key.")
        return primary_key

    @cached(TTLCache(maxsize=1, ttl=10))
    def get_primary_keys(self, table_name: str):
        primary_key = self.get_primary_key(table_name)
        if not primary_key:
            return []
        return self.read_table_column(table_name, primary_key).tolist()

    @cached(TTLCache(maxsize=1, ttl=10))
    def get_table_schema(self, table_name: str):
        schema_filename = (
            Path(self.data_folder).parent / "schemas" / f"{table_name}.schema.json"
        )
        try:
            with open(schema_filename, "r") as f:
                schema = json.load(f)
        except FileNotFoundError:
            return {}
        return schema

    @abstractmethod
    def get_tables_list(self):
        pass  # pragma: no cover

    @abstractmethod
    def read_table(self, table_name: str) -> pd.DataFrame:
        pass  # pragma: no cover

    @abstractmethod
    def read_table_column(self, table_name: str, column_name: str) -> pd.Series:
        pass  # pragma: no cover

    @abstractmethod
    def commit_table(self, table_name: str, df: pd.DataFrame):
        pass  # pragma: no cover


class DatabaseParquet(DatabaseBase):
    def __init__(self, data_folder: str = ""):
        super().__init__(DatabaseBackend.PARQUET, data_folder)

    # override
    def get_tables_list(self):
        if not os.path.exists(self.data_folder):
            return []
        return [
            ".".join(f.split(".")[:-1])
            for f in os.listdir(self.data_folder)
            if f.endswith(".parquet")
        ]

    # override
    def read_table(self, table_name: str) -> pd.DataFrame:
        file_path = f"{self.data_folder}/{table_name}.parquet"
        table = pq.read_table(file_path)
        return table.to_pandas()

    # override
    def read_table_column(self, table_name: str, column_name: str) -> pd.Series:
        file_path = f"{self.data_folder}/{table_name}.parquet"
        table = pq.read_table(file_path)
        return table[column_name].to_pandas()

    # override
    def commit_table(self, table_name: str, df: pd.DataFrame):
        self.write_table_parquet(table_name, df)

    # Utility functions

    def backup(self, file_path, backup_policy: BackupPolicy = None):
        backup_policy = backup_policy or self.backup_policy
        if backup_policy == BackupPolicy.BACKUP:
            backup_folder = Path(self.data_folder) / "backup"
            backup_folder.mkdir(parents=True, exist_ok=True)
            datetime_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            shutil.copy(file_path, f"{file_path.stem}_{datetime_stamp}_.backup")

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
        file_path = Path(self.data_folder) / f"{table_name}.parquet"
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
                combined_df = pd.concat([old_df, df], ignore_index=True)
            if primary_key not in df.columns:
                raise ValueError(
                    f"Critical error - primary key '{primary_key}' not found in existing database."
                )
            match write_policy:
                case WritePolicy.APPEND:
                    # Remove matching keys from the new DataFrame
                    df = df[~df[primary_key].isin(old_df[primary_key])]
                    # Combine old and new DataFrames (no duplicate primary keys)
                    combined_df = pd.concat([old_df, df], ignore_index=True)
                case WritePolicy.UPSERT:
                    # Remove matching keys from old DataFrame
                    old_df = old_df[~old_df[primary_key].isin(df[primary_key])]
                    # Combine old and new DataFrames (no duplicate primary keys)
                    combined_df = pd.concat([old_df, df], ignore_index=True)
                case _:
                    raise ValueError(
                        f"Requested WritePolicy '{write_policy}' is not supported."
                    )
        else:
            # First time writing to the file
            combined_df = df
        # Write the updated DataFrame to the Parquet file
        table = Table.from_pandas(combined_df)
        pq.write_table(table, file_path)
        # Create a timestamped version of the database as a backup
        self.backup(file_path)


class Database:
    def __new__(
        self,
        backend: DatabaseBackend = DatabaseBackend.PARQUET,
        data_folder: str = "",
    ):
        if backend == DatabaseBackend.PARQUET:
            return DatabaseParquet(data_folder)
        else:
            raise ValueError(f"Backend '{backend}' not supported.")
