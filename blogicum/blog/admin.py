from django.contrib import admin

# Register your models here.
from .models import Category, Location, Post, Comment


admin.site.register(Category)
admin.site.register(Location)
admin.site.register(Post)
admin.site.register(Comment)
