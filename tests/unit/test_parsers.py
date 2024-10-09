import sys
import importlib
from unittest import mock
import pytest
import pandas as pd
from unittest.mock import patch

from InsightBoard.parsers import (
    adtl_check_command,
    adtl_check_parser,
    adtl,
    parse_adtl,
)


def test_import_adtl__success():
    with patch.dict("sys.modules", {"adtl": mock.Mock()}):
        importlib.reload(importlib.import_module("InsightBoard.parsers"))
        import InsightBoard.parsers

        assert InsightBoard.parsers.adtl_parser is not None


def test_import_adtl__failure():
    with patch.dict("sys.modules", {"adtl": None}):
        importlib.reload(importlib.import_module("InsightBoard.parsers"))
        import InsightBoard.parsers

        assert InsightBoard.parsers.adtl_parser is None


def test_adtl_check_command():
    with patch("InsightBoard.parsers.shutil.which") as mock_which:
        mock_which.return_value = True
        adtl_check_command()


def test_adtl_check_command_fail():
    with patch("InsightBoard.parsers.shutil.which") as mock_which:
        mock_which.return_value = None
        with pytest.raises(ImportError):
            adtl_check_command()


def test_adtl_check_parser():
    with patch("InsightBoard.parsers.adtl_parser") as mock_adtl_parser:
        mock_adtl_parser.return_value = True
        adtl_check_parser()


def test_adtl_check_parser_fail():
    with patch("InsightBoard.parsers.adtl_parser", None):
        with pytest.raises(ImportError):
            adtl_check_parser()


def test_adtl():
    class mock_Result:
        stdout = b"test"

    df = pd.DataFrame()
    specification_file = "some_file.json"
    with (
        patch("InsightBoard.parsers.subprocess.run") as mock_run,
        patch("InsightBoard.parsers.adtl_check_command", return_value=None),
    ):
        mock_run.return_value = mock_Result
        assert adtl(df, specification_file) == {"stdout": b"test"}


class mock_adtl_parser:
    def __init__(self, *args, **kwargs):
        pass

    class Parser:
        def __init__(self, *args, **kwargs):
            self.df = pd.DataFrame(
                {
                    "adtl_valid": [True, True, False],
                    "adtl_error": [None, None, None],
                    "name": ["test1", "test2", "test3"],
                }
            )

        def parse(self, filename):
            class Parse:
                def __init__(self, df):
                    self.df = df

                def write_csv(self, table_name, filename, *args, **kwargs):
                    self.df.to_csv(filename)

            return Parse(self.df)


@patch("InsightBoard.parsers.adtl_parser", mock_adtl_parser)
def test_parse_adtl__str():
    df = pd.DataFrame({"name": ["test1", "test2", "test3"]})
    spec_file = "some_file.json"
    table_names = "table1"
    dbs = parse_adtl(df, spec_file, table_names)
    assert len(dbs) == 1
    db1 = dbs[0]
    assert db1["database"] == "table1"
    assert db1["data"]["name"].equals(df["name"])


@patch("InsightBoard.parsers.adtl_parser", mock_adtl_parser)
def test_parse_adtl__list():
    df = pd.DataFrame({"name": ["test1", "test2", "test3"]})
    spec_file = "some_file.json"
    table_names = ["table1", "table2"]
    dbs = parse_adtl(df, spec_file, table_names)
    len(dbs) == 2
    db1, db2 = dbs
    assert db1["database"] == "table1"
    assert db1["data"]["name"].equals(df["name"])
    assert db2["database"] == "table2"
    assert db2["data"]["name"].equals(df["name"])
