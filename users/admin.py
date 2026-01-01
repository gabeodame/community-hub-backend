from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("id", "username", "email", "display_name", "is_staff", "is_active")
    search_fields = ("username", "email", "display_name")
    list_filter = ("is_staff", "is_superuser", "is_active")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Profile", {"fields": ("display_name",)}),
    )
