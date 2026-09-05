import asyncio
import queue

from fastapi import APIRouter, HTTPException

from app.auth import service, session
from app.models import (
    AuthStatusResponse,
    LoginCompleteRequest,
    LoginCompleteResponse,
    LoginStartRequest,
    LoginStartResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

LOGIN_URL_TIMEOUT_SECONDS = 30
LOGIN_COMPLETE_TIMEOUT_SECONDS = 30


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status() -> AuthStatusResponse:
    return AuthStatusResponse(authenticated=service.is_logged_in())


@router.post("/login/start", response_model=LoginStartResponse)
async def login_start(body: LoginStartRequest) -> LoginStartResponse:
    handshake = session.start(body.locale)
    try:
        login_url = await asyncio.to_thread(
            handshake.url_queue.get, timeout=LOGIN_URL_TIMEOUT_SECONDS
        )
    except queue.Empty:
        session.discard(handshake.id)
        raise HTTPException(status_code=504, detail="Timed out waiting for a login URL")
    return LoginStartResponse(session_id=handshake.id, login_url=login_url)


@router.post("/login/complete", response_model=LoginCompleteResponse)
async def login_complete(body: LoginCompleteRequest) -> LoginCompleteResponse:
    handshake = session.get(body.session_id)
    if handshake is None:
        raise HTTPException(status_code=404, detail="Unknown or expired login session")

    handshake.postlogin_queue.put(body.postlogin_url)
    finished = await asyncio.to_thread(
        handshake.done_event.wait, LOGIN_COMPLETE_TIMEOUT_SECONDS
    )
    if not finished:
        raise HTTPException(status_code=504, detail="Timed out completing login")

    session.discard(handshake.id)
    if handshake.error is not None:
        return LoginCompleteResponse(success=False, error=str(handshake.error))
    return LoginCompleteResponse(success=True)


@router.post("/logout")
async def logout() -> dict:
    service.logout()
    return {"success": True}
