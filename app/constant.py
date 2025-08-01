import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/projectdb")
API_ROOT = "http://localhost:8000"
CACHE_TTL = 600
