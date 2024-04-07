from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin
from accounts.models import User, UserProfile


# Register your models here.
class CustomUserAdmin(UserAdmin):
    list_display = ["email", "first_name", "last_name", "username", "role", "is_active"]
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()
    ordering = ["-id"]


class UserProfileAdmin(ModelAdmin):
    ordering = ["-id"]





admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
