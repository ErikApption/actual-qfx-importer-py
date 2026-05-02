"""Application state for qfx_importer."""
import logging
import os
import secrets
from typing import Optional

import reflex as rx
from passlib.context import CryptContext
from sqlmodel import Session, select

from qfx_importer.database import (
    AppConfig,
    engine,
    get_config,
    hash_token,
    verify_token,
)
from qfx_importer.importer import parse_qfx, import_transactions

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Base / auth state
# ---------------------------------------------------------------------------


class AppState(rx.State):
    """Shared authentication state."""

    session_token: str = rx.LocalStorage("")
    is_authenticated: bool = False

    def check_auth(self):
        """Called on_load for authenticated pages."""
        with Session(engine) as session:
            config = get_config(session)
            if not config.setup_complete:
                return rx.redirect("/setup")
        if not self.session_token:
            return rx.redirect("/login")
        with Session(engine) as session:
            config = get_config(session)
            if config.session_token_hash and verify_token(
                self.session_token, config.session_token_hash
            ):
                self.is_authenticated = True
            else:
                self.is_authenticated = False
                return rx.redirect("/login")

    def check_setup_page(self):
        """Called on_load for /setup – redirect away if already set up."""
        with Session(engine) as session:
            config = get_config(session)
            if config.setup_complete:
                return rx.redirect("/login")

    def check_login_page(self):
        """Called on_load for /login – redirect to dashboard if already authed."""
        with Session(engine) as session:
            config = get_config(session)
            if not config.setup_complete:
                return rx.redirect("/setup")
        if self.session_token:
            with Session(engine) as session:
                config = get_config(session)
                if config.session_token_hash and verify_token(
                    self.session_token, config.session_token_hash
                ):
                    return rx.redirect("/")

    def logout(self):
        """Invalidate session."""
        self.session_token = ""
        self.is_authenticated = False
        with Session(engine) as session:
            config = get_config(session)
            config.session_token_hash = None
            session.add(config)
            session.commit()
        return rx.redirect("/login")


# ---------------------------------------------------------------------------
# Setup page state
# ---------------------------------------------------------------------------


class SetupState(AppState):
    setup_token_input: str = ""
    new_password: str = ""
    confirm_password: str = ""
    error: str = ""
    success: str = ""

    def handle_setup(self):
        self.error = ""
        if not self.setup_token_input or not self.new_password:
            self.error = "All fields are required."
            return
        if self.new_password != self.confirm_password:
            self.error = "Passwords do not match."
            return
        if len(self.new_password) < 12:
            self.error = "Password must be at least 12 characters."
            return
        with Session(engine) as session:
            config = get_config(session)
            if config.setup_complete:
                self.error = "Setup already complete."
                return
            if not config.setup_token or not secrets.compare_digest(
                config.setup_token, self.setup_token_input
            ):
                self.error = "Invalid setup token."
                return
            config.app_password_hash = pwd_context.hash(self.new_password)
            config.setup_token = None
            config.setup_complete = True
            session.add(config)
            session.commit()
        self.success = "Setup complete! Redirecting to login…"
        return rx.redirect("/login")


# ---------------------------------------------------------------------------
# Login page state
# ---------------------------------------------------------------------------


class LoginState(AppState):
    password_input: str = ""
    error: str = ""

    def handle_login(self):
        self.error = ""
        with Session(engine) as session:
            config = get_config(session)
            if not config.setup_complete or not config.app_password_hash:
                self.error = "App not set up yet."
                return rx.redirect("/setup")
            if not pwd_context.verify(self.password_input, config.app_password_hash):
                self.error = "Invalid password."
                return
            token = secrets.token_urlsafe(32)
            config.session_token_hash = hash_token(token)
            session.add(config)
            session.commit()
        self.session_token = token
        self.is_authenticated = True
        return rx.redirect("/")


# ---------------------------------------------------------------------------
# Settings page state
# ---------------------------------------------------------------------------


class SettingsState(AppState):
    base_url: str = ""
    actual_password: str = ""
    file_name: str = ""
    encryption_password: str = ""
    data_dir: str = ""
    cert: str = ""
    status_msg: str = ""
    status_ok: bool = False

    def load_settings(self):
        """Load saved settings from DB."""
        result = self.check_auth()
        if result:
            return result
        with Session(engine) as session:
            config = get_config(session)
            self.base_url = config.actual_base_url or ""
            self.actual_password = config.actual_password or ""
            self.file_name = config.actual_file or ""
            self.encryption_password = config.actual_encryption_password or ""
            self.data_dir = config.actual_data_dir or "data/actual"
            self.cert = config.actual_cert or ""

    def save_settings(self):
        self.status_msg = ""
        with Session(engine) as session:
            config = get_config(session)
            config.actual_base_url = self.base_url
            config.actual_password = self.actual_password or None
            config.actual_file = self.file_name or None
            config.actual_encryption_password = self.encryption_password or None
            config.actual_data_dir = self.data_dir or "data/actual"
            config.actual_cert = self.cert or None
            session.add(config)
            session.commit()
        self.status_msg = "Settings saved."
        self.status_ok = True

    def test_connection(self):
        self.status_msg = ""
        self.status_ok = False
        try:
            from actual import Actual

            with Session(engine) as session:
                config = get_config(session)
            cert: bool | str = True
            if config.actual_cert:
                cert = config.actual_cert
            with Actual(
                base_url=config.actual_base_url,
                password=config.actual_password,
                file=config.actual_file,
                encryption_password=config.actual_encryption_password or None,
                data_dir=config.actual_data_dir or "data/actual",
                cert=cert,
            ):
                pass
            self.status_msg = "Connection successful!"
            self.status_ok = True
        except Exception as exc:
            logger.error("Actual connection test failed: %s", exc)
            self.status_msg = "Connection failed. Check your settings and server logs for details."
            self.status_ok = False


