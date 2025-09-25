from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    password = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return self.google_id

