from fastapi import Request
from fastapi.responses import JSONResponse

from app.types.exceptions import (
    AuthenticationException,
    AuthorizationException,
    BusinessRuleException,
    ConflictException,
    NotFoundException,
    ResourceNotFound,
)


def set_up_exception_handler(app):
    @app.exception_handler(BusinessRuleException)
    async def handle_business_error(_: Request, exc: BusinessRuleException):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ConflictException)
    async def handle_conflict(_: Request, exc: ConflictException):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(NotFoundException)
    @app.exception_handler(ResourceNotFound)
    async def handle_not_found(_: Request, exc: Exception):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(AuthenticationException)
    async def handle_auth_error(_: Request, exc: AuthenticationException):
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    @app.exception_handler(AuthorizationException)
    async def handle_forbidden(_: Request, exc: AuthorizationException):
        return JSONResponse(status_code=403, content={"detail": str(exc)})
