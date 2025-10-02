from django.db import models
from django.conf import settings
from images.models import Image

class Classification(models.Model):
    """Model to store classification results for images"""
    
    # Enum choices for classification (matching API specification)
    CLASSIFICATION_CHOICES = [
        ('stage1', 'Estágio 1'),
        ('stage2', 'Estágio 2'), 
        ('stage3', 'Estágio 3'),
        ('stage4', 'Estágio 4'),
        ('not_classifiable', 'Not Classifiable'),
        ('dtpi', 'DTPI'),
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
    stage = models.CharField(
        max_length=20,
        choices=CLASSIFICATION_CHOICES,
        default='nao_classificavel',  # Default value for migration
        help_text="Classification stage for the image"
    )
    
    # Observations field (renamed from comment to match API spec)
    observations = models.TextField(
        blank=True,
        null=True,
        help_text="Additional observations about the classification"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        # Optional: Add unique constraint if each user can only classify an image once
        # unique_together = ['user', 'image']
    
    def __str__(self):
        return f"Classification by {self.user.name} for Image {self.image.id}: {self.get_stage_display()}"

# Create your models here.
