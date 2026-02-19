"""
users/tests.py — UNIT-тести для додатку users
Покриває: Profile model, signals, UserRegisterForm,
          UserUpdateForm, ProfileUpdateForm, register view, profile view
Використовує: django.test.TestCase, unittest.mock (Mock/Spy/patch)
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock, call

from users.models import Profile
from users.forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm


# ══════════════════════════════════════════════════════
#  1. MODEL — Profile  (повне покриття 100%)
# ══════════════════════════════════════════════════════

class ProfileModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass1234')

    # сигнал автоматично створює Profile
    def test_profile_auto_created(self):
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, Profile)

    # OneToOne зв'язок
    def test_profile_linked_to_user(self):
        self.assertEqual(self.user.profile.user, self.user)

    # __str__
    def test_str_format(self):
        self.assertEqual(str(self.user.profile), f'Профіль {self.user.username}')

    # default image
    def test_default_image_name(self):
        self.assertEqual(self.user.profile.image.name, 'default.jpg')

    # bio за замовчуванням порожній
    def test_bio_default_empty(self):
        self.assertEqual(self.user.profile.bio, '')

    # bio можна заповнити
    def test_bio_can_be_set(self):
        self.user.profile.bio = 'Трохи про мене'
        self.user.profile.save()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, 'Трохи про мене')

    # один Profile на одного User
    def test_one_profile_per_user(self):
        count = Profile.objects.filter(user=self.user).count()
        self.assertEqual(count, 1)

    # CASCADE: видалення User → видалення Profile
    def test_profile_deleted_with_user(self):
        user_id = self.user.pk
        self.user.delete()
        self.assertEqual(Profile.objects.filter(user_id=user_id).count(), 0)

    # bio max_length = 500
    def test_bio_max_length(self):
        max_length = Profile._meta.get_field('bio').max_length
        self.assertEqual(max_length, 500)


# ══════════════════════════════════════════════════════
#  2. SIGNALS  — ізольоване тестування через Mock
# ══════════════════════════════════════════════════════

class ProfileSignalTest(TestCase):

    # Інтеграційний: реальний сигнал → реальний Profile
    def test_signal_creates_profile_on_new_user(self):
        user = User.objects.create_user(username='newone', password='pass')
        self.assertTrue(Profile.objects.filter(user=user).exists())

    # Сигнал не дублює Profile при повторному збереженні user
    def test_signal_no_duplicate_on_user_save(self):
        self.user = User.objects.create_user(username='saveagain', password='pass')
        self.user.first_name = 'Іван'
        self.user.save()  # повторне збереження
        count = Profile.objects.filter(user=self.user).count()
        self.assertEqual(count, 1)

    # ── MOCK: ізольований тест функції сигналу ──
    @patch('users.signals.Profile')
    def test_signal_handler_calls_create_when_created(self, MockProfile):
        """Mock Profile.objects — без звернення до БД."""
        from users.signals import create_or_update_profile
        mock_user = MagicMock(spec=User)

        create_or_update_profile(sender=User, instance=mock_user, created=True)

        MockProfile.objects.create.assert_called_once_with(user=mock_user)

    @patch('users.signals.Profile')
    def test_signal_handler_calls_get_or_create_when_not_created(self, MockProfile):
        """Mock: при оновленні існуючого user — get_or_create."""
        from users.signals import create_or_update_profile
        mock_user = MagicMock(spec=User)

        create_or_update_profile(sender=User, instance=mock_user, created=False)

        MockProfile.objects.get_or_create.assert_called_once_with(user=mock_user)
        MockProfile.objects.create.assert_not_called()


# ══════════════════════════════════════════════════════
#  3. FORMS  — повне покриття (100%)
# ══════════════════════════════════════════════════════

class UserRegisterFormTest(TestCase):

    def _data(self, **kwargs):
        base = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'Str0ng!Pass',
            'password2': 'Str0ng!Pass',
        }
        base.update(kwargs)
        return base

    def test_valid_form(self):
        form = UserRegisterForm(data=self._data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_email_invalid(self):
        form = UserRegisterForm(data=self._data(email=''))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_password_mismatch(self):
        form = UserRegisterForm(data=self._data(password2='WrongPass!'))
        self.assertFalse(form.is_valid())

    def test_duplicate_username(self):
        User.objects.create_user(username='newuser', password='x')
        form = UserRegisterForm(data=self._data())
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_invalid_email_format(self):
        form = UserRegisterForm(data=self._data(email='not-an-email'))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_email_field_required(self):
        form = UserRegisterForm()
        self.assertTrue(form.fields['email'].required)

    def test_fields_list(self):
        form = UserRegisterForm()
        for field in ['username', 'email', 'password1', 'password2']:
            self.assertIn(field, form.fields)

    def test_password_labels_ukrainian(self):
        form = UserRegisterForm()
        self.assertEqual(form.fields['password1'].label, 'Пароль')
        self.assertEqual(form.fields['password2'].label, 'Підтвердження паролю')


class UserUpdateFormTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='updateme', email='old@ex.com', password='pass'
        )

    def test_valid_update(self):
        form = UserUpdateForm(
            data={'username': 'updateme', 'email': 'new@ex.com'},
            instance=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_empty_username_invalid(self):
        form = UserUpdateForm(
            data={'username': '', 'email': 'new@ex.com'},
            instance=self.user,
        )
        self.assertFalse(form.is_valid())

    def test_invalid_email_invalid(self):
        form = UserUpdateForm(
            data={'username': 'updateme', 'email': 'bad-email'},
            instance=self.user,
        )
        self.assertFalse(form.is_valid())

    def test_fields_present(self):
        form = UserUpdateForm()
        self.assertIn('username', form.fields)
        self.assertIn('email', form.fields)


class ProfileUpdateFormTest(TestCase):

    def test_fields_present(self):
        form = ProfileUpdateForm()
        self.assertIn('image', form.fields)
        self.assertIn('bio', form.fields)

    def test_bio_widget_is_textarea(self):
        from django import forms as django_forms
        form = ProfileUpdateForm()
        self.assertIsInstance(form.fields['bio'].widget, django_forms.Textarea)

    def test_valid_form_with_bio(self):
        user = User.objects.create_user(username='proftest', password='pass')
        profile = user.profile
        form = ProfileUpdateForm(
            data={'bio': 'Розробник Django', 'image': ''},
            instance=profile,
        )
        # image не обов'язкове — форма валідна з лише bio
        self.assertTrue(form.is_valid(), form.errors)


# ══════════════════════════════════════════════════════
#  4. VIEWS  — бізнес-логіка (~50%+ покриття)
# ══════════════════════════════════════════════════════

class RegisterViewTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_get_status_200(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_get_template(self):
        response = self.client.get(reverse('register'))
        self.assertTemplateUsed(response, 'users/register.html')

    def test_get_context_has_form(self):
        response = self.client.get(reverse('register'))
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], UserRegisterForm)

    def test_valid_post_creates_user(self):
        self.client.post(reverse('register'), {
            'username': 'brand_new',
            'email': 'brand@new.com',
            'password1': 'Str0ng!Pass',
            'password2': 'Str0ng!Pass',
        })
        self.assertTrue(User.objects.filter(username='brand_new').exists())

    def test_valid_post_redirects_to_login(self):
        response = self.client.post(reverse('register'), {
            'username': 'brand_new',
            'email': 'brand@new.com',
            'password1': 'Str0ng!Pass',
            'password2': 'Str0ng!Pass',
        })
        self.assertRedirects(response, reverse('login'))

    def test_invalid_post_does_not_create_user(self):
        self.client.post(reverse('register'), {
            'username': '',
            'email': 'bad',
            'password1': '123',
            'password2': '456',
        })
        self.assertEqual(User.objects.count(), 0)

    def test_invalid_post_stays_on_register(self):
        response = self.client.post(reverse('register'), {})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    # ── MOCK: перевіряємо що messages.success викликається ──
    @patch('users.views.messages')
    def test_success_message_sent_on_register(self, mock_messages):
        """Spy — перевіряємо виклик messages.success."""
        self.client.post(reverse('register'), {
            'username': 'msguser',
            'email': 'msg@test.com',
            'password1': 'Str0ng!Pass',
            'password2': 'Str0ng!Pass',
        })
        mock_messages.success.assert_called_once()

    # ── MOCK: ізолюємо форму повністю ──
    @patch('users.views.UserRegisterForm')
    def test_register_uses_user_register_form(self, MockForm):
        """Mock форми — перевіряємо що view використовує UserRegisterForm."""
        mock_form = MagicMock()
        mock_form.is_valid.return_value = False
        MockForm.return_value = mock_form

        self.client.post(reverse('register'), {})
        self.assertTrue(MockForm.called)


class ProfileViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='profuser', email='prof@ex.com', password='pass'
        )

    def test_get_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_get_authenticated_200(self):
        self.client.login(username='profuser', password='pass')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_get_template(self):
        self.client.login(username='profuser', password='pass')
        response = self.client.get(reverse('profile'))
        self.assertTemplateUsed(response, 'users/profile.html')

    def test_get_context_has_forms(self):
        self.client.login(username='profuser', password='pass')
        response = self.client.get(reverse('profile'))
        self.assertIn('u_form', response.context)
        self.assertIn('p_form', response.context)

    def test_post_updates_email(self):
        self.client.login(username='profuser', password='pass')
        self.client.post(reverse('profile'), {
            'username': 'profuser',
            'email': 'updated@ex.com',
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updated@ex.com')

    def test_valid_post_redirects_to_profile(self):
        self.client.login(username='profuser', password='pass')
        response = self.client.post(reverse('profile'), {
            'username': 'profuser',
            'email': 'ok@ex.com',
        })
        self.assertRedirects(response, reverse('profile'))

    def test_invalid_post_stays_on_profile(self):
        self.client.login(username='profuser', password='pass')
        response = self.client.post(reverse('profile'), {
            'username': '',
            'email': 'bad-email',
        })
        self.assertEqual(response.status_code, 200)

    # ── SPY: перевіряємо виклик messages.success ──
    @patch('users.views.messages')
    def test_success_message_on_profile_update(self, mock_messages):
        """Spy — перевіряємо messages.success при успішному оновленні."""
        self.client.login(username='profuser', password='pass')
        self.client.post(reverse('profile'), {
            'username': 'profuser',
            'email': 'spy@test.com',
        })
        mock_messages.success.assert_called_once()