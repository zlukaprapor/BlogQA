from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import CommentForm
from .models import Comment, Post


class PostListView(ListView):
    """Список всіх постів"""

    model = Post
    template_name = "blog/home.html"
    context_object_name = "posts"
    ordering = ["-date_posted"]
    paginate_by = 5


class UserPostListView(ListView):
    """Список постів конкретного користувача"""

    model = Post
    template_name = "blog/user_posts.html"
    context_object_name = "posts"
    paginate_by = 5

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get("username"))
        return Post.objects.filter(author=user).order_by("-date_posted")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["author"] = get_object_or_404(User, username=self.kwargs.get("username"))
        return context


class PostDetailView(DetailView):
    """Деталі поста з коментарями"""

    model = Post
    template_name = "blog/post_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comments"] = self.object.comments.all()
        context["comment_form"] = CommentForm()
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """Створення нового поста"""

    model = Post
    fields = ["title", "content"]
    template_name = "blog/post_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, "Пост успішно створено!")
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редагування поста"""

    model = Post
    fields = ["title", "content"]
    template_name = "blog/post_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, "Пост оновлено!")
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Видалення поста"""

    model = Post
    success_url = "/"
    template_name = "blog/post_confirm_delete.html"

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Пост видалено!")
        return super().delete(request, *args, **kwargs)


def add_comment(request, pk):
    """Додавання коментаря до поста"""
    post = get_object_or_404(Post, pk=pk)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, "Коментар додано!")
            return redirect("post-detail", pk=post.pk)

    return redirect("post-detail", pk=post.pk)


def delete_comment(request, pk):
    """Видалення коментаря"""
    comment = get_object_or_404(Comment, pk=pk)
    post_pk = comment.post.pk

    if request.user == comment.author:
        comment.delete()
        messages.success(request, "Коментар видалено!")
    else:
        messages.error(request, "Ви не можете видалити чужий коментар!")

    return redirect("post-detail", pk=post_pk)
