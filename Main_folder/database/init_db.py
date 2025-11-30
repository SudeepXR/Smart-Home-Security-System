# database/init_db.py

from .db import init_db

if __name__ == "__main__":
    print("[DB] Initializing database...")
    init_db()
    print("[DB] Done.")
