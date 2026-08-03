from django.db import models
from django.contrib.auth.models import AbstractUser

from .managers import CustomUserManager


class User(AbstractUser):

    username = models.CharField(
        max_length=100,
        unique=True
    )

    email = models.EmailField(
        unique=True
    )

    first_name = models.CharField(
        max_length=100
    )

    last_name = models.CharField(
        max_length=100
    )

    profile_picture = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email