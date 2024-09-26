import os
import json
import importlib
import pandas as pd
import pyarrow.parquet as pq

from enum import Enum
from pathlib import Path
from pyarrow import Table
from jsonschema import Draft7Validator
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
    def commit_table(self, project: str, table_name: str, df: pd.DataFrame):
        pass


class DatabaseParquet(DatabaseBase):

    def __init__(self, data_folder: str = ""):
        super().__init__(DatabaseBackend.PARQUET, data_folder)

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


def find_project_root():
    """Find project root

    Return the full path to the projects root folder.
    """
    cwd = os.getcwd()
    if os.path.exists(f"{cwd}/projects"):
        return cwd
    raise Exception("'projects' folder not found in the current working directory.")


def get_projects_folder():
    """Get projects folder

    Return the path to the (root) projects folder (i.e. './projects').
    """
    return f"{find_project_root()}/projects"


def get_projects_list():
    """Get projects list

    Return the name of subfolders in the './projects' folder.
    These are the projects that the user has created.
    Projects have a folder structure like this:
        ./projects
            /MyProject1
                /data
                    ... (managed data files) ...
                /reports
                    MyReport1.py (reports per project)
                    ...
                /parsers
                    MyParser1.py (ingestion parsers per source)
                    ...
            ...

    """
    return [f.name for f in sorted(Path(get_projects_folder()).iterdir()) if f.is_dir()]


class Project:

    def __init__(self, name):
        self.name = name
        self.projects_folder = get_projects_folder()
        self.project_folder = f"{self.projects_folder}/{self.name}"
        self.database = Database(
            backend=DatabaseBackend.PARQUET,
            data_folder=self.get_data_folder()
        )

    def get_reports_folder(self):
        return f"{self.project_folder}/reports"

    def get_data_folder(self):
        return f"{self.project_folder}/data"

    def get_parsers_folder(self):
        return f"{self.project_folder}/parsers"

    def get_schemas_folder(self):
        return f"{self.project_folder}/schemas"

    def get_reports_list(self):
        report_files = [
            f
            for f in Path(self.get_reports_folder()).iterdir()
            if f.is_file() and f.suffix == ".py"
        ]
        return [{"label": f.stem, "value": f.stem} for f in report_files]

    def get_project_datasets(self):
        return [
            {"filename": f, "label": f.with_suffix("").name}
            for f in Path(self.get_data_folder()).iterdir()
            if f.is_file() and f.suffix == ".parquet"
        ]

    def get_project_parsers(self):
        return [
            {"filename": f, "label": f.with_suffix("").name}
            for f in Path(self.get_parsers_folder()).iterdir()
            if f.is_file() and f.suffix == ".py"
        ]

    def get_datasets(self, datasets):
        project_datasets = self.get_project_datasets()
        if not all(d in [d["label"] for d in project_datasets] for d in datasets):
            raise Exception(
                "Not all requested datasets are available "
                f"in the project '{self.project}'.\n"
                f"Requested datasets: {datasets}\n"
                f"Available datasets: {[d['label'] for d in project_datasets]}"
            )
        datasets = [d for d in project_datasets if d["label"] in datasets]
        return [pd.read_parquet(f"{d['filename']}") for d in datasets]

    def commit_tables_dict(self, table_names, datasets):
        self.database.commit_tables_dict(self.name, table_names, datasets)


def get_project(name):
    return Project(name)


def load_module(module_name, module_path):
    # Dynamically load the selected report
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_against_jsonscheme(df: pd.DataFrame, schema):
    if isinstance(schema, str) or isinstance(schema, Path):
        with open(schema, "r") as f:
            schema = json.load(f)
    if not isinstance(schema, dict):
        raise ValueError(
            f"Schema must be a dictionary or a path to a json file. Got {type(schema)}"
        )

    # schema validation
    error_list = []
    for idx, row in df.iterrows():
        errors = validate_row_jsonschema(idx, row.to_dict(), schema)
        error_list.append(errors)
    return error_list


def validate_row_jsonschema(row_number, row, schema):
    validator = Draft7Validator(schema)
    error_list = list(validator.iter_errors(row))
    if error_list:
        return f"Row {row_number + 1} - " + (
            "; ".join(
                [
                    f"'{""".""".join([str(e) for e in error.path])}': {error.message}"
                    for error in error_list
                ]
            )
        )
    return []
