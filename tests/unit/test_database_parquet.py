"""Unit tests for the Parquet and Versioned-Parquet database backends."""

import json
import pytest
import pyarrow
import pandas as pd

from pathlib import Path
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


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_DatabaseParquet_set_write_policy(request, backend):
    db = request.getfixturevalue(backend)
    db.set_write_policy(WritePolicy.APPEND)
    assert db.write_policy == WritePolicy.APPEND
    db.set_write_policy(WritePolicy.UPSERT)
    assert db.write_policy == WritePolicy.UPSERT


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_DatabaseParquet_set_write_policy__invalid(request, backend):
    db = request.getfixturevalue(backend)
    with pytest.raises(ValueError):
        db.set_write_policy("invalid_policy")


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_DatabaseParquet_set_backup_policy(request, backend):
    db = request.getfixturevalue(backend)
    db.set_backup_policy(BackupPolicy.NONE)
    assert db.backup_policy == BackupPolicy.NONE
    db.set_backup_policy(BackupPolicy.TIMESTAMPED_COPIES)
    assert db.backup_policy == BackupPolicy.TIMESTAMPED_COPIES


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_DatabaseParquet_set_backup_policy__invalid(request, backend):
    db = request.getfixturevalue(backend)
    with pytest.raises(ValueError):
        db.set_backup_policy("invalid_policy")


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


def test_DatabaseParquet_read_table_column(db_parquet):
    db = db_parquet
    table_name = "table1"
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    table = pyarrow.Table.from_pandas(df)
    with patch("pyarrow.parquet.read_table", return_value=table):
        col1 = db.read_table_column(table_name, "col1")
        assert col1.equals(pd.Series([1, 2, 3]))
        col2 = db.read_table_column(table_name, "col2")
        assert col2.equals(pd.Series([4, 5, 6]))


def test_DatabaseParquetVersioned_read_table_column(db_parquet_versioned):
    db = db_parquet_versioned
    table_name = "table1"
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    with patch(
        "InsightBoard.database.database.DatabaseParquetVersioned.read_table",
        return_value=df,
    ):
        col1 = db.read_table_column(table_name, "col1")
        assert col1.equals(pd.Series([1, 2, 3]))
        col2 = db.read_table_column(table_name, "col2")
        assert col2.equals(pd.Series([4, 5, 6]))


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
    with patch(
        "InsightBoard.database.database.DatabaseBase.get_table_schema"
    ) as mock_schema:
        mock_schema.return_value = {
            "properties": {
                "col1": {"type": "integer"},
                "col2": {"type": "integer"},
            },
        }
        db.commit_tables_dict(table_name, dataset)
    # Read and check parquet files
    db1 = drop_metadata(pd.read_parquet(db.data_folder + "/table1." + db.suffix))
    assert (db1.values == pd.DataFrame(dataset).values).all()


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
    with patch(
        "InsightBoard.database.database.DatabaseBase.get_table_schema"
    ) as mock_schema:
        mock_schema.return_value = {
            "properties": {
                "col1": {"type": "integer"},
                "col2": {"type": "integer"},
            },
        }
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
    with patch(
        "InsightBoard.database.database.DatabaseBase.get_table_schema"
    ) as mock_schema:
        mock_schema.return_value = {
            "properties": {
                "col1": {"type": "integer"},
                "col2": {"type": "integer"},
            },
        }
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
    with patch(
        "InsightBoard.database.database.DatabaseBase.get_table_schema"
    ) as mock_schema:
        mock_schema.return_value = {
            "properties": {
                "col1": {"type": "integer"},
                "col2": {"type": "integer"},
            },
        }
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


def test_get_primary_keys_parquet(db_parquet):
    db = db_parquet
    with (
        patch(
            "InsightBoard.database.database.DatabaseBase.get_primary_key",
            return_value="col1",
        ),
        patch(
            "InsightBoard.database.database.DatabaseParquet.read_table_column",
            return_value=pd.Series([1, 2, 3]),
        ),
    ):
        assert db.get_primary_keys("table1") == [1, 2, 3]


