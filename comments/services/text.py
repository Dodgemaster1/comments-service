from typing import Final

import nh3


class TextService:
    """Sanitize user-provided HTML while preserving a small safe subset."""

    ALLOWED_TAGS: Final = frozenset({"a", "code", "i", "strong"})
    ALLOWED_ATTRIBUTES: Final = {
        "a": {"href", "title"},
    }
    ALLOWED_SCHEMES: Final = frozenset({"http", "https", "mailto"})

    @staticmethod
    def sanitize(text: str) -> str:
        """Return sanitized text suitable for rendering."""
        return nh3.clean(
            text,
            tags=TextService.ALLOWED_TAGS,
            attributes=TextService.ALLOWED_ATTRIBUTES,
            url_schemes=TextService.ALLOWED_SCHEMES,
            link_rel="noopener noreferrer",
        )
