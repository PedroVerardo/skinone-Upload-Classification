from django.db import models
from django.conf import settings
from images.models import Image

class Classification(models.Model):
    """Model to store classification results for images"""
    
    CLASSIFICATION_CHOICES = [
        ('stage1', 'Estágio 1'),
        ('stage2', 'Estágio 2'), 
        ('stage3', 'Estágio 3'),
        ('stage4', 'Estágio 4'),
        ('not_classifiable', 'Not Classifiable'),
        ('dtpi', 'DTPI'),
    ]
    
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
    
    stage = models.CharField(
        max_length=20,
        choices=CLASSIFICATION_CHOICES,
        default='not_classifiable',
    )
    
    observations = models.TextField(
        blank=True,
        null=True,
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        # Optional: Add unique constraint if each user can only classify an image once
        # unique_together = ['user', 'image']
    
    def __str__(self):
        return f"Classification by {self.user.name} for Image {self.image.id}: {self.get_stage_display()}"

# Create your models here.
