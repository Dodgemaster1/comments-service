import io
from pathlib import Path
from typing import ClassVar, Final

from django.core.files.base import ContentFile, File
lazy from PIL import Image, ImageOps, ImageSequence, UnidentifiedImageError


class ImageService:
    """Validate, sanitize, and resize uploaded Django images before storage."""

    MAX_SIZE: Final = (320, 240)
    ALLOWED_FORMATS: Final = frozenset({"JPEG", "PNG", "GIF"})
    MAX_PIXELS: Final = 20_000_000  # ~5000x4000
    MAX_GIF_FRAMES: Final = 150
    BACKGROUND_COLOR: Final = (255, 255, 255)

    FORMAT_EXTENSIONS: ClassVar[dict[str, str]] = {
        "JPEG": ".jpg",
        "PNG": ".png",
        "GIF": ".gif",
    }

    @classmethod
    def process(cls, django_file: File | None) -> ContentFile | None:
        """Return a processed ContentFile that matches the service constraints."""
        if not django_file or not django_file.size:
            return None

        django_file.seek(0)

        try:
            with Image.open(django_file) as image:
                if not image.format:
                    raise ValueError("Cannot determine image format.")

                image_format = image.format.upper()
                if image_format not in cls.ALLOWED_FORMATS:
                    allowed = ", ".join(sorted(cls.ALLOWED_FORMATS))
                    raise ValueError(f"Unsupported image format: {image_format}. Allowed: {allowed}")

                if image.width * image.height > cls.MAX_PIXELS:
                    raise ValueError(
                        f"Image resolution ({image.width}x{image.height}) "
                        + f"exceeds maximum limit of {cls.MAX_PIXELS} pixels."
                    )

                buffer = io.BytesIO()

                if image_format == "GIF" and getattr(image, "is_animated", False):
                    cls._process_animated_gif(image, buffer)
                else:
                    cls._process_static_image(image, image_format, buffer)

        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            raise ValueError("Invalid, corrupted, or dangerously large image file.") from exc
        finally:
            django_file.seek(0)

        safe_name = cls._get_safe_filename(django_file.name, image_format)
        return ContentFile(buffer.getvalue(), name=safe_name)

    @classmethod
    def _process_static_image(cls, image: Image.Image, image_format: str, buffer: io.BytesIO) -> None:
        image = ImageOps.exif_transpose(image)

        if image_format == "JPEG":
            image = cls._to_rgb_with_background(image)

        image.thumbnail(cls.MAX_SIZE, Image.Resampling.LANCZOS)

        save_kwargs: dict[str, object] = {"format": image_format, "optimize": True}
        if image_format == "JPEG":
            save_kwargs["quality"] = 85

        extra_params: dict[str, object] = {"optimize": True}
        if image_format == "JPEG":
            extra_params["quality"] = 85

        image.save(buffer, format=image_format, **extra_params)

    @classmethod
    def _process_animated_gif(cls, image: Image.Image, buffer: io.BytesIO) -> None:
        n_frames = getattr(image, "n_frames", 1)
        if n_frames > cls.MAX_GIF_FRAMES:
            raise ValueError(f"GIF has too many frames ({n_frames}). Maximum allowed is {cls.MAX_GIF_FRAMES}.")

        frames: list[Image.Image] = []
        durations: list[int] = []

        for frame in ImageSequence.Iterator(image):
            durations.append(frame.info.get("duration", 100))
            frame_copy = frame.convert("RGBA")
            frame_copy.thumbnail(cls.MAX_SIZE, Image.Resampling.LANCZOS)
            frames.append(frame_copy)

        frames[0].save(
            buffer,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            optimize=True,
            loop=image.info.get("loop", 0),
            duration=durations,
            disposal=2,
        )

    @classmethod
    def _to_rgb_with_background(cls, image: Image.Image) -> Image.Image:
        if image.mode == "RGB":
            return image

        if image.mode in {"RGBA", "LA"} or (image.mode == "P" and "transparency" in image.info):
            rgba_image = image.convert("RGBA")
            background = Image.new("RGB", rgba_image.size, cls.BACKGROUND_COLOR)
            background.paste(rgba_image, mask=rgba_image.split()[3])
            return background

        return image.convert("RGB")

    @classmethod
    def _get_safe_filename(cls, original_name: str | None, image_format: str) -> str:
        stem = Path(original_name).stem if original_name else "upload"
        ext = cls.FORMAT_EXTENSIONS.get(image_format, ".png")
        return f"{stem or 'upload'}{ext}"
