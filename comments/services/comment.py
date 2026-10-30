from http import HTTPStatus

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import UploadedFile
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from dmr import APIError
from dmr.pagination import Page, Paginated

from comments.models import CommentModel, FileModel, UserModel
from comments.schemas import CommentCreateSchema, CommentQuery, CommentSchema, FileMetadataSchema, UploadFileSchema
from comments.serializers import build_comment_tree
from comments.tasks import process_image

from .captcha import CaptchaService


class FileUploadService:
    """Validate and persist optional uploaded files for comments."""

    def __init__(self, file: UploadedFile, file_metadata: FileMetadataSchema) -> None:
        self.file = file
        self.file_metadata = file_metadata

    def validate(self) -> None:
        """Validate non-image metadata and enforce upload constraints."""
        if self.file_metadata is None:
            return

        if self.file_metadata.content_type == "text/plain":
            if not self.file_metadata.name.lower().endswith(".txt"):
                raise APIError(
                    "A file with the “text/plain” MIME type must have a .txt extension",
                    status_code=HTTPStatus.BAD_REQUEST,
                )
            if self.file_metadata.size > 100 * 1024:
                raise APIError(
                    "A text file must not exceed 100 KB",
                    status_code=HTTPStatus.BAD_REQUEST,
                )

    def save(self, comment: CommentModel) -> FileModel:
        """Persist an image and enqueue its processing after the transaction commits."""
        file_model = FileModel.objects.create(file=self.file, comment=comment)
        transaction.on_commit(lambda: process_image.delay(file_model.pk))
        return file_model


class CommentService:
    """Encapsulate the comment creation workflow used by the controller."""

    @staticmethod
    def list_comments(parsed_query: CommentQuery) -> Paginated[CommentSchema]:
        """Return a cached page of comments with nested replies."""
        cache_key = f"comments:list:{parsed_query.page}:{parsed_query.page_size}:{parsed_query.ordering}"
        cached_comments = cache.get(cache_key)
        if cached_comments is not None:
            return cached_comments

        ordering = {
            "username": "user__username",
            "-username": "-user__username",
            "email": "user__email",
            "-email": "-user__email",
        }.get(parsed_query.ordering, parsed_query.ordering)
        roots_qs = CommentModel.objects.filter(depth=1).order_by(ordering, "-id")
        paginator = Paginator(roots_qs, parsed_query.page_size)
        page = paginator.get_page(parsed_query.page)

        result = Paginated(
            count=paginator.count,
            num_pages=paginator.num_pages,
            per_page=paginator.per_page,
            page=Page(
                number=page.number,
                object_list=build_comment_tree(list(page.object_list)),
            ),
        )
        cache.set(cache_key, result, timeout=settings.COMMENTS_CACHE_TIMEOUT)
        return result

    @staticmethod
    def create_comment(
        parsed_body: CommentCreateSchema,
        parsed_file_metadata: UploadFileSchema,
        request_files: dict[str, UploadedFile],
    ) -> tuple[CommentModel, UserModel]:
        """Create a user/comment pair and attach an optional uploaded file."""
        with transaction.atomic():
            CaptchaService.validate(parsed_body)

            user, _ = UserModel.objects.get_or_create(
                email=parsed_body.email,
                defaults={"username": parsed_body.username},
            )

            fields = {
                "user": user,
                "text": parsed_body.text,
                "homepage": parsed_body.homepage,
                "created_at": timezone.now(),
            }

            if parsed_body.reply_to is not None:
                parent = get_object_or_404(CommentModel, pk=parsed_body.reply_to)
                comment = parent.add_child(**fields)
            else:
                comment = CommentModel.add_root(**fields)

            if parsed_file_metadata.file is not None:
                file_upload_service = FileUploadService(request_files["file"], parsed_file_metadata.file)
                file_upload_service.validate()
                file_upload_service.save(comment)

        return comment, user
