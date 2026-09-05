import json

import app.db as db_module
from app.models import BookIn


def test_upsert_and_get_book(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    db_module.init_db()

    book = BookIn(asin="B000TEST01", title="Test Book", authors=["Jane Author"], narrators=["Nar Rator"])
    db_module.upsert_book(book)

    rows = db_module.get_all_books()
    assert len(rows) == 1
    assert rows[0]["asin"] == "B000TEST01"
    assert json.loads(rows[0]["authors_json"]) == ["Jane Author"]

    fetched = db_module.get_book_by_asin("B000TEST01")
    assert fetched is not None
    assert fetched["title"] == "Test Book"

    assert db_module.get_book_by_asin("NOPE") is None


def test_upsert_book_updates_existing_row(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    db_module.init_db()

    db_module.upsert_book(BookIn(asin="B000TEST02", title="Original Title"))
    db_module.upsert_book(BookIn(asin="B000TEST02", title="Updated Title"))

    rows = db_module.get_all_books()
    assert len(rows) == 1
    assert rows[0]["title"] == "Updated Title"
