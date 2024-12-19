import base64
import importlib.resources as resources
import io
from pathlib import Path

import pandas as pd
import tomli
import tomli_w

try:
    import adtl.autoparser as autoparser
except ImportError:
    autoparser = None


class AutoParser:
    def __init__(
        self, model=None, api_key=None, schema=None, table_name=None, schema_path=None
    ):
        self.model = model
        self.api_key = api_key

        # find appropriate way to get the config file & schema
        self.schema = schema

        if schema_path:
            with resources.files("adtl.autoparser.config").joinpath(
                "autoparser.toml"
            ).open("rb") as fp:
                config = tomli.load(fp)
            schema_loc = Path(schema_path, table_name)
            schema_loc = schema_loc.parent / (schema_loc.name + ".schema.json")
            self.schema_path = schema_loc
            config["schemas"] = {table_name: str(schema_loc)}

            schema_path = Path(schema_path)
            config_path = Path(schema_path, "autoparser.toml")
            with open(str(config_path), "wb") as f:
                tomli_w.dump(config, f)
            self.config = config_path

        else:
            self.config = None

        # created attributes
        self.data_dict = None
        self.mapping_file = None
        # don't need to save the parser, it'll get written out

    @property
    def is_autoparser_ready(self):
        not_set = []
        if not self.model:
            not_set.append("model")
        if not self.api_key:
            not_set.append("api key")
        if not self.schema:
            not_set.append("schema")

        return (
            not not_set,
            f"AutoParser is not ready, please set {', '.join(not_set)}",
        )

    def create_dict(self, filename, contents, llm_descriptions, language):
        ready, msg = self.is_autoparser_ready
        if not ready:
            return msg, None

        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        ext = filename.split(".")[-1].lower()
        if ext == "csv":
            raw_df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        elif ext == "xlsx":
            raw_df = pd.read_excel(io.BytesIO(decoded))
        else:
            return "Unsupported file type.", None, [], "", ""

        # currently config doesn't make any difference
        self.data_dict = autoparser.create_dict(raw_df, config=self.config)

        # this config won't be right
        if llm_descriptions:
            self.data_dict = autoparser.generate_descriptions(
                self.data_dict,
                language,
                key=self.api_key,
                llm=self.model,
                config=self.config,
            )

        return self.data_dict

    def create_mapping(self, data_dict, language):
        descriptions = data_dict["source_description"]
        if descriptions.empty:
            return (
                "The data dictionary is missing the field descriptions required for mapping.",
                None,
                [],
                "",
                "",
            )

        self.mapping = autoparser.create_mapping(
            data_dict,
            self.schema_path,
            language,
            self.api_key,
            llm=self.model,
            config=self.config,
        )
        return self.mapping

    def create_parser(self):
        if not self.mapping:
            return "No mapping file", None

        autoparser.create_parser(
            self.mapping, self.schema, "file path for parser", config=self.config
        )

        return "Parser saved to <file path>", True
