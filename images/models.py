from django.db import models
from django.conf import settings

# Create your models here.
class Image(models.Model):
    file_path = models.CharField(max_length=500)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_images"
    )

    def __str__(self):
        return f"Image {self.id} ({self.file_path})"