from django.contrib import admin
from .models import Classification

@admin.register(Classification)
class ClassificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'image', 'stage', 'created_at']
    list_filter = ['stage', 'created_at', 'updated_at']
    search_fields = ['user__email', 'observations']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'image', 'stage', 'observations')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Register your models here.
