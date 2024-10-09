import os
import time
import socket
import logging
import subprocess
import webbrowser
from .app import app  # noqa: F401

from .version import __version__  # noqa: F401

INSIGHTBOARD_HOST = os.getenv("INSIGHTBOARD_HOST", "127.0.0.1")
INSIGHTBOARD_PORT = os.getenv("INSIGHTBOARD_PORT", 8050)
INSIGHTBOARD_TIMEOUT = os.getenv("INSIGHTBOARD_TIMEOUT", 30)


def launch_app() -> subprocess.Popen:
    logging.getLogger("waitress.queue").setLevel(logging.ERROR)
    cmd = [
        "waitress-serve",
        f"--listen=0.0.0.0:{INSIGHTBOARD_PORT}",
        "InsightBoard.app:server",
    ]
    return subprocess.Popen(cmd)


def check_port(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except (OSError, ConnectionRefusedError):
        return False


def wait_for_server(
    host=INSIGHTBOARD_HOST, port=INSIGHTBOARD_PORT, timeout=INSIGHTBOARD_TIMEOUT
) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            if check_port(host, port):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(1)
    raise TimeoutError(f"Server did not start within {timeout} seconds")


def main(debug=False):
    if check_port(INSIGHTBOARD_HOST, INSIGHTBOARD_PORT):
        logging.info("Port is already in use. Opening browser.")
        webbrowser.open(f"http://{INSIGHTBOARD_HOST}:{INSIGHTBOARD_PORT}")
        return
    process = launch_app()
    wait_for_server(
        INSIGHTBOARD_HOST,
        INSIGHTBOARD_PORT,
        INSIGHTBOARD_TIMEOUT,
    )
    webbrowser.open(f"http://{INSIGHTBOARD_HOST}:{INSIGHTBOARD_PORT}")
    process.wait()
