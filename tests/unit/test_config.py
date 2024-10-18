import os
import pytest

from unittest import mock
from unittest.mock import patch
from InsightBoard.config import ConfigManager


class mock_File:
    def __init__(self, exists=True):
        self._exists = exists

    def exists(self):
        return self._exists


class mock_Dir:
    def __init__(self, exists=True):
        self._exists = exists

    def exists(self):
        return self._exists

    def mkdir(self, *args, **kwargs):
        return None


@pytest.fixture
def manager():
    """ConfigManager is a singleton instance
    Ensure it is reset before each test to avoid test pollution.
    """
    manager = ConfigManager()
    del manager
    manager = ConfigManager()
    yield manager


def test_singleton(manager):
    # ConfigManager is a singleton instance
    assert manager
    config = ConfigManager()
    assert config
    assert manager is config


def test_singleton__reset(manager):
    # Check that our singleton reset method works
    config = {"name": "Alice"}
    assert manager
    manager_copy = ConfigManager()
    assert manager is manager_copy
    manager.config = config
    assert manager.config == config
    assert manager_copy.config == config
    del manager
    del manager_copy
    new_manager = ConfigManager()
    assert new_manager.config != config


def test_init(manager):
    config = manager
    assert config.config_dir
    assert config.config_file
    assert config.default_config


def test_ensure_config_exists__create(manager):
    # Create config file if it does not exist
    mock_open_file = mock.mock_open()
    with (
        patch.object(manager, "config_file", new=mock_File(exists=False)),
        patch.object(manager, "config_dir", new=mock_Dir(exists=False)),
        patch("builtins.open", mock_open_file),
        patch.object(manager, "write_default_config", return_value=None),
    ):
        manager.ensure_config_exists()
        mock_open_file.assert_called_once()


def test_get_config_base__windows(manager):
    with (
        patch.dict(os.environ, {"APPDATA": "C:\\Users\\Alice\\AppData"}),
        patch("platform.system", return_value="Windows"),
    ):
        assert str(manager.get_config_base()) == "C:\\Users\\Alice\\AppData"


def test_get_config_base__not_windows(manager):
    with (
        patch.dict(os.environ, {"HOME": "/home/alice"}),
        patch("platform.system", return_value="Linux"),
    ):
        assert str(manager.get_config_base()) == "/home/alice/.config"


def test_ensure_config_exists__exists(manager):
    # Create config file if it does not exist
    mock_open_file = mock.mock_open()
    with (
        patch.object(manager, "config_file", new=mock_File(exists=True)),
        patch.object(manager, "config_dir", new=mock_Dir(exists=False)),
        patch("builtins.open", mock_open_file),
        patch.object(manager, "write_default_config", return_value=None),
    ):
        manager.ensure_config_exists()
        mock_open_file.assert_not_called()


def test_write_default_config(manager):
    mock_file = mock.mock_open()
    with mock_file() as file:
        manager.write_default_config(file)
        file.write.assert_called()


def test_load_config__exists(manager):
    toml_data = {
        "name": "MyApp",
        "version": "1.0",
    }
    mock_config_file = mock.Mock()
    mock_config_file.exists.return_value = True
    with mock.patch(
        "builtins.open", mock.mock_open(read_data=b'name = "MyApp"\nversion = "1.0"')
    ):
        with mock.patch("tomllib.load", return_value=toml_data):
            manager.config_file = mock_config_file
            config = manager.load_config()
            assert config == toml_data


def test_load_config__not_exists(manager):
    mock_config_file = mock.Mock()
    mock_config_file.exists.return_value = False
    manager.config_file = mock_config_file
    config = manager.load_config()
    assert config == {}


def test_merge_configs(manager):
    config = {"name": "MyApp", "version": "1.0"}
    default_config = {"name": "MyApp", "author": "Bob"}
    config_merged = manager.merge_configs(config, default_config)
    assert config_merged == {"name": "MyApp", "version": "1.0", "author": "Bob"}


def test_load_and_merge_config(manager):
    pass


def test_get_project_folder(manager):
    manager.config = {
        "project": {
            "folder": "project_folder",
        },
    }
    assert manager.get_project_folder() == "project_folder"


def test_set_project_folder(manager):
    manager.config = {}
    manager.set_project_folder("project_folder")
    assert manager.config.get("project", {}).get("folder", None) == "project_folder"


def test_get_default_project(manager):
    manager.config = {
        "project": {
            "folder": "project_folder",
        },
    }
    assert manager.get_project_folder() == "project_folder"


def test_get__simple_key(manager):
    manager.config = {"name": "Alice"}
    assert manager.get("name", None) == "Alice"


def test_get__missing_key(manager):
    manager.config = {"name": "Alice"}
    assert not manager.get("age", None)


def test_get__nested_key(manager):
    manager.config = {"person": {"name": "Bob"}}
    assert manager.get("person.name", None) == "Bob"


def test_get__deeply_nested_key(manager):
    manager.config = {"a": {"b": {"c": {"d": {"e": "value"}}}}}
    assert manager.get("a.b.c.d.e", None) == "value"


def test_get__deeply_nested_missing_key(manager):
    manager.config = {"a": {"b": {"c": {"d": {"e": "value"}}}}}
    assert not manager.get("a.b.d.e", None)


def test_get__default_value(manager):
    manager.config = {"name": "Alice"}
    assert manager.get("age", 30) == 30


def test_set__simple_key(manager):
    manager.set("name", "Alice")
    assert manager.config.get("name", None) == "Alice"


def test_set__nested_key(manager):
    manager.set("person.name", "Bob")
    assert manager.config.get("person", None) == {"name": "Bob"}
    assert manager.config.get("person", {}).get("name", None) == "Bob"


def test_set__overwrite_key(manager):
    manager.set("name", "Alice")
    manager.set("name", "Charlie")
    assert manager.config.get("name", None) == "Charlie"


def test_set__add_to_existing_nested_key(manager):
    manager.set("person.name", "Bob")
    manager.set("person.age", 30)
    assert manager.config.get("person", None) == {"name": "Bob", "age": 30}


def test_set__deeply_nested_key(manager):
    manager.set("a.b.c.d.e", "value")
    assert manager.config.get("a", None) == {"b": {"c": {"d": {"e": "value"}}}}


def test_save(manager):
    config = {"name": "MyApp", "version": "1.0"}
    mock_open = mock.mock_open()
    manager.config_file = "dummy_file.toml"
    manager.config = config
    with (
        mock.patch("builtins.open", mock_open),
        mock.patch("tomli_w.dump") as mock_tomli_w_dump,
    ):
        manager.save()
        mock_open.assert_called_once_with("dummy_file.toml", "wb")
        mock_tomli_w_dump.assert_called_once_with(config, mock_open())
