from django.db import models
from django.conf import settings
from images.models import Image

class Classification(models.Model):
    """Model to store classification results for images"""
    
    # Enum choices for classification
    CLASSIFICATION_CHOICES = [
        ('stage1', 'Stage 1'),
        ('stage2', 'Stage 2'),
        ('stage3', 'Stage 3'),
        ('stage4', 'Stage 4'),
        ('normal', 'Normal'),
        ('notapplicable', 'Not Applicable'),
        ('notunderstand', 'Not Understand'),
    ]
    
    # Foreign key relationships
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='classifications'
    )
    image = models.ForeignKey(
        Image,
        on_delete=models.CASCADE,
        related_name='classifications'
    )
    
    # Classification field with enum choices
    classification = models.CharField(
        max_length=20,
        choices=CLASSIFICATION_CHOICES,
        help_text="Classification result for the image"
    )
    
    # Comment field
    comment = models.TextField(
        blank=True,
        null=True,
        help_text="Additional comments about the classification"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        # Optional: Add unique constraint if each user can only classify an image once
        # unique_together = ['user', 'image']
    
    def __str__(self):
        return f"Classification by {self.user.email} for Image {self.image.id}: {self.get_classification_display()}"

# Create your models here.
