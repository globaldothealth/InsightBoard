import os
import pandas as pd
import pyarrow.parquet as pq

from enum import Enum
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

    def commit_tables_dict(self, project: str, table_names: [str], datasets: [dict]):
        if not isinstance(datasets, list):
            datasets = [datasets]
        for idx, data in enumerate(datasets):
            datasets[idx] = pd.DataFrame(data)
        self.commit_tables(project, table_names, datasets)

    def commit_tables(self, project: str, table_names: [str], datasets: [pd.DataFrame]):
        if not isinstance(table_names, list):
            table_names = [table_names]
        if not isinstance(datasets, list):
            datasets = [datasets]
        for table_name, df in zip(table_names, datasets, strict=True):
            self.commit_table(project, table_name, df)

    @abstractmethod
    def get_tables_list(self):
        pass

    @abstractmethod
    def read_table(self, project: str, table_name: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def commit_table(self, project: str, table_name: str, df: pd.DataFrame):
        pass


class DatabaseParquet(DatabaseBase):
    def __init__(self, data_folder: str = ""):
        super().__init__(DatabaseBackend.PARQUET, data_folder)

    def get_tables_list(self):
        return ['.'.join(f.split('.')[:-1]) for f in os.listdir(self.data_folder) if f.endswith(".parquet")]

    def read_table(self, project: str, table_name: str) -> pd.DataFrame:
        file_path = f"{self.data_folder}/{table_name}.parquet"
        table = pq.read_table(file_path)
        return table.to_pandas()

    def commit_table(self, project: str, table_name: str, df: pd.DataFrame):
        self.write_table_parquet(project, table_name, df)

    def write_table_parquet(self, project: str, table_name: str, df: pd.DataFrame):
        """Plain Parquet writer, no version history"""
        # Check if the Parquet file exists, and append the data
        file_path = f"{self.data_folder}/{table_name}.parquet"
        try:
            existing_table = pq.read_table(file_path)
            existing_df = existing_table.to_pandas()
            combined_df = pd.concat([existing_df, df], ignore_index=True)
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
