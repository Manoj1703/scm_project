from fastapi import HTTPException, Request

from backend.services.auth_service import decode_access_token


async def auth_context_middleware(request: Request, call_next):
    auth_header = request.headers.get("authorization", "")
    request.state.access_token_payload = None
    request.state.authenticated_user_id = None

    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        if token:
            try:
                payload = decode_access_token(token)
            except HTTPException:
                payload = None
            else:
                request.state.access_token_payload = payload
                request.state.authenticated_user_id = payload.get("sub")

    return await call_next(request)
