from captcha.models import CaptchaStore
from django.utils import timezone

from comments.schemas import CommentCreateSchema


class CaptchaService:
    """Validate CAPTCHA tokens and invalidate them after successful use."""

    @staticmethod
    def generate() -> str:
        """Create and persist a fresh CAPTCHA challenge."""
        return CaptchaStore.generate_key()

    @staticmethod
    def validate(parsed_body: CommentCreateSchema) -> None:
        """Check the submitted CAPTCHA against the persisted challenge."""
        captcha = CaptchaStore.objects.get(
            hashkey=parsed_body.captcha_key,
            response=parsed_body.captcha_value.lower(),
            expiration__gt=timezone.now(),
        )
        captcha.delete()
