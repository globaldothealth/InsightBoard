"""Unit tests for the Parquet and Versioned-Parquet database backends."""

import json
import pytest
import pandas as pd

from unittest import mock
from datetime import datetime
from tempfile import TemporaryDirectory
from unittest.mock import patch

from InsightBoard.database import Database, DatabaseBackend, WritePolicy, BackupPolicy


@pytest.fixture
def db_parquet():
    with TemporaryDirectory() as temp_dir:
        yield Database(DatabaseBackend.PARQUET, temp_dir)


@pytest.fixture
def db_parquet_versioned():
    with TemporaryDirectory() as temp_dir:
        yield Database(DatabaseBackend.PARQUET_VERSIONED, temp_dir)


def drop_metadata(df):
    return df.drop(columns=["_version", "_deleted", "_metadata"], errors="ignore")


@pytest.mark.parametrize(
    "backend, db_backend",
    [
        ("db_parquet", DatabaseBackend.PARQUET),
        ("db_parquet_versioned", DatabaseBackend.PARQUET_VERSIONED),
    ],
)
def test_backend(request, backend, db_backend):
    db = request.getfixturevalue(backend)
    assert db.BACKEND == db_backend


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_DatabaseParquet_commit_tables_dict__single(request, backend):
    db = request.getfixturevalue(backend)
    table_name = "table1"
    dataset = {"col1": [1, 2, 3], "col2": [4, 5, 6]}
    db.commit_tables_dict(table_name, dataset)
    # Read and check parquet files
    db1 = drop_metadata(pd.read_parquet(db.data_folder + "/table1." + db.suffix))
    assert db1.equals(pd.DataFrame(dataset))


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_DatabaseParquet_commit_tables_dict__failure(request, backend):
    db = request.getfixturevalue(backend)
    table_names = "table1"
    ds1 = {"col1": [1, 2, 3], "col2": [4, 5, 6]}
    ds2 = {"col1": [7, 8, 9], "col2": [10, 11, 12]}
    datasets = [ds1, ds2]
    with pytest.raises(ValueError):
        db.commit_tables_dict(table_names, datasets)


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_DatabaseParquet_commit_tables_dict__list(request, backend):
    db = request.getfixturevalue(backend)
    table_names = ["table1", "table2"]
    ds1 = {"col1": [1, 2, 3], "col2": [4, 5, 6]}
    ds2 = {"col1": [7, 8, 9], "col2": [10, 11, 12]}
    datasets = [ds1, ds2]
    db.commit_tables_dict(table_names, datasets)
    # Read and check parquet files
    db1 = drop_metadata(pd.read_parquet(db.data_folder + "/table1." + db.suffix))
    assert db1.equals(pd.DataFrame(ds1))
    db2 = drop_metadata(pd.read_parquet(db.data_folder + "/table2." + db.suffix))
    assert db2.equals(pd.DataFrame(ds2))


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_commit_tables__single(request, backend):
    db = request.getfixturevalue(backend)
    table_name = "table1"
    dataset = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    db.commit_tables(table_name, dataset)
    # Read and check parquet files
    db1 = drop_metadata(pd.read_parquet(db.data_folder + "/table1." + db.suffix))
    assert db1.equals(dataset)


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_commit_tables__failure(request, backend):
    db = request.getfixturevalue(backend)
    table_names = ["table1", "table2"]
    datasets = [
        pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]}),
    ]
    with pytest.raises(ValueError):
        db.commit_tables(table_names, datasets)


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_commit_tables__list(request, backend):
    db = request.getfixturevalue(backend)
    table_names = ["table1", "table2"]
    datasets = [
        pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]}),
        pd.DataFrame({"col1": [7, 8, 9], "col2": [10, 11, 12]}),
    ]
    db.commit_tables(table_names, datasets)
    # Read and check parquet files
    db1 = drop_metadata(pd.read_parquet(db.data_folder + "/table1." + db.suffix))
    assert db1.equals(datasets[0])
    db2 = drop_metadata(pd.read_parquet(db.data_folder + "/table2." + db.suffix))
    assert db2.equals(datasets[1])


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_get_primary_key(request, backend):
    db = request.getfixturevalue(backend)
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


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_get_primary_key__too_many(request, backend):
    db = request.getfixturevalue(backend)
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


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_get_table_schema(request, backend):
    db = request.getfixturevalue(backend)
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


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_get_table_schema__failure(request, backend):
    db = request.getfixturevalue(backend)
    table_name = "non_existent_table"
    result = db.get_table_schema(table_name)
    assert not result


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_get_tables_list__none(request, backend):
    db = request.getfixturevalue(backend)
    tables = db.get_tables_list()
    assert tables == []


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_get_tables_list__single(request, backend):
    db = request.getfixturevalue(backend)
    table_name = "table1"
    dataset = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    db.commit_tables(table_name, dataset)
    tables = db.get_tables_list()
    assert tables == [table_name]


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_get_tables_list__multiple(request, backend):
    db = request.getfixturevalue(backend)
    table_names = ["table1", "table2"]
    datasets = [
        pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]}),
        pd.DataFrame({"col1": [7, 8, 9], "col2": [10, 11, 12]}),
    ]
    db.commit_tables(table_names, datasets)
    tables = db.get_tables_list()
    assert set(tables) == set(table_names)


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_get_tables_list__bad_folder(request, backend):
    db = request.getfixturevalue(backend)
    db.data_folder = "bad_folder"
    assert db.get_tables_list() == []


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_read_table(request, backend):
    db = request.getfixturevalue(backend)
    table_name = "table1"
    dataset = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    db.commit_table(table_name, dataset)
    result = db.read_table(table_name)
    assert result.equals(dataset)


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_commit_table(request, backend):
    db = request.getfixturevalue(backend)
    table_name = "table1"
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    db.commit_table(table_name, df)
    # Read and check parquet file
    db1 = drop_metadata(pd.read_parquet(db.data_folder + "/table1." + db.suffix))
    assert db1.equals(df)


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_write_table_parquet(request, backend):
    db = request.getfixturevalue(backend)
    table_name = "table1"
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    db.write_table_parquet(table_name, df)
    # Read and check parquet file
    db1 = drop_metadata(pd.read_parquet(db.data_folder + "/table1." + db.suffix))
    assert db1.equals(df)


