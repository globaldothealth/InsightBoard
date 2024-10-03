import json
import importlib
import pandas as pd

from pathlib import Path
from jsonschema import Draft7Validator

from .project import Project
from .project.project import (  # expose downstream # noqa: F401
    get_projects_list,
    get_default_project,
    get_custom_assets_folder,
)


def get_project(name):
    return Project(name)


def load_module(module_name: str, module_path: str | Path):
    # Dynamically load the selected report
    if isinstance(module_path, Path):
        module_path = str(module_path)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_against_jsonschema(df: pd.DataFrame, schema):
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
    return list(validator.iter_errors(row))
