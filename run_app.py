import threading
import time

import httpx
import uvicorn
import webview

from app.main import app as fastapi_app

HOST = "127.0.0.1"
PORT = 8000


def _run_server() -> None:
    uvicorn.run(fastapi_app, host=HOST, port=PORT)


def _wait_for_server(timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    url = f"http://{HOST}:{PORT}/api/health"
    while time.monotonic() < deadline:
        try:
            if httpx.get(url, timeout=0.5).status_code == 200:
                return True
        except httpx.HTTPError:
            pass
        time.sleep(0.1)
    return False


def main() -> None:
    threading.Thread(target=_run_server, daemon=True).start()
    _wait_for_server()
    webview.create_window(
        "Audiobook Backup",
        f"http://{HOST}:{PORT}",
        width=1100,
        height=800,
        min_size=(480, 400),
    )
    webview.start()


if __name__ == "__main__":
    main()