def test_get_primary_keys_parquet_versioned(db_parquet_versioned):
    db = db_parquet_versioned
    with (
        patch(
            "InsightBoard.database.database.DatabaseBase.get_primary_key",
            return_value="col1",
        ),
        patch(
            "InsightBoard.database.database.DatabaseParquetVersioned.read_table_column",
            return_value=pd.Series([1, 2, 3]),
        ),
    ):
        assert db.get_primary_keys("table1") == [1, 2, 3]


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_get_primary_keys__no_key(request, backend):
    db = request.getfixturevalue(backend)
    with (
        patch(
            "InsightBoard.database.database.DatabaseBase.get_primary_key",
            return_value=None,
        ),
    ):
        assert db.get_primary_keys("table1") == []


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
    with patch(
        "InsightBoard.database.database.DatabaseBase.get_table_schema"
    ) as mock_schema:
        mock_schema.return_value = {
            "properties": {
                "col1": {"type": "integer"},
                "col2": {"type": "integer"},
            },
        }
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
    with patch(
        "InsightBoard.database.database.DatabaseBase.get_table_schema"
    ) as mock_schema:
        mock_schema.return_value = {
            "properties": {
                "col1": {"type": "integer"},
                "col2": {"type": "integer"},
            },
        }
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
    with patch(
        "InsightBoard.database.database.DatabaseBase.get_table_schema"
    ) as mock_schema:
        mock_schema.return_value = {
            "properties": {
                "col1": {"type": "integer"},
                "col2": {"type": "integer"},
            },
        }
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
    with patch(
        "InsightBoard.database.database.DatabaseBase.get_table_schema"
    ) as mock_schema:
        mock_schema.return_value = {
            "properties": {
                "col1": {"type": "integer"},
                "col2": {"type": "integer"},
            },
        }
        db.commit_table(table_name, df)
    # Read and check parquet file
    db1 = drop_metadata(pd.read_parquet(db.data_folder + "/table1." + db.suffix))
    assert db1.equals(df)


@pytest.mark.parametrize(
    "backend,suffix",
    [
        ("db_parquet", "parquet"),
        ("db_parquet_versioned", "ver.parquet"),
    ],
)
def test_backup(request, backend, suffix):
    db = request.getfixturevalue(backend)
    # Backup policy: NONE (no action)
    db.backup("datafile.parquet", BackupPolicy.NONE)
    with (
        TemporaryDirectory() as temp_dir,
    ):
        # Backup policy: TIMESTAMPED_COPIES (copy file)
        with (
            patch.object(db, "data_folder", temp_dir),
            patch("InsightBoard.database.db_parquet.datetime") as mock_datetime,
        ):
            # Create temp file for backup and ensure backup target does not exist
            temp_filename = str(Path(temp_dir) / "datafile.parquet")
            with open(temp_filename, "wb") as temp_file:
                temp_file.write(b"test contents")
            mock_datetime.now.return_value = datetime(2021, 2, 1, 1, 2, 3)
            strnow = mock_datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            target_file = Path(temp_dir) / "backup" / f"datafile_{strnow}.{suffix}"
            target_file.unlink(missing_ok=True)
            # Perform backup
            db.backup(temp_file.name, BackupPolicy.TIMESTAMPED_COPIES)
            # Check that the file was copied correctly
            assert target_file.exists()
            with open(target_file, "rb") as f:
                assert f.read() == b"test contents"


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
    with patch(
        "InsightBoard.database.database.DatabaseBase.get_table_schema"
    ) as mock_schema:
        mock_schema.return_value = {
            "properties": {
                "col1": {"type": "integer"},
                "col2": {"type": "integer"},
            },
        }
        db.write_table_parquet(table_name, df)
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
def test_write_table_parquet__empty(request, backend):
    db = request.getfixturevalue(backend)
    table_name = "table1"
    df = pd.DataFrame({"col1": [], "col2": []})
    db.write_table_parquet(table_name, df)


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_write_table_parquet__key_error(request, backend):
    db = request.getfixturevalue(backend)
    table_name = "table1"
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    with (
        patch(
            "InsightBoard.database.database.DatabaseBase.get_primary_key",
            return_value="not_a_column",
        ),
        patch(
            "InsightBoard.database.database.DatabaseBase.get_table_schema"
        ) as mock_schema,
    ):
        mock_schema.return_value = {
            "properties": {
                "col1": {"type": "integer"},
                "col2": {"type": "integer"},
            },
        }
        with pytest.raises(ValueError):
            db.write_table_parquet(table_name, df)


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_write_table_parquet__invalid_write_policy(request, backend):
    db = request.getfixturevalue(backend)
    table_name = "table1"
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    schema = {
        "properties": {
            "col1": {"type": "integer"},
            "col2": {"type": "integer"},
        },
    }
    with (
        patch(
            "InsightBoard.database.database.DatabaseBase.get_primary_key",
            return_value="col1",
        ),
        patch(
            "InsightBoard.database.database.DatabaseBase.get_table_schema"
        ) as mock_schema,
    ):
        # Ensure the target file exists (for append to work)
        mock_schema.return_value = schema
        db_file = Path(db.data_folder) / f"table1.{db.suffix}"
        db_file.unlink(missing_ok=True)
        db.write_table_parquet(table_name, df)
        with pytest.raises(ValueError):
            db.write_table_parquet(
                table_name,
                df,
                write_policy="invalid_policy",
                backup_policy=BackupPolicy.NONE,
            )


