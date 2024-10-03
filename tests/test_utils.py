import inspect
import pytest
import pandas as pd
from unittest.mock import patch
from InsightBoard.utils import (
    get_project,
    load_module,
    validate_against_jsonschema,
    validate_row_jsonschema,
)
from InsightBoard.project import Project


@pytest.fixture
def sample_data():
    return pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "city": ["New York", "San Francisco", "Los Angeles"],
        }
    )


@pytest.fixture
def sample_schema():
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "city": {"type": "string"},
        },
        "required": ["name", "age", "city"],
    }


def test_get_project():
    # Get an existing project
    name = "test_project"
    with patch("pathlib.Path.exists") as mock_path_exists:
        mock_path_exists.return_value = True
        project = get_project(name)
    assert isinstance(project, Project)
    assert project.name == name


def test_get_project_fail():
    # Attempt to get a project that does not exist
    with pytest.raises(Exception):
        get_project("nonexistent_project")


def test_load_module():
    module = load_module("inspect", inspect.__file__)
    assert inspect.ismodule(module)
    assert isinstance(module, type(inspect))
    assert module.__name__ == "inspect"


def test_load_module_fail():
    with pytest.raises(Exception):
        load_module("nonexistent_module")


def test_validate_against_jsonschema(sample_data, sample_schema):
    errors = validate_against_jsonschema(sample_data, sample_schema)
    assert len(errors) == 3  # One error per row
    assert all(isinstance(error, list) for error in errors)  # Errors are lists
    assert all(len(error) == 0 for error in errors)  # No errors in this case


def test_validate_against_jsonschema_fail(sample_data, sample_schema):
    sample_data["age"] = ["25", "30", "35"]  # Schema error: age should be an integer
    errors = validate_against_jsonschema(sample_data, sample_schema)
    assert len(errors) == 3  # One error per row
    assert all(isinstance(error, list) for error in errors)  # Errors are lists
    assert all(len(error) == 1 for error in errors)  # One error per row


def test_validate_row_jsonschema(sample_data, sample_schema):
    errors = validate_row_jsonschema(0, sample_data.iloc[0].to_dict(), sample_schema)
    assert len(errors) == 0  # No errors in this case


def test_validate_row_jsonschema_fail(sample_data, sample_schema):
    sample_data["age"] = ["25", 30, 35]  # Schema error: age should be an integer
    errors = validate_row_jsonschema(0, sample_data.iloc[0].to_dict(), sample_schema)
    assert len(errors) == 1  # One error in this case
