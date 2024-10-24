import json
import pandas as pd

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from cachetools import cached, TTLCache


class DatabaseBackend(Enum):
    DEFAULT = "parquet"
    PARQUET = "parquet"
    PARQUET_VERSIONED = "parquet_versioned"
    SQLITE = "sqlite"
    DUCKDB = "duckdb"


class WritePolicy(Enum):
    APPEND = "append"  # Append new data, do not overwrite existing records
    UPSERT = "upsert"  # Update existing records, insert new records


class BackupPolicy(Enum):
    NONE = "none"
    TIMESTAMPED_COPIES = (
        "timestamped_copies"  # Backup the table before writing new data
    )


class DatabaseBase(ABC):
    def __init__(
        self,
        backend: DatabaseBackend = DatabaseBackend.DEFAULT,
        data_folder: str = "",
    ):
        self.BACKEND = backend
        self.data_folder = data_folder
        self.write_policy = WritePolicy.UPSERT
        self.backup_policy = BackupPolicy.NONE

    def set_write_policy(self, policy: WritePolicy):
        if not isinstance(policy, WritePolicy):
            raise ValueError("WritePolicy must be an instance of WritePolicy.")
        self.write_policy = policy

    def set_backup_policy(self, policy: BackupPolicy):
        if not isinstance(policy, BackupPolicy):
            raise ValueError("BackupPolicy must be an instance of BackupPolicy.")
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

    def field_is_nullable(self, props: dict):
        # Check if the 'properties' JSON specification allows the field to be nullable
        json_type = props.get("type", [])
        if not isinstance(json_type, list):
            json_type = [json_type]
        json_enum = props.get("enum", [])
        if not isinstance(json_enum, list):
            json_enum = [json_enum]
        return (
            props.get("nullable", False)
            or (None in json_type)
            or ('null' in json_type)
            or (None in json_enum)
            or ('null' in json_enum)
        )

    @abstractmethod
    def db_metadata(self):
        pass  # pragma: no cover

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

    @abstractmethod
    def sql_query(self, query: str, tablename: str) -> pd.DataFrame:
        pass  # pragma: no cover
