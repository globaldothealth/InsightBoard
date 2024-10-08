import importlib

from unittest.mock import patch

import InsightBoard as ib


def test_main_fcn():
    with (
        patch("InsightBoard.__main__.app") as mock_app,
        patch("InsightBoard.__main__.__name__", "__main__"),
    ):
        mock_app.run.return_value = None
        module = importlib.reload(importlib.import_module("InsightBoard.__main__"))
        assert module.__name__ == "InsightBoard.__main__"
        # mock_app.run.assert_called_once()


def test_main():
    class mock_process:
        def __init__(self, *args, **kwargs):
            pass

        def wait(self):
            return 0

    with (
        patch("subprocess.Popen") as mock_subprocess,
        patch("webbrowser.open") as mock_webbrowser,
    ):
        mock_subprocess.return_value = mock_process()
        mock_webbrowser.return_value = None
        ib.main()
