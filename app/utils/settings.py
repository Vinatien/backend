import os

from dotenv import load_dotenv

load_dotenv()

# CONFIGS
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

ACCOUNT_SECRET_KEY = os.getenv("ACCOUNT_SECRET_KEY")

# Internal API key for service-to-service communication
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

# DATABASE
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "vinatien_db")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "root")
DB_PORT = os.getenv("DB_PORT", "5432")

# Async for app (using asyncpg for PostgreSQL)
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Sync for migrations (using psycopg2 for PostgreSQL)
SYNC_DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# JWT SETTINGS
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET", "your-access-token-secret-key")
REFRESH_TOKEN_SECRET = os.getenv("REFRESH_TOKEN_SECRET", "your-refresh-token-secret-key")
ACCESS_TOKEN_EXPIRES_IN = int(os.getenv("ACCESS_TOKEN_EXPIRES_IN", 3600))  # 1 hour
REFRESH_TOKEN_EXPIRES_IN = int(os.getenv("REFRESH_TOKEN_EXPIRES_IN", 86400))  # 24 hours
JWT_SIGNING_ALGORITHM = os.getenv("JWT_SIGNING_ALGORITHM", "HS256")

# GOOGLE OAUTH SETTINGS
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URIS = os.getenv("GOOGLE_REDIRECT_URIS", "").split(",")
GOOGLE_REDIRECT_URI = (
    GOOGLE_REDIRECT_URIS[0]
    if GOOGLE_REDIRECT_URIS and GOOGLE_REDIRECT_URIS[0]
    else os.environ.get("GOOGLE_REDIRECT_URI", "")
)
