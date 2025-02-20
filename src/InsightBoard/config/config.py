import logging
import os
import platform
import tomllib
from pathlib import Path

import tomli_w


class ConfigManager:
    _instance = None

    # Make ConfigManager a singleton instance
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        # Define the path to the config file in the user's home directory
        self.config_dir = self.get_config_base() / "InsightBoard"
        self.config_file = self.config_dir / "config.toml"

        # Default configuration
        self.default_config = {
            "project": {
                "folder": (Path.home() / "InsightBoard" / "projects").as_posix()
            },
            "chatbot": {
                "model": os.environ.get("CHATBOT_MODEL", None),
                "api_key": os.environ.get("CHATBOT_API_KEY", None),
            },
            "autoparser": {
                "model": os.environ.get("AUTOPARSER_MODEL", None),
                "api_key": os.environ.get("AUTOPARSER_API_KEY", None),
            },
        }

        # Ensure the config file exists and load the config
        self.config = self.load_and_merge_config()

    def get_config_base(self) -> Path:
        """Get the base configuration dictionary."""
        if platform.system() == "Windows":
            return Path(os.getenv("APPDATA"))
        else:
            return Path.home() / ".config"

    def ensure_config_exists(self):
        """
        Check if the config file exists, and create it with default values if it doesn't
        """
        if not self.config_file.exists():
            # Create the directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            # Write the default config manually since tomllib can't write
            with open(self.config_file, "w") as file:
                self.write_default_config(file)
            logging.info(f"Configuration file created at {self.config_file}")
        else:
            logging.info(f"Configuration file found at {self.config_file}")

    def write_default_config(self, file):
        """Manually write the default configuration to a TOML file."""
        file.write("[project]\n")
        file.write(f'folder = "{self.default_config["project"]["folder"]}"\n')

    def load_config(self):
        """Load the configuration from the TOML file using tomllib."""
        if self.config_file.exists():
            with open(self.config_file, "rb") as file:
                config = tomllib.load(file)
            return config
        return {}

    def merge_configs(self, loaded_config, default_config):
        """
        Recursively merge default and loaded configuration,
        keeping defaults for missing keys.
        """
        for key, value in default_config.items():
            if isinstance(value, dict) and key in loaded_config:
                # If the value is a dictionary, recursively merge
                loaded_config[key] = self.merge_configs(
                    loaded_config.get(key, {}), value
                )
            else:
                # If the key is missing in the loaded config, use the default
                loaded_config.setdefault(key, value)
        return loaded_config

    def load_and_merge_config(self):
        """Ensure config exists, load the user config, and merge with defaults."""
        self.ensure_config_exists()
        user_config = self.load_config()
        # Merge user config with default config, keeping defaults for missing keys
        config = self.merge_configs(user_config, self.default_config)
        # Make the projects folder if it doesn't exist
        Path(config["project"]["folder"]).mkdir(parents=True, exist_ok=True)
        return config

    def get_project_folder(self):
        """Get the project folder from the configuration."""
        return self.config.get("project", {}).get("folder", None)

    def set_project_folder(self, folder):
        """Set the project folder in the configuration."""
        self.set("project.folder", folder)

    def get_default_project(self):
        """Get the default project from the configuration."""
        return self.config.get("project", {}).get("default", None)

    def get(self, key, default=None):
        """Get a key from the configuration, with a default value."""
        keys = key.split(".")
        d = self.config
        for key in keys:
            d = d.get(key, {})
        return d or default

    def set(self, key, value, save=True):
        """Set a key in the configuration."""
        keys = key.split(".")
        d = self.config  # Reference to dictionary
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        d[keys[-1]] = value
        if save:
            self.save()

    @staticmethod
    def remove_null(d):
        """TOML does not support nil/null values, simply remove them."""
        for key, value in list(d.items()):
            if value is None:
                del d[key]
            elif isinstance(value, dict):
                ConfigManager.remove_null(value)
                if not value:
                    del d[key]
        return d

    def save(self):
        """Save the configuration to the TOML file."""
        with open(self.config_file, "wb") as file:
            tomli_w.dump(ConfigManager.remove_null(self.config), file)
        logging.info(f"Configuration saved to {self.config_file}")
