"""
Run once to create all tables in the configured PostgreSQL database:

    python3 init_db.py

Requires DATABASE_URL in .env to point at a running, reachable PostgreSQL
instance, and the backend dependencies from requirements.txt to be installed.
"""
from app.database import init_db

if __name__ == "__main__":
    init_db()
    print("Tables created (or already existed).")
