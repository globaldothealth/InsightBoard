import json
import pytest
import pandas as pd

from unittest import mock
from tempfile import TemporaryDirectory
from unittest.mock import patch

from InsightBoard.database import Database, DatabaseBackend


@pytest.fixture
def db():
    with TemporaryDirectory() as temp_dir:
        yield Database(DatabaseBackend.PARQUET, temp_dir)


def test_DatabaseParquet(db):
    assert db.BACKEND == DatabaseBackend.PARQUET


def test_DatabaseParquet_commit_tables_dict__single(db):
    table_name = "table1"
    dataset = {"col1": [1, 2, 3], "col2": [4, 5, 6]}
    db.commit_tables_dict(table_name, dataset)
    # Read and check parquet files
    db1 = pd.read_parquet(db.data_folder + "/table1.parquet")
    assert db1.equals(pd.DataFrame(dataset))


def test_DatabaseParquet_commit_tables_dict__failure(db):
    table_names = "table1"
    ds1 = {"col1": [1, 2, 3], "col2": [4, 5, 6]}
    ds2 = {"col1": [7, 8, 9], "col2": [10, 11, 12]}
    datasets = [ds1, ds2]
    with pytest.raises(ValueError):
        db.commit_tables_dict(table_names, datasets)


def test_DatabaseParquet_commit_tables_dict__list(db):
    table_names = ["table1", "table2"]
    ds1 = {"col1": [1, 2, 3], "col2": [4, 5, 6]}
    ds2 = {"col1": [7, 8, 9], "col2": [10, 11, 12]}
    datasets = [ds1, ds2]
    db.commit_tables_dict(table_names, datasets)
    # Read and check parquet files
    db1 = pd.read_parquet(db.data_folder + "/table1.parquet")
    assert db1.equals(pd.DataFrame(ds1))
    db2 = pd.read_parquet(db.data_folder + "/table2.parquet")
    assert db2.equals(pd.DataFrame(ds2))


def test_commit_tables__single(db):
    table_name = "table1"
    dataset = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    db.commit_tables(table_name, dataset)
    # Read and check parquet files
    db1 = pd.read_parquet(db.data_folder + "/table1.parquet")
    assert db1.equals(dataset)


def test_commit_tables__failure(db):
    table_names = ["table1", "table2"]
    datasets = [
        pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]}),
    ]
    with pytest.raises(ValueError):
        db.commit_tables(table_names, datasets)


def test_commit_tables__list(db):
    table_names = ["table1", "table2"]
    datasets = [
        pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]}),
        pd.DataFrame({"col1": [7, 8, 9], "col2": [10, 11, 12]}),
    ]
    db.commit_tables(table_names, datasets)
    # Read and check parquet files
    db1 = pd.read_parquet(db.data_folder + "/table1.parquet")
    assert db1.equals(datasets[0])
    db2 = pd.read_parquet(db.data_folder + "/table2.parquet")
    assert db2.equals(datasets[1])


def test_get_primary_key(db):
    with patch(
        "InsightBoard.database.database.DatabaseBase.get_table_schema"
    ) as mock_schema:
        mock_schema.return_value = {
            "properties": {
                "col1": {"type": "integer", "PrimaryKey": True},
                "col2": {"type": "number"},
                "col3": {"type": "string"},
            },
        }
        table_name = "table1"
        assert db.get_primary_key(table_name) == "col1"


def test_get_primary_key__too_many(db):
    with patch(
        "InsightBoard.database.database.DatabaseBase.get_table_schema"
    ) as mock_schema:
        mock_schema.return_value = {
            "properties": {
                "col1": {"type": "integer", "PrimaryKey": True},
                "col2": {"type": "number", "PrimaryKey": True},
                "col3": {"type": "string"},
            },
        }
        table_name = "table1"
        with pytest.raises(ValueError):
            db.get_primary_key(table_name)


def test_get_table_schema(db):
    mock_json_schema = {
        "properties": {
            "col1": {"type": "integer"},
            "col2": {"type": "number"},
            "col3": {"type": "string"},
        }
    }
    table_name = "table1"
    with patch("builtins.open", mock.mock_open(read_data=json.dumps(mock_json_schema))):
        result = db.get_table_schema(table_name)
        assert result == mock_json_schema


def test_get_table_schema__failure(db):
    table_name = "non_existent_table"
    result = db.get_table_schema(table_name)
    assert not result


def test_get_tables_list__none(db):
    tables = db.get_tables_list()
    assert tables == []


def test_get_tables_list__single(db):
    table_name = "table1"
    dataset = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    db.commit_tables(table_name, dataset)
    tables = db.get_tables_list()
    assert tables == [table_name]


def test_get_tables_list__multiple(db):
    table_names = ["table1", "table2"]
    datasets = [
        pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]}),
        pd.DataFrame({"col1": [7, 8, 9], "col2": [10, 11, 12]}),
    ]
    db.commit_tables(table_names, datasets)
    tables = db.get_tables_list()
    assert set(tables) == set(table_names)


def test_get_tables_list__bad_folder(db):
    db.data_folder = "bad_folder"
    assert db.get_tables_list() == []


def test_read_table(db):
    table_name = "table1"
    dataset = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    db.commit_tables(table_name, dataset)
    result = db.read_table(table_name)
    assert result.equals(dataset)


def test_commit_table(db):
    table_name = "table1"
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    db.commit_table(table_name, df)
    # Read and check parquet file
    db1 = pd.read_parquet(db.data_folder + "/table1.parquet")
    assert db1.equals(df)


def test_write_table_parquet(db):
    table_name = "table1"
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    db.write_table_parquet(table_name, df)
    # Read and check parquet file
    db1 = pd.read_parquet(db.data_folder + "/table1.parquet")
    assert db1.equals(df)


def test_write_table_parquet__primary_key(db):
    # Write table with primary key
    table_name = "table1"
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    db.write_table_parquet(table_name, df)
    # Overwrite table including primary key duplicates
    with patch(
        "InsightBoard.database.database.DatabaseParquet.get_primary_key"
    ) as mock_get_primary_key:
        mock_get_primary_key.return_value = "col1"
        df = pd.DataFrame({"col1": [3, 4, 5], "col2": [7, 8, 9]})
        db.write_table_parquet(table_name, df)
    # Read and check parquet file
    db1 = pd.read_parquet(db.data_folder + "/table1.parquet")
    df_composite = pd.DataFrame({"col1": [1, 2, 3, 4, 5], "col2": [4, 5, 7, 8, 9]})
    assert db1.equals(df_composite)