@pytest.mark.parametrize(
    "backend",
    [
        "db_parquet",
        "db_parquet_versioned",
    ],
)
def test_write_table_parquet__no_primary_key(request, backend):
    db = request.getfixturevalue(backend)
    table_name = "table1"
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    with (
        patch(
            "InsightBoard.database.database.DatabaseBase.get_primary_key",
            return_value=None,
        ),
        patch(
            "InsightBoard.database.database.DatabaseBase.get_table_schema"
        ) as mock_schema,
    ):
        mock_schema.return_value = {
            "properties": {
                "col1": {"type": "integer"},
                "col2": {"type": "integer"},
            },
        }
        db_file = Path(db.data_folder) / f"table1.{db.suffix}"
        db_file.unlink(missing_ok=True)
        db.write_table_parquet(table_name, df)
        df1 = drop_metadata(pd.read_parquet(db_file).sort_values("col1"))
        assert (df1.values == df.values).all()
        db.write_table_parquet(table_name, df)
        df2 = drop_metadata(pd.read_parquet(db_file))
        assert (df2.values == pd.concat([df, df]).values).all()


def test_write_table_parquet__primary_key_upsert(db_parquet):
    # Write table using upsert policy --- Parquet DB (no versioning)
    db = db_parquet
    table_name = "table1"
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    schema = {
        "properties": {
            "col1": {"type": "integer"},
            "col2": {"type": "integer"},
        },
    }
    write_policy = WritePolicy.UPSERT
    backup_policy = BackupPolicy.NONE
    with patch(
        "InsightBoard.database.database.DatabaseBase.get_table_schema"
    ) as mock_schema:
        mock_schema.return_value = schema
        db.write_table_parquet(table_name, df, write_policy, backup_policy)
    # Overwrite table including primary key duplicates
    with (
        patch(
            "InsightBoard.database.database.DatabaseParquet.get_primary_key"
        ) as mock_get_primary_key,
        patch(
            "InsightBoard.database.database.DatabaseBase.get_table_schema"
        ) as mock_schema,
    ):
        mock_get_primary_key.return_value = "col1"
        mock_schema.return_value = schema
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
    schema = {
        "properties": {
            "col1": {"type": "integer"},
            "col2": {"type": "integer"},
        },
    }
    write_policy = WritePolicy.UPSERT
    backup_policy = BackupPolicy.NONE
    with (
        patch("InsightBoard.database.db_parquet.datetime") as mock_datetime,
        patch(
            "InsightBoard.database.database.DatabaseBase.get_table_schema"
        ) as mock_schema,
    ):
        mock_datetime.now.return_value = datetime(2021, 2, 1, 1, 2, 3)
        mock_schema.return_value = schema
        db.write_table_parquet(table_name, df, write_policy, backup_policy)
    # Overwrite table including primary key duplicates
    with (
        patch(
            "InsightBoard.database.database.DatabaseParquet.get_primary_key"
        ) as mock_get_primary_key,
        patch(
            "InsightBoard.database.database.DatabaseBase.get_table_schema"
        ) as mock_schema,
    ):
        mock_get_primary_key.return_value = "col1"
        mock_schema.return_value = schema
        # Add the following:
        #  row 1: (no change, value remains 4); v1 retained
        #  row 3: (update, value changes from 6 to 8); v2 created
        #  row 4: (insert, new row)
        #  row 5: (insert, new row)
        df = pd.DataFrame({"col1": [1, 3, 4, 5], "col2": [4, 8, 9, 10]})
        with patch("InsightBoard.database.db_parquet.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2022, 3, 2, 4, 5, 6)
            db.write_table_parquet(table_name, df, write_policy, backup_policy)
    # Read and check parquet file (sort columns for comparison)
    db1 = pd.read_parquet(db.data_folder + "/table1." + db.suffix).sort_values("col1")
    df_composite = pd.DataFrame(
        {
            "col1": [1, 2, 3, 3, 4, 5],
            "col2": [4, 5, 6, 8, 9, 10],
            "_version": [1, 1, 1, 2, 1, 1],
            "_deleted": [False] * 6,
            "_metadata": ['{"timestamp": "2021-02-01T01:02:03"}'] * 3
            + ['{"timestamp": "2022-03-02T04:05:06"}'] * 3,
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
            "col2": [4, 5, 8, 9, 10],
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
    schema = {
        "properties": {
            "col1": {"type": "integer"},
            "col2": {"type": "integer"},
        },
    }
    write_policy = WritePolicy.APPEND
    backup_policy = BackupPolicy.NONE
    with patch(
        "InsightBoard.database.database.DatabaseBase.get_table_schema"
    ) as mock_schema:
        mock_schema.return_value = schema
        db.write_table_parquet(table_name, df, write_policy, backup_policy)
    # Overwrite table including primary key duplicates
    with (
        patch(
            "InsightBoard.database.database.DatabaseParquet.get_primary_key"
        ) as mock_get_primary_key,
        patch(
            "InsightBoard.database.database.DatabaseBase.get_table_schema"
        ) as mock_schema,
    ):
        mock_schema.return_value = schema
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
    schema = {
        "properties": {
            "col1": {"type": "integer"},
            "col2": {"type": "integer"},
        },
    }
    write_policy = WritePolicy.APPEND
    backup_policy = BackupPolicy.NONE
    with (
        patch("InsightBoard.database.db_parquet.datetime") as mock_datetime,
        patch(
            "InsightBoard.database.database.DatabaseBase.get_table_schema"
        ) as mock_schema,
    ):
        mock_schema.return_value = schema
        mock_datetime.now.return_value = datetime(2021, 2, 1, 1, 2, 3)
        db.write_table_parquet(table_name, df, write_policy, backup_policy)
    # Overwrite table including primary key duplicates
    with patch(
        "InsightBoard.database.database.DatabaseParquet.get_primary_key"
    ) as mock_get_primary_key:
        mock_get_primary_key.return_value = "col1"
        df = pd.DataFrame({"col1": [1, 3, 4, 5], "col2": [7, 8, 9, 10]})
        with (
            patch("InsightBoard.database.db_parquet.datetime") as mock_datetime,
            patch(
                "InsightBoard.database.database.DatabaseBase.get_table_schema"
            ) as mock_schema,
        ):
            mock_schema.return_value = schema
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
