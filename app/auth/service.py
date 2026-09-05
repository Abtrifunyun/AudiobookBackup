from typing import Callable

import audible

from app.config import AUTH_FILE_PATH, DEFAULT_LOCALE


class AuthNotFoundError(Exception):
    pass


def is_logged_in() -> bool:
    return AUTH_FILE_PATH.exists()


def load_authenticator() -> audible.Authenticator:
    if not is_logged_in():
        raise AuthNotFoundError(f"No credentials found at {AUTH_FILE_PATH}")
    return audible.Authenticator.from_file(AUTH_FILE_PATH)


def login_external(locale: str, login_url_callback: Callable[[str], str]) -> audible.Authenticator:
    auth = audible.Authenticator.from_login_external(
        locale=locale or DEFAULT_LOCALE,
        login_url_callback=login_url_callback,
    )
    AUTH_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    auth.to_file(AUTH_FILE_PATH, encryption=False)
    return auth


def logout() -> None:
    AUTH_FILE_PATH.unlink(missing_ok=True)
