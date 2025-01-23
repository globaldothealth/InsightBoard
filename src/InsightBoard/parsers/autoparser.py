import base64
import importlib.resources as resources
import io
import re
import warnings
from ast import literal_eval
from pathlib import Path
from typing import Literal

import pandas as pd
import tomli
import tomli_w

try:
    import adtl.autoparser as autoparser
except ImportError:
    autoparser = None


class AutoParser:
    def __init__(
        self,
        model: Literal["openai", "gemini"] | None = None,
        api_key: str | None = None,
        schema: str | None = None,  # this a path or the actual JSON file?
        table_name=None,
        schema_path=None,
    ):
        if autoparser is None:
            raise ImportError(
                "autoparser is not installed. Please install it using `pip install "
                '"adtl[autoparser]"`'
            )

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

    @property
    def is_autoparser_ready(self) -> tuple[bool, str]:
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

    def create_dict(
        self,
        filename: str,
        contents: base64,
        llm_descriptions: bool,
        language: Literal["fr", "en"],
    ) -> pd.DataFrame:
        _, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        ext = filename.split(".")[-1].lower()
        if ext == "csv":
            raw_df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        elif ext == "xlsx":
            raw_df = pd.read_excel(io.BytesIO(decoded))
        else:
            raise ValueError(
                f"Unsupported file type: {ext}. Please provide data as either an Excel"
                " file, or a csv",
            )

        # currently config doesn't make any difference
        self.data_dict = autoparser.create_dict(raw_df, config=self.config)

        # this config won't be right?
        if llm_descriptions:
            self.data_dict = autoparser.generate_descriptions(
                self.data_dict,
                language,
                key=self.api_key,
                llm=self.model,
                config=self.config,
            )

        return self.data_dict

    def create_mapping(
        self, data_dict: pd.DataFrame, language: Literal["fr", "en"]
    ) -> tuple[pd.DataFrame, list]:
        # PL: 'Description' if no LLM used, 'source_description' if not... need to fix
        # inside adtl.autoparser
        descriptions = data_dict["source_description"]
        if any(descriptions.isnull()):
            raise ValueError(
                "The data dictionary is missing one or more field descriptions which "
                "are required for mapping"
            )

        with warnings.catch_warnings(record=True) as w:
            self.mapping = autoparser.create_mapping(
                data_dict,
                self.schema_path,
                language,
                self.api_key,
                llm=self.model,
                config=self.config,
                save=False,
            )
            if w:
                for warning in w:
                    # Match the warning message to your expected pattern
                    match = re.search(
                        r"The following schema fields have not been mapped: (\[.*\])",
                        str(warning.message),
                    )
                    if match:
                        # Extract the list from the matched group
                        unmapped_fields = literal_eval(
                            match.group(1)
                        )  # Safely evaluate the list
                        break

                errors = []
                for i, row in self.mapping.iterrows():
                    if i not in unmapped_fields:
                        errors.append([])
                    else:
                        errors.append(
                            [
                                {
                                    "path": "source_field",
                                    "message": f"{i} has not been mapped",
                                }
                            ]
                        )

                return self.mapping, errors
        return self.mapping, []

    def create_parser(self, mapping: pd.DataFrame, parser_loc: str, name: str) -> bool:
        # write TOML file
        autoparser.create_parser(
            mapping,
            self.schema_path.parent,
            str(Path(parser_loc, "adtl", f"{name}.toml")),
            config=self.config,
        )

        # make associated python file for InsightBoard
        content = f"""import pandas as pd
from pathlib import Path
from InsightBoard.parsers import parse_adtl

SPECIFICATION_FILE = "adtl/{name}.toml"

def parse(df: pd.DataFrame) -> list[dict]:
    spec_file = Path(__file__).parent / SPECIFICATION_FILE
    return parse_adtl(df, spec_file, ["linelist"])
"""

        file = Path(parser_loc, f"adtl-{name}.py")

        # Create parent directories if they don't exist
        file.parent.mkdir(parents=True, exist_ok=True)

        file.write_text(content)

        return True
