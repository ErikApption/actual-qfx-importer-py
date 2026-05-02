"""Settings page – configure Actual Budget connection."""
import reflex as rx

from qfx_importer.components.navbar import navbar
from qfx_importer.state import SettingsState


def settings_page() -> rx.Component:
    return rx.vstack(
        navbar(),
        rx.box(
            rx.card(
                rx.vstack(
                    rx.heading("Actual Budget Settings", size="5"),
                    rx.text(
                        "Connection parameters for your Actual Budget server.",
                        size="2",
                        color_scheme="gray",
                    ),
                    rx.divider(),
                    rx.grid(
                        rx.text("Server URL", size="2", weight="medium"),
                        rx.input(
                            placeholder="http://localhost:5006",
                            value=SettingsState.base_url,
                            on_change=SettingsState.set_base_url,
                        ),
                        rx.text("Server Password", size="2", weight="medium"),
                        rx.input(
                            placeholder="Actual server password",
                            type="password",
                            value=SettingsState.actual_password,
                            on_change=SettingsState.set_actual_password,
                        ),
                        rx.text("Budget File / Name", size="2", weight="medium"),
                        rx.input(
                            placeholder="My Budget",
                            value=SettingsState.file_name,
                            on_change=SettingsState.set_file_name,
                        ),
                        rx.text(
                            "Encryption Password", size="2", weight="medium"
                        ),
                        rx.input(
                            placeholder="(optional)",
                            type="password",
                            value=SettingsState.encryption_password,
                            on_change=SettingsState.set_encryption_password,
                        ),
                        rx.text("Data Directory", size="2", weight="medium"),
                        rx.input(
                            placeholder="data/actual",
                            value=SettingsState.data_dir,
                            on_change=SettingsState.set_data_dir,
                        ),
                        rx.text(
                            "TLS Certificate Path / Bool",
                            size="2",
                            weight="medium",
                        ),
                        rx.input(
                            placeholder="/path/to/cert.pem  or leave blank for default",
                            value=SettingsState.cert,
                            on_change=SettingsState.set_cert,
                        ),
                        columns="2",
                        gap="3",
                        width="100%",
                    ),
                    rx.cond(
                        SettingsState.status_msg != "",
                        rx.callout(
                            SettingsState.status_msg,
                            icon=rx.cond(
                                SettingsState.status_ok,
                                "circle_check",
                                "triangle_alert",
                            ),
                            color_scheme=rx.cond(
                                SettingsState.status_ok, "green", "red"
                            ),
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    rx.hstack(
                        rx.button(
                            "Save Settings",
                            on_click=SettingsState.save_settings,
                            size="3",
                        ),
                        rx.button(
                            "Test Connection",
                            on_click=SettingsState.test_connection,
                            size="3",
                            variant="soft",
                        ),
                        spacing="3",
                    ),
                    spacing="4",
                    width="100%",
                ),
                max_width="680px",
                width="100%",
                padding="6",
            ),
            padding="8",
            width="100%",
            display="flex",
            justify_content="center",
        ),
        width="100%",
        min_height="100vh",
        background="var(--gray-1)",
        spacing="0",
    )
