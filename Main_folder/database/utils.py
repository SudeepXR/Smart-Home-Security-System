from .db import SessionLocal
from .models import User, VisitorLog
from passlib.context import CryptContext

# =======================
# PASSWORD UTILS
# =======================

from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

# =======================
# USER FUNCTIONS
# =======================

def create_user(username, password, doorbell_ip, cctv_ip, file_destination=None):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"[DB] User already exists: {username}")
            return existing

        user = User(
            username=username,
            password_hash=hash_password(password),
            doorbell_ip=doorbell_ip,
            cctv_ip=cctv_ip,
            file_destination=file_destination
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"[DB] Created user: {username} (id={user.id})")
        return user
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def authenticate_user(username, password):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print("[DB] Login failed: no such user")
            return None

        if not verify_password(password, user.password_hash):
            print("[DB] Login failed: wrong password")
            return None

        print("[DB] Login success")
        return user
    finally:
        db.close()


def print_all_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if not users:
            print("[DB] No users found.")
            return

        print("\n[DB] --- USERS ---")
        for u in users:
            print(
                f"ID={u.id} | username={u.username} | "
                f"doorbell={u.doorbell_ip} | cctv={u.cctv_ip} | "
                f"files={u.file_destination}"
            )
        print("[DB] -------------\n")
    finally:
        db.close()


def clear_all_users():
    db = SessionLocal()
    try:
        deleted = db.query(User).delete()
        db.commit()
        print(f"[DB] Cleared {deleted} users.")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


# =======================
# VISITOR LOG FUNCTIONS
# =======================
from datetime import datetime, timedelta

def log_visitor(user_id: int, name: str, purpose: str = None):
    db = SessionLocal()
    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    try:
        log = VisitorLog(
            user_id=user_id,
            timestamp=ist_now,
            name=name,
            purpose=purpose
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        print(f"[DB] Visitor logged for user {user_id}: {name}")
        return log
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_visitors_for_user(user_id: int):
    db = SessionLocal()
    try:
        return (
            db.query(VisitorLog)
            .filter(VisitorLog.user_id == user_id)
            .order_by(VisitorLog.timestamp.desc())
            .all()
        )
    finally:
        db.close()


def clear_visitors_for_user(user_id: int):
    db = SessionLocal()
    try:
        deleted = (
            db.query(VisitorLog)
            .filter(VisitorLog.user_id == user_id)
            .delete()
        )
        db.commit()
        print(f"[DB] Cleared {deleted} visitor logs for user {user_id}")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

from datetime import datetime, date
from sqlalchemy import and_

def get_today_visitors_for_user(user_id: int):
    """
    Get only today's visitor logs for a specific user.
    """
    db = SessionLocal()
    try:
        today = date.today()

        logs = (
            db.query(VisitorLog)
            .filter(
                VisitorLog.user_id == user_id,
                VisitorLog.timestamp >= datetime.combine(today, datetime.min.time()),
                VisitorLog.timestamp <= datetime.combine(today, datetime.max.time())
            )
            .order_by(VisitorLog.timestamp.desc())
            .all()
        )

        return logs
    finally:
        db.close()

import base64
from .db import SessionLocal
from .models import VisitorLog

def get_visitors_with_pics_for_user(user_id: int):
    db = SessionLocal()
    try:
        logs = (
            db.query(VisitorLog)
            .filter(VisitorLog.user_id == user_id)
            .order_by(VisitorLog.timestamp.desc())
            .all()
        )

        results = []
        for l in logs:
            img_b64 = None
            if l.photo:
                img_b64 = base64.b64encode(l.photo).decode("utf-8")

            results.append({
                "id": l.id,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
                "name": l.name,
                "purpose": l.purpose,
                "image": img_b64,
                "flag": l.flag     # ✅ THIS LINE IS REQUIRED
            })

        return results
    finally:
        db.close()




import os
from datetime import datetime, timedelta

FACE_IMAGE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "Face", "alert_frame.jpg")
)


def log_visitor(user_id: int, name: str, purpose: str = None, message_id: str = None):
    db = SessionLocal()
    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)

    photo_bytes = None
    if os.path.exists(FACE_IMAGE_PATH):
        with open(FACE_IMAGE_PATH, "rb") as f:
            photo_bytes = f.read()

    try:
        log = VisitorLog(
            user_id=user_id,
            timestamp=ist_now,
            name=name,
            purpose=purpose,
            photo=photo_bytes,       # ✅ image stored
            message_id=message_id    # ✅ message ID stored
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        print(f"[DB] Visitor logged for user {user_id}: {name}")
        return log
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
