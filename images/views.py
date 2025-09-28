import os
import hashlib
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import Image
import json
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

def calculate_file_hash(file):
    """Calculate SHA256 hash of a file"""
    hash_sha256 = hashlib.sha256()
    for chunk in file.chunks():
        hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def ensure_upload_directory():
    """Ensure the upload directory exists, create if it doesn't"""
    upload_dir = os.path.join(settings.MEDIA_ROOT, settings.IMAGES_UPLOAD_DIR)
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        logger.info(f"Created upload directory: {upload_dir}")
    return upload_dir

def save_uploaded_file(file, file_hash):
    """Save the uploaded file with hash-based filename"""
    upload_dir = ensure_upload_directory()
    
    # Get file extension from original filename
    original_name = file.name
    file_extension = os.path.splitext(original_name)[1].lower()
    
    # Create filename using hash
    filename = f"{file_hash}{file_extension}"
    file_path = os.path.join(upload_dir, filename)
    
    # Save file to disk
    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    
    # Return relative path for database storage
    relative_path = os.path.join(settings.IMAGES_UPLOAD_DIR, filename)
    return relative_path

@csrf_exempt
@require_http_methods(["POST"])
def upload_image(request):
    try:
        if 'image' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No image file provided'
            }, status=400)
        
        uploaded_file = request.FILES['image']
        
        # Validate file type (basic check)
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return JsonResponse({
                'success': False,
                'error': f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'
            }, status=400)
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if uploaded_file.size > max_size:
            return JsonResponse({
                'success': False,
                'error': 'File too large. Maximum size is 10MB'
            }, status=400)
        
        # Calculate file hash
        file_hash = calculate_file_hash(uploaded_file)
        
        # Check if image with this hash already exists
        existing_image = Image.objects.filter(file_hash=file_hash).first()
        if existing_image:
            return JsonResponse({
                'success': True,
                'message': 'Image already exists',
                'image_id': existing_image.id,
                'file_path': existing_image.file_path,
                'duplicate': True
            })
        
        # Save file to disk
        file_path = save_uploaded_file(uploaded_file, file_hash)
        
        # Get user if user_id is provided
        user = None
        user_id = request.POST.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.warning(f"User with id {user_id} not found")
        
        # Create database record
        image = Image.objects.create(
            file_path=file_path,
            file_hash=file_hash,
            original_filename=uploaded_file.name,
            file_size=uploaded_file.size,
            uploaded_by=user
        )
        
        logger.info(f"Image uploaded successfully: {image.id} - {uploaded_file.name}")
        
        return JsonResponse({
            'success': True,
            'message': 'Image uploaded successfully',
            'image_id': image.id,
            'file_path': image.file_path,
            'file_hash': image.file_hash,
            'original_filename': image.original_filename,
            'file_size': image.file_size,
            'uploaded_at': image.uploaded_at.isoformat(),
            'duplicate': False
        })
        
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@require_http_methods(["GET"])
def get_image_info(request, image_id):
    """Get information about a specific image"""
    try:
        image = Image.objects.get(id=image_id)
        
        return JsonResponse({
            'success': True,
            'image': {
                'id': image.id,
                'file_path': image.file_path,
                'file_hash': image.file_hash,
                'original_filename': image.original_filename,
                'file_size': image.file_size,
                'uploaded_at': image.uploaded_at.isoformat(),
                'uploaded_by': image.uploaded_by.email if image.uploaded_by else None
            }
        })
        
    except Image.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Image not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error getting image info: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@require_http_methods(["GET"])
def list_images(request):
    """List all images with optional filtering"""
    try:
        images = Image.objects.all().order_by('-uploaded_at')
        
        # Optional filtering by user
        user_id = request.GET.get('user_id')
        if user_id:
            images = images.filter(uploaded_by_id=user_id)
        
        # Pagination
        limit = int(request.GET.get('limit', 20))
        offset = int(request.GET.get('offset', 0))
        
        total_count = images.count()
        images = images[offset:offset + limit]
        
        images_data = []
        for image in images:
            images_data.append({
                'id': image.id,
                'file_path': image.file_path,
                'file_hash': image.file_hash,
                'original_filename': image.original_filename,
                'file_size': image.file_size,
                'uploaded_at': image.uploaded_at.isoformat(),
                'uploaded_by': image.uploaded_by.email if image.uploaded_by else None
            })
        
        return JsonResponse({
            'success': True,
            'images': images_data,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Error listing images: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@require_http_methods(["GET"])
def upload_page(request):
    """Render the HTML upload page"""
    return render(request, 'images/upload.html')

# Create your views here.
