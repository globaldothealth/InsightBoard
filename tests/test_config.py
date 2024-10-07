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


def test_singleton():
    # ConfigManager is a singleton instance
    config = ConfigManager()
    assert config
    config2 = ConfigManager()
    assert config2
    assert config == config2


def test_init():
    config = ConfigManager()
    assert config.config_dir
    assert config.config_file
    assert config.default_config


def test_ensure_config_exists__create():
    config = ConfigManager()
    # Create config file if it does not exist
    mock_open_file = mock.mock_open()
    with (
        patch.object(config, "config_file", new=mock_File(exists=False)),
        patch.object(config, "config_dir", new=mock_Dir(exists=False)),
        patch("builtins.open", mock_open_file),
        patch.object(config, "write_default_config", return_value=None),
    ):
        config.ensure_config_exists()
        mock_open_file.assert_called_once()


def test_ensure_config_exists__exists():
    config = ConfigManager()
    # Create config file if it does not exist
    mock_open_file = mock.mock_open()
    with (
        patch.object(config, "config_file", new=mock_File(exists=True)),
        patch.object(config, "config_dir", new=mock_Dir(exists=False)),
        patch("builtins.open", mock_open_file),
        patch.object(config, "write_default_config", return_value=None),
    ):
        config.ensure_config_exists()
        mock_open_file.assert_not_called()


def test_write_default_config():
    config = ConfigManager()
    mock_file = mock.mock_open()
    with mock_file() as file:
        config.write_default_config(file)
        file.write.assert_called()


def test_load_config__exists():
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
            config_loader = ConfigManager()
            config_loader.config_file = mock_config_file
            config = config_loader.load_config()
            assert config == toml_data


def test_load_config__not_exists():
    mock_config_file = mock.Mock()
    mock_config_file.exists.return_value = False
    config_loader = ConfigManager()
    config_loader.config_file = mock_config_file
    config = config_loader.load_config()
    assert config == {}


def test_merge_configs():
    ...


def test_load_and_merge_config():
    ...


def test_get_project_folder():
    ...


def test_get_default_project():
    ...


def test_set_simple_key():
    manager = ConfigManager()
    manager.set("name", "Alice")
    assert manager.config.get("name", None) == "Alice"


def test_set_nested_key():
    manager = ConfigManager()
    manager.set("person.name", "Bob")
    assert manager.config.get("person", None) == {"name": "Bob"}


def test_set_overwrite_key():
    manager = ConfigManager()
    manager.set("name", "Alice")
    manager.set("name", "Charlie")
    assert manager.config.get("name", None) == "Charlie"


def test_set_add_to_existing_nested_key():
    manager = ConfigManager()
    manager.set("person.name", "Bob")
    manager.set("person.age", 30)
    assert manager.config.get("person", None) == {"name": "Bob", "age": 30}


def test_set_deeply_nested_key():
    manager = ConfigManager()
    manager.set("a.b.c.d.e", "value")
    assert manager.config.get('a', None) == {"b": {"c": {"d": {"e": "value"}}}}


def test_save():
    config = {"name": "MyApp", "version": "1.0"}
    mock_open = mock.mock_open()
    config_manager = ConfigManager()
    config_manager.config_file = "dummy_file.toml"
    config_manager.config = config
    with (
        mock.patch('builtins.open', mock_open),
        mock.patch('tomli_w.dump') as mock_tomli_w_dump,
    ):
        config_manager.save()
        mock_open.assert_called_once_with("dummy_file.toml", "wb")
        mock_tomli_w_dump.assert_called_once_with(config, mock_open())
