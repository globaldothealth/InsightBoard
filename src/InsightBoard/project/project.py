import io
import json
import base64
import tomllib
import tomli_w
import pandas as pd

from pathlib import Path

from InsightBoard.database import Database, DatabaseBackend, BackupPolicy
from InsightBoard.config import ConfigManager
from InsightBoard import utils


def get_projects_folder():
    """Get projects folder

    Return the path to the (root) projects folder (i.e. './projects').
    """
    config = ConfigManager()
    projects_folder = config.get_project_folder()
    return projects_folder


def get_default_project():
    """Get default project

    Return the name of the default project.
    """
    config = ConfigManager()
    return config.get_default_project()


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


def get_custom_assets_folder() -> str | None:
    assets_path = Path(get_projects_folder()).parent / "style"
    if assets_path.exists():
        # Return absolute path to the style sheets
        return str(assets_path)
    else:
        return None


class Project:
    def __init__(self, name):
        self.name = name
        self.projects_folder = get_projects_folder()
        self.project_folder = f"{self.projects_folder}/{self.name}"
        if not Path(self.project_folder).exists():
            raise Exception(
                f"Project '{self.name}' does not exist in '{self.projects_folder}'."
            )
        self.default_config = {
            "project": {
                "name": self.name,
            },
            "database": {
                "backend": DatabaseBackend.PARQUET.name,
                "data_folder": "data",
                "backup_policy": BackupPolicy.NONE.name,
            },
        }
        self.config = self.load_config()
        # Initialise database
        self.database = Database(
            backend=self.get_db_backend(),
            data_folder=self.get_data_folder(),
        )
        self.database.set_backup_policy(self.get_db_backup_policy())

    def load_config(self):
        config_path = Path(self.project_folder) / "config.toml"
        if config_path.exists():
            with open(config_path, "rb") as f:
                file_config = tomllib.load(f)
            return {**self.default_config, **file_config}
        else:
            return self.default_config

    def save_config(self):
        config_path = Path(self.project_folder) / "config.toml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "wb") as f:
            tomli_w.dump(self.config, f)

    def set_db_backup_policy(self, policy: BackupPolicy):
        if not isinstance(policy, BackupPolicy):
            raise ValueError("Backup policy must be a BackupPolicy enum.")
        # Set the backup policy in the database
        self.database.set_backup_policy(policy)
        # Update configuration
        self.config["database"]["backup_policy"] = policy.name
        self.save_config()

    def get_db_backup_policy(self):
        return BackupPolicy[self.config["database"]["backup_policy"]]

    def set_db_backend(self, backend: DatabaseBackend):
        if not isinstance(backend, DatabaseBackend):
            raise ValueError("Database backend must be a DatabaseBackend enum.")
        # Create a new database backend
        self.database = Database(backend=backend, data_folder=self.get_data_folder())
        self.database.set_backup_policy(self.get_db_backup_policy())
        # Update configuration
        self.config["database"]["backend"] = backend.name
        self.save_config()

    def get_db_backend(self):
        return DatabaseBackend[self.config["database"]["backend"]]

    def get_reports_folder(self):
        return f"{self.project_folder}/reports"

    def get_data_folder(self):
        return f"{self.project_folder}/data"

    def get_parsers_folder(self):
        return f"{self.project_folder}/parsers"

    def get_schemas_folder(self):
        return f"{self.project_folder}/schemas"

    def get_schema(self, schema_name):
        schema_path = Path(self.get_schemas_folder()) / f"{schema_name}.schema.json"
        with open(schema_path, "r") as f:
            return json.load(f)

    def get_reports_list(self):
        reports_folder = Path(self.get_reports_folder())
        if not reports_folder.exists():
            return []
        report_files = [
            f
            for f in Path(self.get_reports_folder()).iterdir()
            if f.is_file() and f.suffix == ".py"
        ]
        return [{"label": f.stem, "value": f.stem} for f in report_files]

    def get_project_datasets(self):
        data_folder = Path(self.get_data_folder())
        if not data_folder.exists():
            return []
        return [
            {"filename": f, "label": f.name[: -len(self.database.suffix) - 1]}
            for f in data_folder.iterdir()
            if f.is_file() and f.name.endswith(self.database.suffix)
        ]

    def get_project_parsers(self):
        parsers_folder = Path(self.get_parsers_folder())
        if not parsers_folder.exists():
            return []
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
        return [self.database.read_table(d["label"]) for d in datasets]

    def load_and_parse(self, filename, contents, selected_parser):
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        ext = filename.split(".")[-1].lower()
        if ext == "csv":
            raw_df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        elif ext == "xlsx":
            raw_df = pd.read_excel(io.BytesIO(decoded))
        else:
            return "Unsupported file type.", None, [], "", ""

        # Parse the data using the selected parser
        parsers_folder = self.get_parsers_folder()
        parser_module = utils.load_module(
            selected_parser, f"{parsers_folder}/{selected_parser}.py"
        )
        parsed_df_list = parser_module.parse(raw_df)
        if not isinstance(parsed_df_list, list):
            parsed_df_list = [parsed_df_list]
        return parsed_df_list
