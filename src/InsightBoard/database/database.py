import os
import json
import pandas as pd
import pyarrow.parquet as pq

from enum import Enum
from pathlib import Path
from pyarrow import Table
from abc import ABC, abstractmethod


class DatabaseBackend(Enum):
    PARQUET = "parquet"


class DatabaseBase(ABC):
    def __init__(
        self,
        backend: DatabaseBackend = DatabaseBackend.PARQUET,
        data_folder: str = "",
    ):
        self.BACKEND = backend
        self.data_folder = data_folder

    def commit_tables_dict(self, table_names: [str], datasets: [dict]):
        if not isinstance(datasets, list):
            datasets = [datasets]
        for idx, data in enumerate(datasets):
            datasets[idx] = pd.DataFrame(data)
        self.commit_tables(table_names, datasets)

    def commit_tables(self, table_names: [str], datasets: [pd.DataFrame]):
        if not isinstance(table_names, list):
            table_names = [table_names]
        if not isinstance(datasets, list):
            datasets = [datasets]
        for table_name, df in zip(table_names, datasets, strict=True):
            self.commit_table(table_name, df)

    def get_primary_key(self, table_name: str):
        schema_filename = (
            Path(self.data_folder).parent / "schemas" / f"{table_name}.schema.json"
        )
        try:
            with open(schema_filename, "r") as f:
                schema = json.load(f)
        except FileNotFoundError:
            return None
        # Find field that has the 'PrimaryKey' set to 'True'
        primary_key = None
        primary_key_count = 0
        for field_name, d in schema["properties"].items():
            if d.get("PrimaryKey", None):
                primary_key = field_name
                primary_key_count = primary_key_count + 1
        if primary_key_count > 1:
            raise ValueError(f"Table '{table_name}' has more than one primary key.")
        return primary_key

    @abstractmethod
    def get_tables_list(self):
        pass

    @abstractmethod
    def read_table(self, table_name: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def commit_table(self, table_name: str, df: pd.DataFrame):
        pass


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
    def commit_table(self, table_name: str, df: pd.DataFrame):
        self.write_table_parquet(table_name, df)

    # Utility functions

    def write_table_parquet(self, table_name: str, df: pd.DataFrame):
        """Plain Parquet writer, no version history"""
        # Check if the Parquet file exists, and append the data
        file_path = Path(self.data_folder) / f"{table_name}.parquet"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            current_df = pq.read_table(file_path).to_pandas()
            primary_key = self.get_primary_key(table_name)
            if primary_key:
                current_df = current_df[~current_df[primary_key].isin(df[primary_key])]
            combined_df = pd.concat([current_df, df], ignore_index=True)
        except FileNotFoundError:
            combined_df = df
        # Write the updated DataFrame to the Parquet file
        table = Table.from_pandas(combined_df)
        pq.write_table(table, file_path)


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
