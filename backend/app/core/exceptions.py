"""Application error types and the consistent error envelope."""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(HTTPException):
    """HTTP error carrying a stable machine-readable code."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: object | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details

    def envelope(self) -> dict:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class NotFound(AppError):
    def __init__(self, message: str = "Resource not found.", code: str = "not_found") -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, code, message)


class Forbidden(AppError):
    def __init__(self, message: str = "You may not access this resource.") -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, "forbidden", message)


class Unauthorized(AppError):
    def __init__(self, message: str = "Authentication required.") -> None:
        super().__init__(
            status.HTTP_401_UNAUTHORIZED,
            "unauthorized",
            message,
            details=None,
        )


class Conflict(AppError):
    def __init__(self, message: str, code: str = "conflict") -> None:
        super().__init__(status.HTTP_409_CONFLICT, code, message)


class InvalidRequest(AppError):
    def __init__(self, message: str, code: str = "invalid_request") -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, code, message)


class Unavailable(AppError):
    def __init__(self, message: str, code: str = "unavailable") -> None:
        super().__init__(status.HTTP_503_SERVICE_UNAVAILABLE, code, message)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.envelope(),
            headers=headers,
        )

    @app.exception_handler(HTTPException)
    async def _http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "http_error",
                    "message": str(exc.detail),
                    "details": None,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed.",
                    "details": [
                        {"field": ".".join(str(part) for part in error["loc"][1:]), "message": error["msg"]}
                        for error in exc.errors()
                    ],
                }
            },
        )
