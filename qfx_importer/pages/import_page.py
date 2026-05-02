"""Import page – upload and import QFX/OFX files."""
import reflex as rx

from qfx_importer.components.navbar import navbar
from qfx_importer.state import ImportState


def import_page() -> rx.Component:
    return rx.vstack(
        navbar(),
        rx.box(
            rx.card(
                rx.vstack(
                    rx.heading("Import QFX / OFX Files", size="5"),
                    rx.text(
                        "Upload one or more .qfx / .ofx files. "
                        "Transactions will be imported into your Actual Budget.",
                        size="2",
                        color_scheme="gray",
                    ),
                    rx.divider(),
                    # Upload drop zone
                    rx.upload(
                        rx.vstack(
                            rx.icon("upload_cloud", size=40, color="var(--gray-8)"),
                            rx.text(
                                "Drag & drop .qfx / .ofx files here",
                                size="3",
                                color_scheme="gray",
                            ),
                            rx.button(
                                "Browse Files",
                                variant="soft",
                                size="2",
                            ),
                            spacing="3",
                            align="center",
                            padding="8",
                        ),
                        id="qfx_upload",
                        accept={
                            "application/x-ofx": [".qfx", ".ofx"],
                            "application/octet-stream": [".qfx", ".ofx"],
                        },
                        multiple=True,
                        border="2px dashed var(--gray-5)",
                        border_radius="var(--radius-3)",
                        width="100%",
                        _hover={"border_color": "var(--accent-9)"},
                    ),
                    # Selected file list
                    rx.foreach(
                        rx.selected_files("qfx_upload"),
                        lambda f: rx.badge(f, variant="soft", size="2"),
                    ),
                    # Import button
                    rx.button(
                        rx.cond(
                            ImportState.is_importing,
                            rx.hstack(
                                rx.spinner(size="2"),
                                rx.text("Importing…"),
                                spacing="2",
                            ),
                            rx.text("Import Files"),
                        ),
                        on_click=ImportState.handle_upload(
                            rx.upload_files(upload_id="qfx_upload")
                        ),
                        disabled=ImportState.is_importing,
                        size="3",
                        width="100%",
                    ),
                    # Results
                    rx.cond(
                        ImportState.import_results.length() > 0,  # type: ignore[attr-defined]
                        rx.vstack(
                            rx.text(
                                "Import Results", size="3", weight="bold"
                            ),
                            rx.foreach(
                                ImportState.import_results,
                                lambda msg: rx.callout(
                                    msg,
                                    icon="circle_check",
                                    color_scheme="green",
                                    width="100%",
                                ),
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        ImportState.import_errors.length() > 0,  # type: ignore[attr-defined]
                        rx.vstack(
                            rx.text("Errors", size="3", weight="bold"),
                            rx.foreach(
                                ImportState.import_errors,
                                lambda err: rx.callout(
                                    err,
                                    icon="triangle_alert",
                                    color_scheme="red",
                                    width="100%",
                                ),
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        rx.fragment(),
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
