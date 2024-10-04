import subprocess
import webbrowser
from .app import app  # noqa: F401

from .version import __version__  # noqa: F401


def main(debug=False):
    port = 8050
    cmd = [
        "gunicorn",
        "InsightBoard.app:server",
        *["--bind", f"0.0.0.0:{port}"],
    ]
    process = subprocess.Popen(cmd)
    webbrowser.open(f"http://127.0.0.1:{port}")
    process.wait()
