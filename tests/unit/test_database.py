import pytest

from InsightBoard.database import Database


def test_Database_NotSupported():
    with pytest.raises(ValueError):
        Database("Not supported backend")
