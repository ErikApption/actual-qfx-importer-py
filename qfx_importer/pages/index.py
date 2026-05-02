"""Dashboard / index page."""
import reflex as rx

from qfx_importer.components.navbar import navbar
from qfx_importer.state import AppState


def _nav_card(title: str, description: str, href: str, icon: str) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.icon(icon, size=28, color="var(--accent-9)"),
            rx.heading(title, size="4"),
            rx.text(description, size="2", color_scheme="gray"),
            rx.button(
                f"Go to {title}",
                variant="soft",
                size="2",
                on_click=rx.redirect(href),
            ),
            spacing="3",
            align="center",
        ),
        width="240px",
        padding="5",
        _hover={"box_shadow": "var(--shadow-3)"},
    )


def index_page() -> rx.Component:
    return rx.vstack(
        navbar(),
        rx.box(
            rx.vstack(
                rx.heading("Welcome to QFX Importer", size="7", margin_bottom="2"),
                rx.text(
                    "Seamlessly import QFX/OFX bank transactions into your Actual Budget.",
                    size="3",
                    color_scheme="gray",
                ),
                rx.divider(margin_y="4"),
                rx.hstack(
                    _nav_card(
                        "Settings",
                        "Configure your Actual Budget connection.",
                        "/settings",
                        "settings",
                    ),
                    _nav_card(
                        "API Key",
                        "Manage your API key and app password.",
                        "/api-key",
                        "key",
                    ),
                    _nav_card(
                        "Import",
                        "Upload and import QFX / OFX files.",
                        "/import",
                        "upload",
                    ),
                    spacing="5",
                    wrap="wrap",
                    justify="center",
                ),
                spacing="4",
                align="center",
                padding_top="8",
            ),
            width="100%",
            padding="8",
        ),
        width="100%",
        min_height="100vh",
        background="var(--gray-1)",
        spacing="0",
    )
