"""Database models and helpers for qfx_importer."""
import hashlib
import os
import secrets
from datetime import datetime
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select

os.makedirs("data", exist_ok=True)

DATABASE_URL = "sqlite:///data/app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


class AppConfig(SQLModel, table=True):
    """Stores all application configuration and auth state."""

    id: Optional[int] = Field(default=None, primary_key=True)
    setup_complete: bool = False
    setup_token: Optional[str] = None  # plain token, cleared after use
    app_password_hash: Optional[str] = None
    session_token_hash: Optional[str] = None
    api_key_hash: Optional[str] = None
    api_key_prefix: Optional[str] = None  # first 8 chars, for masked display
    actual_base_url: str = "http://localhost:5006"
    actual_password: Optional[str] = None
    actual_file: Optional[str] = None
    actual_encryption_password: Optional[str] = None
    actual_data_dir: str = "data/actual"
    actual_cert: Optional[str] = None


def hash_token(token: str) -> str:
    """SHA-256 hash a random token (for session tokens and API keys)."""
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token(token: str, token_hash: str) -> bool:
    """Verify a plain token against its hash."""
    return hash_token(token) == token_hash


def get_config(session: Session) -> AppConfig:
    """Get (or create) the single AppConfig row."""
    config = session.exec(select(AppConfig)).first()
    if not config:
        config = AppConfig()
        session.add(config)
        session.commit()
        session.refresh(config)
    return config


def init_db() -> None:
    """Create tables and generate setup token if first run."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        config = get_config(session)
        if not config.setup_complete and not config.setup_token:
            token = secrets.token_urlsafe(32)
            config.setup_token = token
            session.add(config)
            session.commit()
            banner = "=" * 64
            print(f"\n{banner}")
            print("  QFX IMPORTER – FIRST-TIME SETUP")
            print(f"  Setup token: {token}")
            print("  Visit /setup in your browser to complete setup.")
            print(f"{banner}\n")
