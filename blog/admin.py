from django.contrib import admin

from .models import Comment, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "date_posted"]
    list_filter = ["date_posted", "author"]
    search_fields = ["title", "content"]
    date_hierarchy = "date_posted"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["author", "post", "date_posted", "content_preview"]
    list_filter = ["date_posted", "author"]
    search_fields = ["content", "author__username"]

    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    content_preview.short_description = "Зміст"
