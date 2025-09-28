from django.contrib import admin
from .models import Classification

@admin.register(Classification)
class ClassificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'image', 'classification', 'created_at']
    list_filter = ['classification', 'created_at', 'updated_at']
    search_fields = ['user__email', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'image', 'classification', 'comment')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Register your models here.