def test_write_table_parquet__primary_key_upsert(db_parquet):
    # Write table using upsert policy --- Parquet DB (no versioning)
    db = db_parquet
    table_name = "table1"
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    write_policy = WritePolicy.UPSERT
    backup_policy = BackupPolicy.NONE
    db.write_table_parquet(table_name, df, write_policy, backup_policy)
    # Overwrite table including primary key duplicates
    with patch(
        "InsightBoard.database.database.DatabaseParquet.get_primary_key"
    ) as mock_get_primary_key:
        mock_get_primary_key.return_value = "col1"
        df = pd.DataFrame({"col1": [1, 3, 4, 5], "col2": [7, 8, 9, 10]})
        db.write_table_parquet(table_name, df, write_policy, backup_policy)
    # Read and check parquet file (sort columns for comparison)
    db1 = pd.read_parquet(db.data_folder + "/table1." + db.suffix).sort_values("col1")
    df_composite = pd.DataFrame(
        {"col1": [1, 2, 3, 4, 5], "col2": [7, 5, 8, 9, 10]}
    ).sort_values("col1")
    # upsert policy (rows 2 and 3 update)
    assert (db1.values == df_composite.values).all()


def test_write_table_parquet_versioned__primary_key_upsert(db_parquet_versioned):
    # Write table using upsert policy --- Parquet DB (with versioning)
    db = db_parquet_versioned
    table_name = "table1"
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    write_policy = WritePolicy.UPSERT
    backup_policy = BackupPolicy.NONE
    with patch("InsightBoard.database.database.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2021, 2, 1, 1, 2, 3)
        db.write_table_parquet(table_name, df, write_policy, backup_policy)
    # Overwrite table including primary key duplicates
    with patch(
        "InsightBoard.database.database.DatabaseParquet.get_primary_key"
    ) as mock_get_primary_key:
        mock_get_primary_key.return_value = "col1"
        df = pd.DataFrame({"col1": [1, 3, 4, 5], "col2": [7, 8, 9, 10]})
        with patch("InsightBoard.database.database.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2022, 3, 2, 4, 5, 6)
            db.write_table_parquet(table_name, df, write_policy, backup_policy)
    # Read and check parquet file (sort columns for comparison)
    db1 = pd.read_parquet(db.data_folder + "/table1." + db.suffix).sort_values("col1")
    df_composite = pd.DataFrame(
        {
            "col1": [1, 2, 3, 1, 3, 4, 5],
            "col2": [4, 5, 6, 7, 8, 9, 10],
            "_version": [1, 1, 1, 2, 2, 1, 1],
            "_deleted": [False] * 7,
            "_metadata": ['{"timestamp": "2021-02-01T01:02:03"}'] * 3
            + ['{"timestamp": "2022-03-02T04:05:06"}'] * 4,
        }
    ).sort_values("col1")
    # upsert policy (rows 2 and 3 update)
    assert (db1.values == df_composite.values).all()
    # Check that the database returns only the most recent version of each row
    with patch(
        "InsightBoard.database.database.DatabaseParquet.get_primary_key"
    ) as mock_get_primary_key:
        mock_get_primary_key.return_value = "col1"
        df2 = db.read_table("table1")
    df2_check = pd.DataFrame(
        {
            "col1": [1, 2, 3, 4, 5],
            "col2": [7, 5, 8, 9, 10],
        }
    )
    df2 = df2.sort_values("col1")
    df2_check = df2_check.sort_values("col1")
    assert (df2.values == df2_check.values).all()


def test_write_table_parquet__primary_key_append(db_parquet):
    db = db_parquet
    # Write table with primary key
    table_name = "table1"
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    write_policy = WritePolicy.APPEND
    backup_policy = BackupPolicy.NONE
    db.write_table_parquet(table_name, df, write_policy, backup_policy)
    # Overwrite table including primary key duplicates
    with patch(
        "InsightBoard.database.database.DatabaseParquet.get_primary_key"
    ) as mock_get_primary_key:
        mock_get_primary_key.return_value = "col1"
        df = pd.DataFrame({"col1": [1, 3, 4, 5], "col2": [7, 8, 9, 10]})
        db.write_table_parquet(table_name, df, write_policy, backup_policy)
    # Read and check parquet file (sort columns for comparison)
    db1 = pd.read_parquet(db.data_folder + "/table1." + db.suffix).sort_values("col1")
    df_composite = pd.DataFrame(
        {
            "col1": [1, 2, 3, 4, 5],
            "col2": [4, 5, 6, 9, 10],
        }
    ).sort_values("col1")
    # append policy (rows 2 and 3 do not update)
    assert (db1.values == df_composite.values).all()


def test_write_table_parquet_versioned__primary_key_append(db_parquet_versioned):
    db = db_parquet_versioned
    # Write table with primary key
    table_name = "table1"
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    write_policy = WritePolicy.APPEND
    backup_policy = BackupPolicy.NONE
    with patch("InsightBoard.database.database.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2021, 2, 1, 1, 2, 3)
        db.write_table_parquet(table_name, df, write_policy, backup_policy)
    # Overwrite table including primary key duplicates
    with patch(
        "InsightBoard.database.database.DatabaseParquet.get_primary_key"
    ) as mock_get_primary_key:
        mock_get_primary_key.return_value = "col1"
        df = pd.DataFrame({"col1": [1, 3, 4, 5], "col2": [7, 8, 9, 10]})
        with patch("InsightBoard.database.database.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2022, 3, 2, 4, 5, 6)
            db.write_table_parquet(table_name, df, write_policy, backup_policy)
    # Read and check parquet file (sort columns for comparison)
    db1 = pd.read_parquet(db.data_folder + "/table1." + db.suffix).sort_values("col1")
    df_composite = pd.DataFrame(
        {
            "col1": [1, 2, 3, 4, 5],
            "col2": [4, 5, 6, 9, 10],
            "_version": [1] * 5,
            "_deleted": [False] * 5,
            "_metadata": ['{"timestamp": "2021-02-01T01:02:03"}'] * 3
            + ['{"timestamp": "2022-03-02T04:05:06"}'] * 2,
        }
    ).sort_values("col1")
    # append policy (rows 2 and 3 do not update)
    assert (db1.values == df_composite.values).all()
