from datetime import datetime, timezone


def normalize_email(email: str) -> str:
    return email.strip().lower()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
