from fastapi import APIRouter

from app import db
from app.models import ErrorOut, ErrorsResponse

router = APIRouter(prefix="/api/errors", tags=["errors"])


@router.get("", response_model=ErrorsResponse)
async def get_errors() -> ErrorsResponse:
    rows = db.get_recent_errors()
    return ErrorsResponse(
        errors=[
            ErrorOut(
                id=row["id"],
                occurred_at=row["occurred_at"],
                source=row["source"],
                message=row["message"],
                traceback=row["traceback"],
            )
            for row in rows
        ]
    )
