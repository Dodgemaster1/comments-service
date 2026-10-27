from django.contrib import admin

from comments.models import CommentModel


# Register your models here.
@admin.register(CommentModel)
class CommentModelAdmin(admin.ModelAdmin):
    """Configure the admin interface for comments."""
