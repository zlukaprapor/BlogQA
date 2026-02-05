from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse


class BlogHomeTests(TestCase):
    """Тести головної сторінки блогу"""

    def test_blog_home_status_code(self):
        """Головна сторінка блогу доступна"""
        response = self.client.get(reverse('blog-home'))
        self.assertEqual(response.status_code, 200)

    def test_blog_home_uses_correct_template(self):
        """Сторінка використовує правильний шаблон"""
        response = self.client.get(reverse('blog-home'))
        self.assertTemplateUsed(response, 'blog/home.html')


class PostCreateTests(TestCase):
    """Тести створення постів"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_post_create_redirects_if_not_logged_in(self):
        """
        Неавторизований користувач
        отримує redirect (302)
        """
        response = self.client.get(reverse('post-create'))
        self.assertEqual(response.status_code, 302)

    def test_post_create_access_for_logged_in_user(self):
        """
        Авторизований користувач
        має доступ до сторінки
        """
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('post-create'))
        self.assertEqual(response.status_code, 200)
