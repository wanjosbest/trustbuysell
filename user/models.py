from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    shopowner = models.BooleanField(default=False, null=True)
    phone_number = models.CharField(max_length=15, null=True)

    def __str__(self):
        return self.username