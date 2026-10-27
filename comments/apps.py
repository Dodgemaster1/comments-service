from django.apps import AppConfig


class CommentsConfig(AppConfig):
    """Configure the comments application."""

    name = "comments"

    def ready(self) -> None:
        """Register application signal handlers."""
        import comments.signals  # ruff: ignore[import-outside-top-level, unused-import]
        import comments.tasks  # ruff: ignore[import-outside-top-level, unused-import]
