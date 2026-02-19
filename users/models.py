from django.db import models
from django.contrib.auth.models import User
from PIL import Image
import os


class Profile(models.Model):
    """Модель профілю користувача"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Користувач")
    image = models.ImageField(
        default='default.jpg',  # повинен лежати у MEDIA_ROOT
        upload_to='profile_pics',
        verbose_name="Аватар"
    )
    bio = models.TextField(max_length=500, blank=True, verbose_name="Про себе")

    class Meta:
        verbose_name = "Профіль"
        verbose_name_plural = "Профілі"

    def __str__(self):
        return f'Профіль {self.user.username}'

    def save(self, *args, **kwargs):
        """Зменшуємо розмір зображення при збереженні"""
        super().save(*args, **kwargs)

        # Перевірка чи файл існує
        if self.image and os.path.exists(self.image.path):
            img = Image.open(self.image.path)
            if img.height > 300 or img.width > 300:
                img.thumbnail((300, 300))
                img.save(self.image.path)