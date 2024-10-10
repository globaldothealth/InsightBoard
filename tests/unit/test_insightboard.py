import importlib

from unittest.mock import patch


def test_main_fcn():
    with (
        patch("InsightBoard.__main__.app") as mock_app,
        patch("InsightBoard.__main__.__name__", "__main__"),
    ):
        mock_app.run.return_value = None
        module = importlib.reload(importlib.import_module("InsightBoard.__main__"))
        assert module.__name__ == "InsightBoard.__main__"
