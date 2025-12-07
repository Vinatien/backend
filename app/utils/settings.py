import os

from dotenv import load_dotenv

load_dotenv()

# CONFIGS
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

ACCOUNT_SECRET_KEY = os.getenv("ACCOUNT_SECRET_KEY")