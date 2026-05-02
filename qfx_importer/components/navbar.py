"""Top navigation bar component."""
import reflex as rx

from qfx_importer.state import AppState


def navbar() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.link(
                rx.heading("QFX Importer", size="4"),
                href="/",
                text_decoration="none",
                color_scheme="gray",
            ),
            rx.spacer(),
            rx.cond(
                AppState.is_authenticated,
                rx.hstack(
                    rx.link("Dashboard", href="/", size="2"),
                    rx.link("Settings", href="/settings", size="2"),
                    rx.link("API Key", href="/api-key", size="2"),
                    rx.link("Import", href="/import", size="2"),
                    rx.button(
                        "Logout",
                        on_click=AppState.logout,
                        size="2",
                        variant="soft",
                        color_scheme="red",
                    ),
                    spacing="4",
                    align="center",
                ),
                rx.fragment(),
            ),
            align="center",
            width="100%",
        ),
        width="100%",
        padding_x="6",
        padding_y="4",
        border_bottom="1px solid var(--gray-4)",
        background="var(--color-background)",
        position="sticky",
        top="0",
        z_index="100",
    )
