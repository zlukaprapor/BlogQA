from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Post(models.Model):
    """Модель для постів блогу"""

    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Зміст")
    date_posted = models.DateTimeField(default=timezone.now, verbose_name="Дата публікації")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")

    class Meta:
        ordering = ["-date_posted"]
        verbose_name = "Пост"
        verbose_name_plural = "Пости"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("post-detail", kwargs={"pk": self.pk})


class Comment(models.Model):
    """Модель для коментарів до постів"""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments", verbose_name="Пост")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    content = models.TextField(verbose_name="Текст коментаря")
    date_posted = models.DateTimeField(default=timezone.now, verbose_name="Дата публікації")

    class Meta:
        ordering = ["date_posted"]
        verbose_name = "Коментар"
        verbose_name_plural = "Коментарі"

    def __str__(self):
        return f'Коментар від {self.author.username} до "{self.post.title}"'
