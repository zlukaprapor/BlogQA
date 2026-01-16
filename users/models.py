from django.db import models
from django.contrib.auth.models import User
from PIL import Image


class Profile(models.Model):
    """Модель профілю користувача"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Користувач")
    image = models.ImageField(default='default.jpg', upload_to='profile_pics', verbose_name="Аватар")
    bio = models.TextField(max_length=500, blank=True, verbose_name="Про себе")

    class Meta:
        verbose_name = "Профіль"
        verbose_name_plural = "Профілі"

    def __str__(self):
        return f'Профіль {self.user.username}'

    def save(self, *args, **kwargs):
        """Зменшуємо розмір зображення при збереженні"""
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)