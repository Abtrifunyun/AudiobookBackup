import queue
import threading
import uuid
from typing import Optional

import audible

from app.auth.service import login_external
from app.error_log import log_exception

POSTLOGIN_TIMEOUT_SECONDS = 600


class LoginHandshake:
    def __init__(self, locale: str):
        self.id = uuid.uuid4().hex
        self.locale = locale
        self.url_queue: "queue.Queue[str]" = queue.Queue(maxsize=1)
        self.postlogin_queue: "queue.Queue[str]" = queue.Queue(maxsize=1)
        self.done_event = threading.Event()
        self.result: Optional[audible.Authenticator] = None
        self.error: Optional[BaseException] = None


_active: dict[str, LoginHandshake] = {}


def start(locale: str) -> LoginHandshake:
    handshake = LoginHandshake(locale)
    _active[handshake.id] = handshake

    def callback(login_url: str) -> str:
        handshake.url_queue.put(login_url)
        return handshake.postlogin_queue.get(timeout=POSTLOGIN_TIMEOUT_SECONDS)

    def run() -> None:
        try:
            handshake.result = login_external(handshake.locale, callback)
        except BaseException as exc:
            handshake.error = exc
            log_exception(f"auth.login:{handshake.id}", exc)
        finally:
            handshake.done_event.set()

    threading.Thread(target=run, daemon=True).start()
    return handshake


def get(session_id: str) -> Optional[LoginHandshake]:
    return _active.get(session_id)


def discard(session_id: str) -> None:
    _active.pop(session_id, None)
