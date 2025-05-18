from fastapi import Request
from fastapi.responses import JSONResponse

async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred"},
        )