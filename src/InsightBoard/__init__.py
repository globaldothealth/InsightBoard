import os
import time
import socket
import logging
import threading
import webbrowser
import subprocess

from waitress import serve

from InsightBoard.app import app  # noqa: F401
from InsightBoard.version import __version__  # noqa: F401

INSIGHTBOARD_HOST = os.getenv("INSIGHTBOARD_HOST", "127.0.0.1")
INSIGHTBOARD_PORT = os.getenv("INSIGHTBOARD_PORT", 8050)
INSIGHTBOARD_TIMEOUT = os.getenv("INSIGHTBOARD_TIMEOUT", 30)


def launch_app():
    logging.getLogger("waitress.queue").setLevel(logging.ERROR)
    serve(app.server, host=INSIGHTBOARD_HOST, port=INSIGHTBOARD_PORT)


def launch_subprocess():
    logging.getLogger("waitress.queue").setLevel(logging.ERROR)
    return subprocess.Popen(
        [
            "waitress-serve",
            "--host",
            INSIGHTBOARD_HOST,
            "--port",
            str(INSIGHTBOARD_PORT),
            "InsightBoard.app:app.server",
        ]
    )


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


def main():
    if check_port(INSIGHTBOARD_HOST, INSIGHTBOARD_PORT):
        logging.info("Port is already in use. Opening browser.")
        webbrowser.open(f"http://{INSIGHTBOARD_HOST}:{INSIGHTBOARD_PORT}")
        return
    # Launch the server in a separate thread
    server_thread = threading.Thread(target=launch_app)
    server_thread.start()
    # Wait for startup before opening web browser
    wait_for_server(
        INSIGHTBOARD_HOST,
        INSIGHTBOARD_PORT,
        INSIGHTBOARD_TIMEOUT,
    )
    webbrowser.open(f"http://{INSIGHTBOARD_HOST}:{INSIGHTBOARD_PORT}")
    # Join the server thread and wait for it to finish or be closed
    server_thread.join()
