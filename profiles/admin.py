from django.contrib import admin

from profiles.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "is_private", "created_at", "updated_at")
    search_fields = ("user__username", "user__email", "user__display_name")
    list_filter = ("is_private",)
