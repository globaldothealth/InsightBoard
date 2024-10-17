import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock
from unittest.mock import patch
from InsightBoard.project.project import (
    get_projects_folder,
    get_default_project,
    get_projects_list,
    get_custom_assets_folder,
    Project,
)


class mock_Path:
    def __init__(self, path, exists=True):
        self.path = path
        self.path_exists = exists

    @property
    def parent(self):
        return mock_Path("/".join(self.path.split("/")[0:-1]), exists=self.path_exists)

    def __truediv__(self, other):
        return mock_Path(f"{self.path}/{other}", exists=self.path_exists)

    def __str__(self):
        return self.path

    def exists(self):
        return self.path_exists


def test_get_projects_folder():
    with patch("InsightBoard.project.project.ConfigManager") as mock_config_manager:
        mock_config_manager.return_value.get_project_folder.return_value = "/projects"
        assert get_projects_folder() == "/projects"


def test_get_default_project():
    with patch("InsightBoard.project.project.ConfigManager") as mock_config_manager:
        mock_config_manager.return_value.get_default_project.return_value = (
            "default_project"
        )
        assert get_default_project() == "default_project"


def test_get_projects_list():
    with patch("InsightBoard.project.project.Path") as mock_projects_folder:
        mock_projects_folder.return_value.glob.return_value = ["project1", "project2"]
        get_projects_list() == ["project1", "project2"]


def test_get_custom_assets_folder():
    with patch("InsightBoard.project.project.Path") as mock_path:
        mock_path.return_value = mock_Path("/projects/project_name", exists=True)
        assert get_custom_assets_folder() == "/projects/style"


def test_get_custom_assets_folder__not_exists():
    with patch("InsightBoard.project.project.Path") as mock_path:
        mock_path.return_value = mock_Path("/projects/project_name", exists=False)
        assert not get_custom_assets_folder()


@pytest.fixture
def project():
    path_exists = Path.exists  # Rename to prevent recursive calls

    # Mock existence of the project folder
    def mock_path_exists(self):
        if self.name == "project_name":
            return True
        return path_exists(self)

    with (
        patch(
            "InsightBoard.project.project.get_projects_folder"
        ) as mock_projects_folder,
        patch("pathlib.Path.exists", new=mock_path_exists),
    ):
        mock_projects_folder.return_value = "/projects"
        project = Project("project_name")
    return project


def test_Project___init__(project):
    assert project.name == "project_name"
    assert project.projects_folder == "/projects"
    assert project.project_folder == "/projects/project_name"
    assert project.get_reports_folder() == "/projects/project_name/reports"
    assert project.get_data_folder() == "/projects/project_name/data"
    assert project.get_parsers_folder() == "/projects/project_name/parsers"
    assert project.get_schemas_folder() == "/projects/project_name/schemas"


def test_Project_get_schema(project):
    mock_json_data = {"name": "Test Schema", "version": 1}
    with mock.patch(
        "builtins.open", mock.mock_open(read_data=json.dumps(mock_json_data))
    ) as mock_open:
        result = project.get_schema("file")
        mock_open.assert_called_once()
        assert result == mock_json_data


def test_Project_get_reports_list(project):
    with TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "reports").mkdir(parents=True, exist_ok=True)
        project.project_folder = tmpdir
        (Path(tmpdir) / "reports" / "report1.py").touch()
        (Path(tmpdir) / "reports" / "report2.py").touch()
        (Path(tmpdir) / "reports" / "report3.py").touch()
        expected_reports_list = [
            {"label": f, "value": f} for f in ["report1", "report2", "report3"]
        ]
        reports_list = project.get_reports_list()
        assert len(reports_list) == len(expected_reports_list)
        assert set([item["label"] for item in reports_list]) == set(
            [item["label"] for item in expected_reports_list]
        )
        assert set([item["value"] for item in reports_list]) == set(
            [item["value"] for item in expected_reports_list]
        )


def test_Project_get_reports_list__empty(project):
    project.project_folder = "/this_project_does_not_exist"
    assert not project.get_reports_list()


def test_Project_get_project_datasets(project):
    with TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "data").mkdir(parents=True, exist_ok=True)
        project.project_folder = tmpdir
        (Path(tmpdir) / "data" / "dataset1.parquet").touch()
        (Path(tmpdir) / "data" / "dataset2.parquet").touch()
        (Path(tmpdir) / "data" / "dataset3.parquet").touch()
        expected_data_list = [
            {"filename": f, "label": f} for f in ["dataset1", "dataset2", "dataset3"]
        ]
        data_list = project.get_project_datasets()
        assert len(data_list) == len(expected_data_list)
        assert set([item["label"] for item in data_list]) == set(
            [item["label"] for item in expected_data_list]
        )


def test_Project_get_project_datasets__empty(project):
    project.project_folder = "/this_project_does_not_exist"
    assert not project.get_project_datasets()


def test_Project_get_project_parsers(project):
    with TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "parsers").mkdir(parents=True, exist_ok=True)
        project.project_folder = tmpdir
        (Path(tmpdir) / "parsers" / "parser1.py").touch()
        (Path(tmpdir) / "parsers" / "parser2.py").touch()
        (Path(tmpdir) / "parsers" / "parser3.py").touch()
        expected_parsers_list = [
            {"filename": f, "label": f} for f in ["parser1", "parser2", "parser3"]
        ]
        parsers_list = project.get_project_parsers()
        assert len(parsers_list) == len(expected_parsers_list)
        assert set([item["label"] for item in parsers_list]) == set(
            [item["label"] for item in expected_parsers_list]
        )


def test_Project_get_project_parsers__empty(project):
    project.project_folder = "/this_project_does_not_exist"
    assert not project.get_project_parsers()


def test_Project_get_datasets(project):
    # project.get_datasets()
    ...


def test_Project_load_and_parse(project):
    # project.load_and_parse()
    ...
