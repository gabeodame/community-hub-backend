from django.contrib import admin

from groups.models import Group, Membership


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "visibility", "join_policy", "created_by")
    search_fields = ("name", "slug", "created_by__username")
    list_filter = ("visibility", "join_policy")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("id", "group", "user", "role", "status", "created_at")
    search_fields = ("group__name", "user__username")
    list_filter = ("role", "status")
