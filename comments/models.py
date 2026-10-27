from django.core.validators import FileExtensionValidator
from django.db import models
from treebeard.mp_tree import MP_Node


class UserModel(models.Model):
    """Store the identity associated with submitted comments."""

    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Configure the database table for users."""

        db_table = "users"

    def __str__(self) -> str:
        """Return the user's display name."""
        return self.username


class CommentModel(MP_Node):
    """Store a comment in the materialized-path reply tree."""

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(UserModel, on_delete=models.RESTRICT, related_name="comments")

    homepage = models.URLField(blank=True, null=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    node_order_by: list[str] = ["created_at"]  # ruff: ignore[mutable-class-default]

    class Meta:
        """Configure the database table for comments."""

        db_table = "comments"

    def __str__(self) -> str:
        """Return a short representation of the comment."""
        return f"{self.user.username}: {self.text[:30]}"


class FileModel(models.Model):
    """Store an image uploaded with a comment."""

    id = models.BigAutoField(primary_key=True)
    file = models.ImageField(
        upload_to="uploads/",
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "gif"])],
    )
    comment = models.ForeignKey(CommentModel, on_delete=models.RESTRICT, related_name="files")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processing_status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("processed", "Processed"), ("failed", "Failed")],
        default="pending",
    )
    processing_error = models.TextField(blank=True)

    class Meta:
        """Configure the database table for uploaded files."""

        db_table = "files"

    def __str__(self) -> str:
        """Return a description of the uploaded file."""
        return f"File {self.id} uploaded at {self.uploaded_at}"
