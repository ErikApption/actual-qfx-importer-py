"""API Key management page."""
import reflex as rx

from qfx_importer.components.navbar import navbar
from qfx_importer.state import ApiKeyState


def api_key_page() -> rx.Component:
    return rx.vstack(
        navbar(),
        rx.box(
            rx.vstack(
                # ── API Key card ────────────────────────────────────────────
                rx.card(
                    rx.vstack(
                        rx.heading("API Key", size="5"),
                        rx.text(
                            "Use this key to authenticate external requests.",
                            size="2",
                            color_scheme="gray",
                        ),
                        rx.divider(),
                        rx.hstack(
                            rx.code(
                                ApiKeyState.masked_key,
                                size="3",
                                variant="soft",
                            ),
                            rx.spacer(),
                            rx.button(
                                "Regenerate",
                                on_click=ApiKeyState.regenerate_key,
                                size="2",
                                color_scheme="amber",
                                variant="soft",
                            ),
                            width="100%",
                            align="center",
                        ),
                        rx.cond(
                            ApiKeyState.new_key_plain != "",
                            rx.vstack(
                                rx.callout(
                                    rx.vstack(
                                        rx.text(
                                            "New API key – copy it now, it will not be shown again:",
                                            weight="medium",
                                            size="2",
                                        ),
                                        rx.code(
                                            ApiKeyState.new_key_plain,
                                            size="2",
                                        ),
                                        rx.button(
                                            "Dismiss",
                                            on_click=ApiKeyState.dismiss_new_key,
                                            size="1",
                                            variant="ghost",
                                        ),
                                        spacing="2",
                                    ),
                                    icon="key",
                                    color_scheme="blue",
                                    width="100%",
                                ),
                                width="100%",
                            ),
                            rx.fragment(),
                        ),
                        rx.cond(
                            ApiKeyState.regen_msg != "",
                            rx.callout(
                                ApiKeyState.regen_msg,
                                icon=rx.cond(
                                    ApiKeyState.regen_ok,
                                    "circle_check",
                                    "triangle_alert",
                                ),
                                color_scheme=rx.cond(
                                    ApiKeyState.regen_ok, "green", "red"
                                ),
                                width="100%",
                            ),
                            rx.fragment(),
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    max_width="560px",
                    width="100%",
                    padding="6",
                ),
                # ── Change Password card ─────────────────────────────────────
                rx.card(
                    rx.vstack(
                        rx.heading("Change App Password", size="5"),
                        rx.divider(),
                        rx.vstack(
                            rx.text("New Password", size="2", weight="medium"),
                            rx.input(
                                placeholder="At least 12 characters",
                                type="password",
                                value=ApiKeyState.new_password,
                                on_change=ApiKeyState.set_new_password,
                                width="100%",
                            ),
                            rx.text(
                                "Confirm New Password", size="2", weight="medium"
                            ),
                            rx.input(
                                placeholder="Repeat new password",
                                type="password",
                                value=ApiKeyState.confirm_password,
                                on_change=ApiKeyState.set_confirm_password,
                                width="100%",
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        rx.cond(
                            ApiKeyState.pw_msg != "",
                            rx.callout(
                                ApiKeyState.pw_msg,
                                icon=rx.cond(
                                    ApiKeyState.pw_ok,
                                    "circle_check",
                                    "triangle_alert",
                                ),
                                color_scheme=rx.cond(
                                    ApiKeyState.pw_ok, "green", "red"
                                ),
                                width="100%",
                            ),
                            rx.fragment(),
                        ),
                        rx.button(
                            "Update Password",
                            on_click=ApiKeyState.change_password,
                            size="3",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    max_width="560px",
                    width="100%",
                    padding="6",
                ),
                spacing="6",
                align="center",
                padding_top="8",
                width="100%",
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
