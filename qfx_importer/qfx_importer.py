"""Main application entry point and page registration."""
import reflex as rx

from qfx_importer.database import init_db
from qfx_importer.pages.api_key import api_key_page
from qfx_importer.pages.import_page import import_page
from qfx_importer.pages.index import index_page
from qfx_importer.pages.login import login_page
from qfx_importer.pages.settings import settings_page
from qfx_importer.pages.setup import setup_page
from qfx_importer.state import (
    ApiKeyState,
    AppState,
    ImportState,
    LoginState,
    SettingsState,
    SetupState,
)

# Bootstrap database (creates tables, prints setup token on first run)
init_db()

app = rx.App(
    theme=rx.theme(accent_color="blue", appearance="light"),
)

app.add_page(
    setup_page,
    route="/setup",
    title="Setup – QFX Importer",
    on_load=SetupState.check_setup_page,
)

app.add_page(
    login_page,
    route="/login",
    title="Login – QFX Importer",
    on_load=LoginState.check_login_page,
)

app.add_page(
    index_page,
    route="/",
    title="Dashboard – QFX Importer",
    on_load=AppState.check_auth,
)

app.add_page(
    settings_page,
    route="/settings",
    title="Settings – QFX Importer",
    on_load=SettingsState.load_settings,
)

app.add_page(
    api_key_page,
    route="/api-key",
    title="API Key – QFX Importer",
    on_load=ApiKeyState.load_api_key,
)

app.add_page(
    import_page,
    route="/import",
    title="Import – QFX Importer",
    on_load=ImportState.load_import_page,
)
