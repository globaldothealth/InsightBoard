import json
import logging
import importlib
import pandas as pd

from pathlib import Path
from jsonschema import Draft7Validator

from InsightBoard.project import Project
from InsightBoard.project.project import (  # expose downstream # noqa: F401
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
        row_dict = row.to_dict()
        # .to_dict() treats NA as NaN; need to replace with None for validation
        for k, v in row_dict.items():
            if isinstance(v, float) and pd.isna(v):
                row_dict[k] = None
        errors = validate_row_jsonschema(idx, row_dict, schema)
        error_list.append(errors)
    return error_list


def validate_row_jsonschema(row_number, row, schema):
    validator = Draft7Validator(schema)
    return list(validator.iter_errors(row))


def ensure_schema_ordering(columns, project, table, prepend=None, append=None):
    if not prepend:
        prepend = []
    if not append:
        append = []
    try:
        projectObj = get_project(project)
        schema = projectObj.database.get_table_schema(table)
        schema_order = list(schema["properties"].keys())
        # Add columns in prepend to the beginning
        for col in reversed(prepend):
            if col["id"] not in schema_order:
                schema_order.insert(0, col["id"])
        # Add any remaining columns that are not in the schema to the end
        for col in columns:
            if col["id"] not in schema_order and col["id"] not in append:
                schema_order.append(col["id"])
        # Add columns in append to the end
        for col in append:
            if col["id"] not in schema_order:
                schema_order.append(col["id"])
        columns = sorted(columns, key=lambda x: schema_order.index(x["id"]))
    except Exception as e:
        logging.debug(f"Error in ensure_schema_ordering: {str(e)}")
    return columns
