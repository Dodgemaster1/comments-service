from celery import shared_task
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from comments.models import FileModel
from comments.services.image import ImageService


@shared_task(
    autoretry_for=(OSError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def process_image(file_id: int) -> None:
    """Validate, resize, and replace an uploaded image in the background."""
    try:
        file_model = FileModel.objects.get(pk=file_id)
    except FileModel.DoesNotExist:
        return

    original_name = file_model.file.name
    try:
        processed_file = _process_file(file_model)
    except (OSError, ValueError) as exc:
        file_model.processing_status = "failed"
        file_model.processing_error = str(exc)
        file_model.save(update_fields=("processing_status", "processing_error"))
        raise

    file_model.file.save(processed_file.name, processed_file, save=False)
    file_model.processing_status = "processed"
    file_model.processing_error = ""
    file_model.save(update_fields=("file", "processing_status", "processing_error"))
    if original_name != file_model.file.name:
        default_storage.delete(original_name)


def _process_file(file_model: FileModel) -> ContentFile:
    processed_file = ImageService.process(file_model.file)
    if processed_file is None:
        raise ValueError("Uploaded image is empty.")
    return processed_file
