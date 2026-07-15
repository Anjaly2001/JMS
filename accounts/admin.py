from django.contrib import admin

<<<<<<< HEAD
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'affiliation', 'created_at']
    list_filter = ['role']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'affiliation']
=======
# Register your models here.
>>>>>>> 6fbd5ab625782991d71a10edc3661e3dc19d8760
