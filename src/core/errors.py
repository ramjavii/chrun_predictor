import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class IDSException(Exception):
    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code


async def ids_exception_handler(request: Request, exc: IDSException) -> JSONResponse:
    logger.warning("IDSException: %s", exc.message, extra={"status_code": exc.status_code})
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.critical("Unhandled exception", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
