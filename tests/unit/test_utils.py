import json
import inspect
import pytest
import pandas as pd
from pathlib import Path
from unittest import mock
from unittest.mock import patch
from InsightBoard.utils import (
    get_project,
    load_module,
    validate_against_jsonschema,
    validate_row_jsonschema,
    ensure_schema_ordering,
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
    path_exists = Path.exists  # Rename to prevent recursive calls

    # Mock existence of the project folder
    def mock_path_exists(self):
        if self.name == "test_project":
            return True
        return path_exists(self)

    with patch("pathlib.Path.exists", new=mock_path_exists):
        project = get_project(name)
    assert isinstance(project, Project)
    assert project.name == name


def test_get_project_fail():
    # Attempt to get a project that does not exist
    with pytest.raises(Exception):
        get_project("nonexistent_project")


def test_load_module__str():
    module = load_module("inspect", inspect.__file__)
    assert inspect.ismodule(module)
    assert isinstance(module, type(inspect))
    assert module.__name__ == "inspect"


def test_load_module__path():
    module = load_module("inspect", Path(inspect.__file__))
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


def test_validate_against_jsonschema__fail(sample_data, sample_schema):
    sample_data["age"] = ["25", "30", "35"]  # Schema error: age should be an integer
    errors = validate_against_jsonschema(sample_data, sample_schema)
    assert len(errors) == 3  # One error per row
    assert all(isinstance(error, list) for error in errors)  # Errors are lists
    assert all(len(error) == 1 for error in errors)  # One error per row


def test_validate_against_jsonschema__filename(sample_data, sample_schema):
    with mock.patch(
        "builtins.open", mock.mock_open(read_data=json.dumps(sample_schema))
    ) as mock_open:
        errors = validate_against_jsonschema(sample_data, "some_filename")
        mock_open.assert_called_once()
        assert len(errors) == 3  # One error per row
        assert all(isinstance(error, list) for error in errors)  # Errors are lists
        assert all(len(error) == 0 for error in errors)  # No errors in this case


def test_validate_against_jsonschema__path(sample_data, sample_schema):
    with mock.patch(
        "builtins.open", mock.mock_open(read_data=json.dumps(sample_schema))
    ) as mock_open:
        errors = validate_against_jsonschema(sample_data, Path("some_filename"))
        mock_open.assert_called_once()
        assert len(errors) == 3  # One error per row
        assert all(isinstance(error, list) for error in errors)  # Errors are lists
        assert all(len(error) == 0 for error in errors)  # No errors in this case


def test_validate_against_jsonschema__invalid_schema():
    df = pd.DataFrame()
    with pytest.raises(Exception):
        validate_against_jsonschema(df, 123)
    with pytest.raises(Exception):
        validate_against_jsonschema(df, [1, 2, 3])


def test_validate_row_jsonschema(sample_data, sample_schema):
    errors = validate_row_jsonschema(0, sample_data.iloc[0].to_dict(), sample_schema)
    assert len(errors) == 0  # No errors in this case


def test_validate_row_jsonschema__fail(sample_data, sample_schema):
    sample_data["age"] = ["25", 30, 35]  # Schema error: age should be an integer
    errors = validate_row_jsonschema(0, sample_data.iloc[0].to_dict(), sample_schema)
    assert len(errors) == 1  # One error in this case


def test_ensure_schema_ordering(sample_schema):
    class mock_Project:
        class database:
            @staticmethod
            def get_table_schema(*args, **kwargs):
                # Schema ordering is: name, age, city
                return json.loads(json.dumps(sample_schema))

    columns = [{"name": v, "id": v} for v in ["age", "city", "name"]]
    with (
        patch("InsightBoard.utils.get_project") as mock_project,
    ):
        mock_project.return_value = mock_Project()
        ordered_columns = ensure_schema_ordering(columns, "test_project", "table_name")
        assert ordered_columns == [columns[2], columns[0], columns[1]]


def test_ensure_schema_ordering__abort(sample_schema):
    columns = [{"name": v, "id": v} for v in ["age", "city", "name"]]
    assert columns == ensure_schema_ordering(columns, [], [])
