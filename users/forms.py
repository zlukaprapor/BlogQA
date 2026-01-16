from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile


class UserRegisterForm(UserCreationForm):
    """Форма реєстрації користувача"""
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        labels = {
            'username': 'Логін',
            'email': 'Email',
        }
        help_texts = {
            'username': 'Обов\'язкове поле. 150 символів або менше. Тільки літери, цифри та символи @/./+/-/_.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Підтвердження паролю'
        self.fields['password1'].help_text = 'Мінімум 8 символів'
        self.fields['password2'].help_text = 'Введіть той самий пароль для підтвердження'


class UserUpdateForm(forms.ModelForm):
    """Форма оновлення даних користувача"""
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']
        labels = {
            'username': 'Логін',
            'email': 'Email',
        }


class ProfileUpdateForm(forms.ModelForm):
    """Форма оновлення профілю"""

    class Meta:
        model = Profile
        fields = ['image', 'bio']
        labels = {
            'image': 'Аватар',
            'bio': 'Про себе',
        }
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }