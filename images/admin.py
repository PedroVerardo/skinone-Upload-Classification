from django.contrib import admin
from .models import Image

# Register your models here.

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'original_filename', 'file_size', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at', 'uploaded_by']
    search_fields = ['original_filename', 'file_hash', 'uploaded_by__email']
    readonly_fields = ['file_hash', 'file_size', 'uploaded_at']
    
    fieldsets = (
        (None, {
            'fields': ('original_filename', 'file_path', 'uploaded_by')
        }),
        ('File Details', {
            'fields': ('file_hash', 'file_size', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
