"""Setup page – first-time configuration."""
import reflex as rx

from qfx_importer.state import SetupState


def setup_page() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("First-Time Setup", size="6", margin_bottom="2"),
                rx.text(
                    "Enter the setup token printed in the server logs, then choose a password.",
                    size="2",
                    color_scheme="gray",
                ),
                rx.divider(),
                rx.vstack(
                    rx.text("Setup Token", size="2", weight="medium"),
                    rx.input(
                        placeholder="Paste setup token from logs",
                        value=SetupState.setup_token_input,
                        on_change=SetupState.set_setup_token_input,
                        width="100%",
                    ),
                    rx.text("New Password", size="2", weight="medium"),
                    rx.input(
                        placeholder="At least 12 characters",
                        type="password",
                        value=SetupState.new_password,
                        on_change=SetupState.set_new_password,
                        width="100%",
                    ),
                    rx.text("Confirm Password", size="2", weight="medium"),
                    rx.input(
                        placeholder="Repeat password",
                        type="password",
                        value=SetupState.confirm_password,
                        on_change=SetupState.set_confirm_password,
                        width="100%",
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.cond(
                    SetupState.error != "",
                    rx.callout(
                        SetupState.error,
                        icon="triangle_alert",
                        color_scheme="red",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    SetupState.success != "",
                    rx.callout(
                        SetupState.success,
                        icon="circle_check",
                        color_scheme="green",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.button(
                    "Complete Setup",
                    on_click=SetupState.handle_setup,
                    width="100%",
                    size="3",
                ),
                spacing="4",
                width="100%",
            ),
            width="420px",
            padding="6",
        ),
        min_height="100vh",
        background="var(--gray-2)",
    )
