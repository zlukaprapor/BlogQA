from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Форма створення/редагування поста"""

    class Meta:
        model = Post
        fields = ["title", "content"]
        labels = {
            "title": "Заголовок",
            "content": "Зміст",
        }
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Введіть заголовок"}),
            "content": forms.Textarea(
                attrs={"class": "form-control", "rows": 10, "placeholder": "Напишіть ваш пост..."}
            ),
        }


class CommentForm(forms.ModelForm):
    """Форма створення коментаря"""

    class Meta:
        model = Comment
        fields = ["content"]
        labels = {
            "content": "",
        }
        widgets = {
            "content": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Напишіть коментар..."}
            ),
        }
