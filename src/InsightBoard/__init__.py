import os
import time
import socket
import subprocess
import webbrowser
from .app import app  # noqa: F401

from .version import __version__  # noqa: F401

INSIGHTBOARD_PORT = os.getenv("INSIGHTBOARD_PORT", 8050)
INSIGHTBOARD_TIMEOUT = os.getenv("INSIGHTBOARD_TIMEOUT", 30)


def launch_app() -> subprocess.Popen:
    cmd = [
        "waitress-serve",
        f"--listen=0.0.0.0:{INSIGHTBOARD_PORT}",
        "InsightBoard.app:server",
    ]
    return subprocess.Popen(cmd)


def wait_for_server(port=INSIGHTBOARD_PORT, timeout=INSIGHTBOARD_TIMEOUT) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True  # Server is up
        except (OSError, ConnectionRefusedError):
            time.sleep(1)
    raise TimeoutError(f"Server did not start within {timeout} seconds")


def main(debug=False):
    process = launch_app()
    wait_for_server(INSIGHTBOARD_PORT, INSIGHTBOARD_TIMEOUT)
    webbrowser.open(f"http://127.0.0.1:{INSIGHTBOARD_PORT}")
    process.wait()
