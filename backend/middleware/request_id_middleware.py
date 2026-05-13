import logging
from uuid import uuid4

from fastapi import Request, Response

from core.logger import reset_request_context, set_request_context

logger = logging.getLogger("scmxpertlite.request")


async def request_id_middleware(request: Request, call_next) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    context_tokens = set_request_context(request_id, request.url.path)

    try:
        logger.info("request started")
        response = await call_next(request)
        logger.info("request completed")
    finally:
        reset_request_context(context_tokens)

    response.headers["X-Request-ID"] = request_id
    return response
