import os
import pandas as pd

from pathlib import Path

from InsightBoard.database import Database, DatabaseBackend
from InsightBoard.config import ConfigManager


def get_projects_folder():
    """Get projects folder

    Return the path to the (root) projects folder (i.e. './projects').
    """
    config = ConfigManager()
    projects_folder = config.get_project_folder()
    return projects_folder


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
            backend=DatabaseBackend.PARQUET, data_folder=self.get_data_folder()
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
        data_folder = Path(self.get_data_folder())
        if data_folder.exists():
            return [
                {"filename": f, "label": f.with_suffix("").name}
                for f in data_folder.iterdir()
                if f.is_file() and f.suffix == ".parquet"
            ]
        return []

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
                f"in the project '{self.name}'.\n"
                f"Requested datasets: {datasets}\n"
                f"Available datasets: {[d['label'] for d in project_datasets]}"
            )
        datasets = [d for d in project_datasets if d["label"] in datasets]
        return [pd.read_parquet(f"{d['filename']}") for d in datasets]
