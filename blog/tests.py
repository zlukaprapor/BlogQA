from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Post


class BlogHomeTests(TestCase):
    """Тести для головної сторінки блогу"""
    
    def setUp(self):
        """Підготовка даних для тестів"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
    
    def test_home_page_status_code(self):
        """Тест що головна сторінка доступна"""
        response = self.client.get(reverse('blog-home'))
        self.assertEqual(response.status_code, 200)
    
    def test_home_page_uses_correct_template(self):
        """Тест що використовується правильний шаблон"""
        response = self.client.get(reverse('blog-home'))
        self.assertTemplateUsed(response, 'blog/home.html')


class PostCreateTests(TestCase):
    """Тести для створення постів"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
    
    def test_post_create_requires_login(self):
        """Тест що створення посту вимагає авторизації"""
        response = self.client.get(reverse('post-create'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
    
    def test_post_create_logged_in(self):
        """Тест доступу до створення посту після логіну"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('post-create'))
        self.assertEqual(response.status_code, 200)
