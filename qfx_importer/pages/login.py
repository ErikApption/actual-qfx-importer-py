"""Login page."""
import reflex as rx

from qfx_importer.state import LoginState


def login_page() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("Sign In", size="6", margin_bottom="2"),
                rx.text(
                    "Enter your password to access QFX Importer.",
                    size="2",
                    color_scheme="gray",
                ),
                rx.divider(),
                rx.vstack(
                    rx.text("Password", size="2", weight="medium"),
                    rx.input(
                        placeholder="Password",
                        type="password",
                        value=LoginState.password_input,
                        on_change=LoginState.set_password_input,
                        on_key_down=rx.cond(
                            rx.Var.create("event.key") == "Enter",
                            LoginState.handle_login,
                            rx.noop(),
                        ),
                        width="100%",
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.cond(
                    LoginState.error != "",
                    rx.callout(
                        LoginState.error,
                        icon="triangle_alert",
                        color_scheme="red",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.button(
                    "Sign In",
                    on_click=LoginState.handle_login,
                    width="100%",
                    size="3",
                ),
                spacing="4",
                width="100%",
            ),
            width="380px",
            padding="6",
        ),
        min_height="100vh",
        background="var(--gray-2)",
    )
