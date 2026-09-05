import logging
from typing import Any, Optional

import audible
import httpx

from app.config import COVERS_DIR
from app.models import BookIn

logger = logging.getLogger(__name__)

LIBRARY_RESPONSE_GROUPS = "contributors,product_desc,product_attrs,media,series,relationships"
LIBRARY_NUM_RESULTS = 999


async def fetch_library(auth: audible.Authenticator) -> list[BookIn]:
    async with audible.AsyncClient(auth) as client:
        response = await client.get(
            path="library",
            params={
                "num_results": LIBRARY_NUM_RESULTS,
                "response_groups": LIBRARY_RESPONSE_GROUPS,
            },
        )
    return [_book_in_from_item(item) for item in response.get("items", [])]


def _book_in_from_item(item: dict[str, Any]) -> BookIn:
    authors = [a.get("name") for a in item.get("authors") or [] if a.get("name")]
    narrators = [n.get("name") for n in item.get("narrators") or [] if n.get("name")]

    series_list = item.get("series") or []
    series_title = series_list[0].get("title") if series_list else None
    series_sequence = series_list[0].get("sequence") if series_list else None

    product_images = item.get("product_images") or {}
    cover_url = (
        product_images.get("500")
        or product_images.get("1000")
        or next(iter(product_images.values()), None)
    )

    library_status = item.get("library_status") or {}

    return BookIn(
        asin=item["asin"],
        title=item.get("title", "Unknown title"),
        subtitle=item.get("subtitle"),
        authors=authors,
        narrators=narrators,
        publisher=item.get("publisher_name"),
        series_title=series_title,
        series_sequence=series_sequence,
        language=item.get("language"),
        isbn=item.get("isbn"),
        summary=item.get("publisher_summary") or item.get("merchandising_summary"),
        runtime_length_min=item.get("runtime_length_min"),
        release_date=item.get("release_date"),
        purchase_date=item.get("purchase_date") or library_status.get("date_added"),
        cover_url=cover_url,
        raw_metadata=item,
    )


async def cache_cover(asin: str, cover_url: Optional[str]) -> Optional[str]:
    if not cover_url:
        return None
    filename = f"{asin}.jpg"
    dest = COVERS_DIR / filename
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(cover_url)
            response.raise_for_status()
            dest.write_bytes(response.content)
    except Exception:
        logger.warning("Failed to cache cover for %s", asin, exc_info=True)
        return None
    return filename