# ---------------------------------------------------------------------------
# API Key page state
# ---------------------------------------------------------------------------


class ApiKeyState(AppState):
    masked_key: str = ""
    new_password: str = ""
    confirm_password: str = ""
    regen_msg: str = ""
    regen_ok: bool = False
    pw_msg: str = ""
    pw_ok: bool = False
    copied: bool = False
    # Holds the newly generated key just once (cleared after display)
    new_key_plain: str = ""

    def load_api_key(self):
        result = self.check_auth()
        if result:
            return result
        with Session(engine) as session:
            config = get_config(session)
            if config.api_key_prefix:
                self.masked_key = config.api_key_prefix + "..." + "****"
            else:
                self.masked_key = "(no API key generated)"

    def regenerate_key(self):
        self.regen_msg = ""
        plain_key = secrets.token_urlsafe(32)
        with Session(engine) as session:
            config = get_config(session)
            config.api_key_hash = hash_token(plain_key)
            config.api_key_prefix = plain_key[:8]
            session.add(config)
            session.commit()
        self.masked_key = plain_key[:8] + "..." + "****"
        self.new_key_plain = plain_key
        self.regen_msg = "New API key generated. Copy it now – it won't be shown again."
        self.regen_ok = True

    def dismiss_new_key(self):
        self.new_key_plain = ""

    def change_password(self):
        self.pw_msg = ""
        self.pw_ok = False
        if not self.new_password:
            self.pw_msg = "Password cannot be empty."
            return
        if self.new_password != self.confirm_password:
            self.pw_msg = "Passwords do not match."
            return
        if len(self.new_password) < 12:
            self.pw_msg = "Password must be at least 12 characters."
            return
        with Session(engine) as session:
            config = get_config(session)
            config.app_password_hash = pwd_context.hash(self.new_password)
            session.add(config)
            session.commit()
        self.new_password = ""
        self.confirm_password = ""
        self.pw_msg = "Password updated successfully."
        self.pw_ok = True


# ---------------------------------------------------------------------------
# Import page state
# ---------------------------------------------------------------------------


class ImportState(AppState):
    import_results: list[str] = []
    import_errors: list[str] = []
    is_importing: bool = False

    def load_import_page(self):
        result = self.check_auth()
        if result:
            return result
        self.import_results = []
        self.import_errors = []

    async def handle_upload(self, files: list[rx.UploadFile]):
        if not files:
            self.import_errors = ["No files selected."]
            return

        self.is_importing = True
        self.import_results = []
        self.import_errors = []
        yield

        with Session(engine) as session:
            config = get_config(session)
            base_url = config.actual_base_url
            actual_password = config.actual_password
            actual_file = config.actual_file
            encryption_password = config.actual_encryption_password
            data_dir = config.actual_data_dir or "data/actual"
            actual_cert: bool | str = True
            if config.actual_cert:
                actual_cert = config.actual_cert

        if not base_url or not actual_file:
            self.import_errors = [
                "Actual settings not configured. Please visit /settings first."
            ]
            self.is_importing = False
            return

        from actual import Actual
        from actual.database import Accounts
        from sqlmodel import select as sa_select

        os.makedirs(data_dir, exist_ok=True)

        for upload_file in files:
            filename = upload_file.filename
            content = await upload_file.read()

            # 1. Parse QFX/OFX content
            try:
                parsed_accounts = parse_qfx(content)
            except Exception as exc:
                logger.error("QFX parse error for %s: %s", filename, exc)
                self.import_errors.append(
                    f"{filename}: failed to parse file. Check the server logs for details."
                )
                continue

            # 2. Connect to Actual and import
            try:
                with Actual(
                    base_url=base_url,
                    password=actual_password,
                    file=actual_file,
                    encryption_password=encryption_password or None,
                    data_dir=data_dir,
                    cert=actual_cert,
                ) as a:
                    for parsed_account in parsed_accounts:
                        # Resolve account by account_id (name or id)
                        account_obj = a.session.exec(
                            sa_select(Accounts).where(
                                Accounts.name == parsed_account.account_id
                            )
                        ).first() or a.session.exec(
                            sa_select(Accounts).where(
                                Accounts.id == parsed_account.account_id
                            )
                        ).first()

                        if account_obj is None:
                            logger.warning(
                                "Account %r not found in Actual for file %s",
                                parsed_account.account_id,
                                filename,
                            )
                            self.import_errors.append(
                                f"{filename}: account '{parsed_account.account_id}' not found in Actual Budget."
                            )
                            continue

                        result = import_transactions(
                            a.session,
                            account_obj,
                            parsed_account.transactions,
                            filename=filename,
                        )
                        self.import_results.append(
                            f"{filename}: imported {result.imported_count} transaction(s)."
                        )
                        if result.errors:
                            self.import_errors.extend(
                                [f"{filename} row error: {e}" for e in result.errors[:5]]
                            )
                    a.commit()
            except Exception as exc:
                logger.error(
                    "Actual connection error while importing %s: %s", filename, exc
                )
                self.import_errors.append(
                    f"{filename}: failed to connect to Actual Budget. Check Settings and server logs."
                )
                continue

        self.is_importing = False
