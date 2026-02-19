"""
blog/tests.py  — UNIT-тести для додатку blog
Покриває: Post model, Comment model, PostForm, CommentForm, всі views
Використовує: django.test.TestCase, unittest.mock (Mock/Spy/patch)
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from blog.models import Post, Comment
from blog.forms import PostForm, CommentForm


# ══════════════════════════════════════════════════════
#  1. MODELS  — повне покриття (100%)
# ══════════════════════════════════════════════════════


class PostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="author", password="pass1234")
        self.post = Post.objects.create(
            title="Тестовий пост",
            content="Вміст поста",
            author=self.user,
        )

    # __str__
    def test_str_returns_title(self):
        self.assertEqual(str(self.post), "Тестовий пост")

    # get_absolute_url
    def test_get_absolute_url_contains_pk(self):
        url = self.post.get_absolute_url()
        self.assertEqual(url, reverse("post-detail", kwargs={"pk": self.post.pk}))

    # date_posted встановлюється автоматично
    def test_date_posted_set_automatically(self):
        self.assertIsNotNone(self.post.date_posted)
        self.assertLessEqual(self.post.date_posted, timezone.now())

    # ForeignKey author
    def test_author_is_correct(self):
        self.assertEqual(self.post.author, self.user)

    # ordering — новіший пост іде першим
    def test_ordering_newest_first(self):
        post2 = Post.objects.create(title="Новіший", content="...", author=self.user)
        posts = list(Post.objects.all())
        self.assertEqual(posts[0], post2)

    # title max_length = 200
    def test_title_max_length(self):
        max_length = Post._meta.get_field("title").max_length
        self.assertEqual(max_length, 200)

    # CASCADE: видалення user → видалення постів
    def test_posts_deleted_when_user_deleted(self):
        self.user.delete()
        self.assertEqual(Post.objects.count(), 0)

    # кілька постів одного автора
    def test_multiple_posts_same_author(self):
        Post.objects.create(title="P2", content="c", author=self.user)
        self.assertEqual(Post.objects.filter(author=self.user).count(), 2)


class CommentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="commenter", password="pass1234")
        self.post = Post.objects.create(title="Пост", content="Вміст", author=self.user)
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content="Мій коментар",
        )

    # __str__
    def test_str_format(self):
        expected = f'Коментар від {self.user.username} до "{self.post.title}"'
        self.assertEqual(str(self.comment), expected)

    # ForeignKey post
    def test_comment_linked_to_post(self):
        self.assertEqual(self.comment.post, self.post)

    # ForeignKey author
    def test_comment_author_correct(self):
        self.assertEqual(self.comment.author, self.user)

    # related_name 'comments'
    def test_related_name_comments(self):
        self.assertIn(self.comment, self.post.comments.all())

    # ordering: найстаріші перші
    def test_ordering_oldest_first(self):
        c2 = Comment.objects.create(post=self.post, author=self.user, content="Другий")
        comments = list(Comment.objects.all())
        self.assertEqual(comments[0], self.comment)
        self.assertEqual(comments[1], c2)

    # CASCADE: видалення поста → видалення коментарів
    def test_comments_deleted_when_post_deleted(self):
        self.post.delete()
        self.assertEqual(Comment.objects.count(), 0)

    # CASCADE: видалення user → видалення коментарів
    def test_comments_deleted_when_user_deleted(self):
        self.user.delete()
        self.assertEqual(Comment.objects.count(), 0)

    # date_posted
    def test_date_posted_auto_set(self):
        self.assertIsNotNone(self.comment.date_posted)


# ══════════════════════════════════════════════════════
#  2. FORMS  — повне покриття (100%)
# ══════════════════════════════════════════════════════


class PostFormTest(TestCase):
    def test_valid_form(self):
        form = PostForm(data={"title": "Заголовок", "content": "Вміст"})
        self.assertTrue(form.is_valid())

    def test_missing_title(self):
        form = PostForm(data={"title": "", "content": "Вміст"})
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_missing_content(self):
        form = PostForm(data={"title": "Заголовок", "content": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)

    def test_empty_form_invalid(self):
        form = PostForm(data={})
        self.assertFalse(form.is_valid())

    def test_fields_present(self):
        form = PostForm()
        self.assertIn("title", form.fields)
        self.assertIn("content", form.fields)

    def test_title_widget_has_class(self):
        form = PostForm()
        self.assertIn("form-control", form.fields["title"].widget.attrs.get("class", ""))

    def test_title_max_length_respected(self):
        long_title = "А" * 201
        form = PostForm(data={"title": long_title, "content": "Вміст"})
        self.assertFalse(form.is_valid())


class CommentFormTest(TestCase):
    def test_valid_form(self):
        form = CommentForm(data={"content": "Цікавий коментар"})
        self.assertTrue(form.is_valid())

    def test_empty_content_invalid(self):
        form = CommentForm(data={"content": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)

    def test_field_present(self):
        form = CommentForm()
        self.assertIn("content", form.fields)

    def test_content_widget_is_textarea(self):
        from django import forms as django_forms

        form = CommentForm()
        self.assertIsInstance(form.fields["content"].widget, django_forms.Textarea)


# ══════════════════════════════════════════════════════
#  3. VIEWS  — бізнес-логіка (~50%+ покриття)
#     Mock/Spy через unittest.mock
# ══════════════════════════════════════════════════════


class PostListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user1", password="pass")

    def test_status_200(self):
        response = self.client.get(reverse("blog-home"))
        self.assertEqual(response.status_code, 200)

    def test_correct_template(self):
        response = self.client.get(reverse("blog-home"))
        self.assertTemplateUsed(response, "blog/home.html")

    def test_context_has_posts(self):
        Post.objects.create(title="Видимий", content="ok", author=self.user)
        response = self.client.get(reverse("blog-home"))
        self.assertIn("posts", response.context)

    def test_paginate_by_5(self):
        for i in range(7):
            Post.objects.create(title=f"Post {i}", content="c", author=self.user)
        response = self.client.get(reverse("blog-home"))
        self.assertEqual(len(response.context["posts"]), 5)

    def test_second_page(self):
        for i in range(7):
            Post.objects.create(title=f"Post {i}", content="c", author=self.user)
        response = self.client.get(reverse("blog-home") + "?page=2")
        self.assertEqual(response.status_code, 200)


class UserPostListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="blogger", password="pass")
        self.other = User.objects.create_user(username="other", password="pass")
        self.post = Post.objects.create(title="Мій пост", content="c", author=self.user)
        Post.objects.create(title="Чужий пост", content="c", author=self.other)

    def test_status_200(self):
        response = self.client.get(reverse("user-posts", kwargs={"username": self.user.username}))
        self.assertEqual(response.status_code, 200)

    def test_template(self):
        response = self.client.get(reverse("user-posts", kwargs={"username": self.user.username}))
        self.assertTemplateUsed(response, "blog/user_posts.html")

    def test_only_user_posts_shown(self):
        response = self.client.get(reverse("user-posts", kwargs={"username": self.user.username}))
        posts = response.context["posts"]
        for post in posts:
            self.assertEqual(post.author, self.user)

    def test_context_has_author(self):
        response = self.client.get(reverse("user-posts", kwargs={"username": self.user.username}))
        self.assertEqual(response.context["author"], self.user)

    def test_404_for_nonexistent_user(self):
        response = self.client.get(reverse("user-posts", kwargs={"username": "nobody"}))
        self.assertEqual(response.status_code, 404)


class PostDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="author", password="pass")
        self.post = Post.objects.create(title="Деталі", content="вміст", author=self.user)

    def test_status_200(self):
        response = self.client.get(reverse("post-detail", kwargs={"pk": self.post.pk}))
        self.assertEqual(response.status_code, 200)

    def test_template(self):
        response = self.client.get(reverse("post-detail", kwargs={"pk": self.post.pk}))
        self.assertTemplateUsed(response, "blog/post_detail.html")

    def test_404_for_missing_post(self):
        response = self.client.get(reverse("post-detail", kwargs={"pk": 9999}))
        self.assertEqual(response.status_code, 404)

    def test_context_has_comments(self):
        response = self.client.get(reverse("post-detail", kwargs={"pk": self.post.pk}))
        self.assertIn("comments", response.context)

    def test_context_has_comment_form(self):
        response = self.client.get(reverse("post-detail", kwargs={"pk": self.post.pk}))
        self.assertIn("comment_form", response.context)
        self.assertIsInstance(response.context["comment_form"], CommentForm)


class PostCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="creator", password="pass")

    def test_requires_login_redirects(self):
        response = self.client.get(reverse("post-create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_authenticated_get_200(self):
        self.client.login(username="creator", password="pass")
        response = self.client.get(reverse("post-create"))
        self.assertEqual(response.status_code, 200)

    def test_post_creates_object(self):
        self.client.login(username="creator", password="pass")
        self.client.post(reverse("post-create"), {"title": "Новий", "content": "Вміст"})
        self.assertEqual(Post.objects.count(), 1)

    def test_author_set_to_current_user(self):
        self.client.login(username="creator", password="pass")
        self.client.post(reverse("post-create"), {"title": "Мій", "content": "Вміст"})
        self.assertEqual(Post.objects.first().author, self.user)

    def test_invalid_post_does_not_create(self):
        self.client.login(username="creator", password="pass")
        self.client.post(reverse("post-create"), {"title": "", "content": ""})
        self.assertEqual(Post.objects.count(), 0)

    @patch("blog.views.messages")
    def test_success_message_sent(self, mock_messages):
        """Spy — перевіряємо що messages.success викликається при створенні поста."""
        self.client.login(username="creator", password="pass")
        self.client.post(reverse("post-create"), {"title": "Тест", "content": "Вміст"})
        mock_messages.success.assert_called_once()


class PostUpdateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="editor", password="pass")
        self.other = User.objects.create_user(username="stranger", password="pass")
        self.post = Post.objects.create(title="Старий", content="старий", author=self.user)

    def test_author_can_update(self):
        self.client.login(username="editor", password="pass")
        self.client.post(
            reverse("post-update", kwargs={"pk": self.post.pk}),
            {"title": "Оновлений", "content": "новий вміст"},
        )
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Оновлений")

    def test_other_user_gets_403(self):
        self.client.login(username="stranger", password="pass")
        response = self.client.post(
            reverse("post-update", kwargs={"pk": self.post.pk}),
            {"title": "Зламаний", "content": "x"},
        )
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_redirects(self):
        response = self.client.get(reverse("post-update", kwargs={"pk": self.post.pk}))
        self.assertEqual(response.status_code, 302)

    @patch("blog.views.messages")
    def test_update_success_message(self, mock_messages):
        self.client.login(username="editor", password="pass")
        self.client.post(
            reverse("post-update", kwargs={"pk": self.post.pk}),
            {"title": "Оновлений", "content": "вміст"},
        )
        mock_messages.success.assert_called_once()


class PostDeleteViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="deleter", password="pass")
        self.other = User.objects.create_user(username="intruder", password="pass")
        self.post = Post.objects.create(title="Delete me", content="bye", author=self.user)

    def test_author_can_delete(self):
        self.client.login(username="deleter", password="pass")
        self.client.post(reverse("post-delete", kwargs={"pk": self.post.pk}))
        self.assertEqual(Post.objects.count(), 0)

    def test_other_user_cannot_delete(self):
        self.client.login(username="intruder", password="pass")
        response = self.client.post(reverse("post-delete", kwargs={"pk": self.post.pk}))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Post.objects.count(), 1)

    def test_unauthenticated_redirects(self):
        response = self.client.post(reverse("post-delete", kwargs={"pk": self.post.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Post.objects.count(), 1)

    def test_redirects_to_home_after_delete(self):
        self.client.login(username="deleter", password="pass")
        response = self.client.post(reverse("post-delete", kwargs={"pk": self.post.pk}))
        self.assertRedirects(response, "/")


class AddCommentViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="commenter", password="pass")
        self.post = Post.objects.create(title="Пост", content="вміст", author=self.user)

    def test_add_comment_creates_object(self):
        self.client.login(username="commenter", password="pass")
        self.client.post(
            reverse("add-comment", kwargs={"pk": self.post.pk}),
            {"content": "Мій коментар"},
        )
        self.assertEqual(Comment.objects.count(), 1)

    def test_comment_author_is_current_user(self):
        self.client.login(username="commenter", password="pass")
        self.client.post(
            reverse("add-comment", kwargs={"pk": self.post.pk}),
            {"content": "Привіт"},
        )
        self.assertEqual(Comment.objects.first().author, self.user)

    def test_comment_linked_to_post(self):
        self.client.login(username="commenter", password="pass")
        self.client.post(
            reverse("add-comment", kwargs={"pk": self.post.pk}),
            {"content": "Текст"},
        )
        self.assertEqual(Comment.objects.first().post, self.post)

    def test_invalid_comment_not_created(self):
        self.client.login(username="commenter", password="pass")
        self.client.post(
            reverse("add-comment", kwargs={"pk": self.post.pk}),
            {"content": ""},
        )
        self.assertEqual(Comment.objects.count(), 0)

    def test_redirects_to_post_detail(self):
        self.client.login(username="commenter", password="pass")
        response = self.client.post(
            reverse("add-comment", kwargs={"pk": self.post.pk}),
            {"content": "Ок"},
        )
        self.assertRedirects(response, reverse("post-detail", kwargs={"pk": self.post.pk}))

    def test_404_for_nonexistent_post(self):
        self.client.login(username="commenter", password="pass")
        response = self.client.post(
            reverse("add-comment", kwargs={"pk": 9999}),
            {"content": "Текст"},
        )
        self.assertEqual(response.status_code, 404)

    @patch("blog.views.messages")
    def test_success_message_on_comment(self, mock_messages):
        self.client.login(username="commenter", password="pass")
        self.client.post(
            reverse("add-comment", kwargs={"pk": self.post.pk}),
            {"content": "Коментар"},
        )
        mock_messages.success.assert_called_once()


class DeleteCommentViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="owner", password="pass")
        self.other = User.objects.create_user(username="alien", password="pass")
        self.post = Post.objects.create(title="Пост", content="вміст", author=self.user)
        self.comment = Comment.objects.create(post=self.post, author=self.user, content="Оригінальний")

    def test_author_can_delete_comment(self):
        self.client.login(username="owner", password="pass")
        self.client.post(reverse("delete-comment", kwargs={"pk": self.comment.pk}))
        self.assertEqual(Comment.objects.count(), 0)

    def test_other_user_cannot_delete_comment(self):
        self.client.login(username="alien", password="pass")
        self.client.post(reverse("delete-comment", kwargs={"pk": self.comment.pk}))
        self.assertEqual(Comment.objects.count(), 1)

    def test_redirects_to_post_after_delete(self):
        self.client.login(username="owner", password="pass")
        response = self.client.post(reverse("delete-comment", kwargs={"pk": self.comment.pk}))
        self.assertRedirects(response, reverse("post-detail", kwargs={"pk": self.post.pk}))

    @patch("blog.views.messages")
    def test_error_message_for_wrong_user(self, mock_messages):
        self.client.login(username="alien", password="pass")
        self.client.post(reverse("delete-comment", kwargs={"pk": self.comment.pk}))
        mock_messages.error.assert_called_once()
