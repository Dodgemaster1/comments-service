from typing import Literal

import msgspec

MAX_PAGE_SIZE = 100


class FileMetadataSchema(msgspec.Struct):
    """Describe metadata for an uploaded file."""

    content_type: Literal[
        "text/plain",
        "image/jpeg",
        "image/png",
        "image/gif",
    ]
    name: str
    size: int


class UploadFileSchema(msgspec.Struct, kw_only=True):
    """Describe the optional upload in a multipart request."""

    file: FileMetadataSchema | None = None


class CommentCreateSchema(msgspec.Struct, kw_only=True):
    """Validate fields accepted when creating a comment."""

    username: str
    email: str
    text: str
    captcha_key: str
    captcha_value: str
    homepage: str | None = None
    reply_to: int | None = None


class CommentSchema(msgspec.Struct, kw_only=True):
    """Represent a comment and its nested replies."""

    id: int
    username: str
    email: str
    text: str
    homepage: str | None = None
    file_url: str | None = None
    children: list[CommentSchema] = msgspec.field(default_factory=list)


class CommentQuery(msgspec.Struct):
    """Represent pagination and ordering options for comments."""

    page: int = 1
    page_size: int = 25

    ordering: Literal["created_at", "-created_at", "username", "-username", "email", "-email"] = "-created_at"

    def validate(self) -> None:
        """Validate pagination bounds."""
        if self.page < 1:
            raise ValueError("Page must be greater than 0")
        if self.page_size < 1 or self.page_size > MAX_PAGE_SIZE:
            message = f"Page size must be between 1 and {MAX_PAGE_SIZE}"
            raise ValueError(message)


class CaptchaOutputSchema(msgspec.Struct, kw_only=True):
    """Represent the key and image URL for a CAPTCHA challenge."""

    captcha_key: str
    image_url: str
