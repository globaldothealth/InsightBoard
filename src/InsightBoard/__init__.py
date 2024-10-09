import subprocess
import webbrowser
from .app import app  # noqa: F401

from .version import __version__  # noqa: F401


def main(debug=False):
    port = 8050
    cmd = [
        "waitress-serve",
        f"--listen=0.0.0.0:{port}",
        "InsightBoard.app:server",
    ]
    process = subprocess.Popen(cmd)
    webbrowser.open(f"http://127.0.0.1:{port}")
    process.wait()
