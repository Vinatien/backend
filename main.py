from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.google_auth import router as google_auth_router
from app.api.health import router as health_router
from app.api.bank_accounts import router as bank_accounts_router
from app.handlers.exception_handlers import set_up_exception_handler

# from app.api.users.routes import router as users_router
from app.middlewares.cors_middleware import setup_cors

app = FastAPI(title="VinaTien Backend Service", version="1.0.0")

setup_cors(app)
set_up_exception_handler(app)


@app.get("/", tags=["Root"])
async def welcome_root():
    return {"message": "Welcome to the VinaTien Backend Service!!!"}


app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(google_auth_router, prefix="/api/auth/google", tags=["Google OAuth"])
app.include_router(health_router, prefix="/api/health", tags=["Health"])
app.include_router(bank_accounts_router, prefix="/api/bank-accounts", tags=["Bank Accounts"])
# app.include_router(users_router, prefix="/api/users", tags=["Users"])
