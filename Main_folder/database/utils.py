# database/utils.py

from .db import SessionLocal
from .models import VisitorLog, User


def log_visitor(name: str, purpose: str = None):
    """
    Add a visitor entry to the VisitorLog table.
    Returns the created VisitorLog object.
    """
    db = SessionLocal()

    try:
        log = VisitorLog(name=name, purpose=purpose)
        db.add(log)
        db.commit()
        db.refresh(log)

        print(f"[DB] Logged visitor: {name}, id: {log.id}, time: {log.timestamp} purpose={purpose}")
        return log

    except Exception as e:
        print("[DB] Error logging visitor:", e)
        db.rollback()
        raise e

    finally:
        db.close()


def clear_all_visitors():
    """
    Delete ALL rows from VisitorLog.
    Use carefully.
    """
    db = SessionLocal()

    try:
        deleted = db.query(VisitorLog).delete()
        db.commit()
        print(f"[DB] Cleared {deleted} visitor logs.")

    except Exception as e:
        print("[DB] Error clearing visitor logs:", e)
        db.rollback()
        raise e

    finally:
        db.close()

def print_all_visitors():
    """
    Print all rows in VisitorLog table to the terminal.
    """
    db = SessionLocal()

    try:
        logs = db.query(VisitorLog).all()

        if not logs:
            print("[DB] No visitor logs found.")
            return

        print("\n[DB] --- Visitor Logs ---")
        for l in logs:
            print(f"ID={l.id} | Time={l.timestamp} | Name={l.name} | Purpose={l.purpose}")
        print("[DB] ---------------------\n")

    except Exception as e:
        print("[DB] Error printing logs:", e)

    finally:
        db.close()

# =======================
# USER HELPERS
# =======================

def create_user(email: str, password: str):
    """
    Create a new user with email + password.
    WARNING: password is stored as plain text (OK for local dev, NOT for production).
    """
    db = SessionLocal()
    try:
        # check if user already exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"[DB] User already exists: {email} (id={existing.id})")
            return existing

        user = User(email=email, password=password)
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"[DB] Created user: {email} (id={user.id})")
        return user

    except Exception as e:
        print("[DB] Error creating user:", e)
        db.rollback()
        raise e

    finally:
        db.close()


def get_user_by_email(email: str):
    """
    Fetch a user by email, or return None.
    """
    db = SessionLocal()
    try:
        return db.query(User).filter(User.email == email).first()
    finally:
        db.close()


def authenticate_user(email: str, password: str):
    """
    Check email + password.
    Return User if valid, else None.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            print(f"[DB] Login failed: no such user {email}")
            return None
        if user.password != password:
            print(f"[DB] Login failed: wrong password for {email}")
            return None
        print(f"[DB] Login success: {email}")
        return user
    finally:
        db.close()


def print_all_users():
    """
    Print all users.
    """
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if not users:
            print("[DB] No users found.")
            return

        print("\n[DB] --- Users ---")
        for u in users:
            print(f"ID={u.id} | Email={u.email} | Password={u.password}")
        print("[DB] -------------\n")
    finally:
        db.close()

def clear_all_users():
    """
    Delete ALL rows from User table.
    Use carefully.
    """
    db = SessionLocal()

    try:
        deleted = db.query(User).delete()
        db.commit()
        print(f"[DB] Cleared {deleted} users.")

    except Exception as e:
        print("[DB] Error clearing users:", e)
        db.rollback()
        raise e

    finally:
        db.close()

from housepass import getpass
HOUSE_PASSWORD = getpass()   # hardcoded for now


def create_user_secure(email: str, password: str, house_password: str):
    """
    Create a new user ONLY if the house password matches.
    Returns:
        - User object if created
        - None if creation failed
    """
    # Step 1: verify house password
    if house_password != HOUSE_PASSWORD:
        print("[DB] Wrong house password. User creation denied.")
        return None

    db = SessionLocal()
    try:
        # Step 2: check if email already exists
        existing = db.query(User).filter(User.email == email).first()
        print(existing)
        if existing:
            print("HI")
            print(f"[DB] User already exists: {email} (id={existing.id})")
            return "Existing"

        # Step 3: create new user
        user = User(email=email, password=password)
        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"[DB] Created user: {email} (id={user.id})")
        return user

    except Exception as e:
        print("[DB] Error creating user:", e)
        db.rollback()
        raise e

    finally:
        db.close()
