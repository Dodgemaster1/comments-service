from http import HTTPStatus

from asgiref.sync import sync_to_async
from captcha.helpers import captcha_image_url
from captcha.models import CaptchaStore
from dmr import APIError, Body, Controller, FileMetadata, Query
from dmr.pagination import Paginated
from dmr.parsers import MultiPartParser
from dmr.plugins.msgspec import MsgspecSerializer

from comments.schemas import CaptchaOutputSchema, CommentCreateSchema, CommentQuery, CommentSchema, UploadFileSchema
from comments.services.captcha import CaptchaService
from comments.services.comment import CommentService
from comments.services.text import TextService


class CommentController(Controller[MsgspecSerializer]):
    """Expose endpoints for listing and creating comments."""

    parsers = (MultiPartParser(),)

    async def get(self, parsed_query: Query[CommentQuery]) -> Paginated[CommentSchema]:
        """Return a paginated comment tree."""
        return await sync_to_async(CommentService.list_comments)(parsed_query)

    async def post(
        self,
        parsed_body: Body[CommentCreateSchema],
        parsed_file_metadata: FileMetadata[UploadFileSchema],
    ) -> CommentSchema:
        """Validate and create a comment with an optional attachment."""
        try:
            comment, user = await sync_to_async(CommentService.create_comment)(
                parsed_body,
                parsed_file_metadata,
                self.request.FILES,
            )
        except CaptchaStore.DoesNotExist as e:
            raise APIError(self.format_error("Wrong captcha"), status_code=HTTPStatus.BAD_REQUEST) from e

        return CommentSchema(
            id=comment.id,
            username=user.username,
            email=user.email,
            text=TextService.sanitize(comment.text),
            homepage=comment.homepage,
        )


class CaptchaController(Controller[MsgspecSerializer]):
    """Expose the CAPTCHA challenge endpoint."""

    async def get(self) -> CaptchaOutputSchema:
        """Return a fresh CAPTCHA challenge."""
        new_key = await sync_to_async(CaptchaService.generate)()
        image_url = captcha_image_url(new_key)
        return CaptchaOutputSchema(
            captcha_key=new_key,
            image_url=image_url,
        )
