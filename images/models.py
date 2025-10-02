from django.db import models
from django.conf import settings

# Create your models here.
class Image(models.Model):
    file_path = models.CharField(max_length=500)
    file_hash = models.CharField(max_length=64, unique=True, null=True, blank=True, help_text="SHA256 hash of the file for uniqueness")
    original_filename = models.CharField(max_length=255, null=True, blank=True, help_text="Original filename of the uploaded file")
    description = models.TextField(blank=True, null=True, help_text="Description of the image")
    file_size = models.PositiveIntegerField(null=True, blank=True, help_text="File size in bytes")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_images"
    )

    def __str__(self):
        return f"Image {self.id} ({self.original_filename})"