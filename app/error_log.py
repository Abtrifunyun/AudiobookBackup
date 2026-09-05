import logging
import traceback as traceback_module

from app import db


def log_exception(source: str, exc: BaseException) -> None:
    logging.getLogger(source).exception(str(exc))
    db.log_error(source, str(exc), traceback_module.format_exc())
