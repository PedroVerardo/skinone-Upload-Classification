import os
import hashlib
import base64
import io
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile
from .models import Image
import json
import logging
from functools import wraps
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, OpenApiResponse

logger = logging.getLogger(__name__)
User = get_user_model()

def verify_jwt_token(token):
    """
    Verify JWT token - import from users app
    """
    try:
        from users.views import verify_jwt_token as verify_token
        return verify_token(token)
    except Exception as e:
        logger.error(f"JWT verification error: {str(e)}")
        return None, "Token verification failed"

def jwt_required(f):
    """
    Decorator to require JWT authentication
    """
    @wraps(f)
    def decorated_function(request, *args, **kwargs):
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({
                'success': False,
                'error': 'Authorization header missing or invalid format'
            }, status=401)
        
        token = auth_header.split(' ')[1]
        user_id, error = verify_jwt_token(token)
        
        if error:
            return JsonResponse({
                'success': False,
                'error': f'Authentication failed: {error}'
            }, status=401)
        
        # Get user object
        try:
            user = User.objects.get(id=user_id)
            request.user = user  # Add user to request
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=401)
        
        return f(request, *args, **kwargs)
    return decorated_function

def calculate_file_hash_from_content(content):
    """Calculate SHA256 hash from file content (bytes)"""
    hash_sha256 = hashlib.sha256()
    hash_sha256.update(content)
    return hash_sha256.hexdigest()

def decode_base64_image(base64_string, filename=None):
    """
    Decode base64 image and return file-like object
    """
    try:
        # Remove data URL prefix if present (data:image/jpeg;base64,)
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_string)
        
        # Create file-like object
        image_file = io.BytesIO(image_data)
        
        # Create InMemoryUploadedFile
        if not filename:
            filename = 'uploaded_image.jpg'
        
        uploaded_file = InMemoryUploadedFile(
            image_file, None, filename, 'image/jpeg', len(image_data), None
        )
        
        return uploaded_file, len(image_data)
    except Exception as e:
        logger.error(f"Base64 decode error: {str(e)}")
        return None, 0

def save_image_from_content(content, file_hash, original_filename):
    """Save image content directly to disk"""
    upload_dir = ensure_upload_directory()
    
    # Get file extension from original filename
    file_extension = os.path.splitext(original_filename)[1].lower()
    if not file_extension:
        file_extension = '.jpg'  # Default extension
    
    # Create filename using hash
    filename = f"{file_hash}{file_extension}"
    file_path = os.path.join(upload_dir, filename)
    
    # Save file to disk
    with open(file_path, 'wb') as destination:
        destination.write(content)
    
    # Return relative path for database storage
    relative_path = os.path.join(settings.IMAGES_UPLOAD_DIR, filename)
    return relative_path

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
    upload_dir = ensure_upload_directory()
    
    original_name = file.name
    file_extension = os.path.splitext(original_name)[1].lower()
    
    filename = f"{file_hash}{file_extension}"
    file_path = os.path.join(upload_dir, filename)
    
    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    relative_path = os.path.join(settings.IMAGES_UPLOAD_DIR, filename)
    return relative_path

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def upload_image(request):
    """
    Upload a single image file (requires JWT authentication)
    Expected: multipart/form-data with 'image' field
    """
    try:
        # Check if image file was provided
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
        
        file_path = save_uploaded_file(uploaded_file, file_hash)
        
        image = Image.objects.create(
            file_path=file_path,
            file_hash=file_hash,
            original_filename=uploaded_file.name,
            file_size=uploaded_file.size,
            uploaded_by=request.user
        )
        
        logger.info(f"Image uploaded successfully: {image.id} - {uploaded_file.name} by {request.user.email}")
        
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

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def upload_batch_images(request):
    """
    Upload multiple images in batch
    Expected: multipart/form-data with multiple 'images' fields
    """
    try:
        # Get all image files
        uploaded_files = request.FILES.getlist('images')
        
        if not uploaded_files:
            return JsonResponse({
                'success': False,
                'error': 'No image files provided'
            }, status=400)
        
        # Validate number of files (max 20 per batch)
        if len(uploaded_files) > 20:
            return JsonResponse({
                'success': False,
                'error': 'Too many files. Maximum 20 files per batch'
            }, status=400)
        
        results = []
        successful_uploads = 0
        errors = []
        
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        max_size = 10 * 1024 * 1024
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                # Validate file type
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                if file_extension not in allowed_extensions:
                    errors.append(f"File {i+1} ({uploaded_file.name}): Invalid file type")
                    continue
                
                # Validate file size
                if uploaded_file.size > max_size:
                    errors.append(f"File {i+1} ({uploaded_file.name}): File too large (max 10MB)")
                    continue
                
                # Calculate file hash
                file_hash = calculate_file_hash(uploaded_file)
                
                # Check if image already exists
                existing_image = Image.objects.filter(file_hash=file_hash).first()
                if existing_image:
                    results.append({
                        'index': i + 1,
                        'filename': uploaded_file.name,
                        'status': 'duplicate',
                        'message': 'Image already exists',
                        'image_id': existing_image.id,
                        'file_path': existing_image.file_path
                    })
                    continue
                
                # Save file to disk
                file_path = save_uploaded_file(uploaded_file, file_hash)
                
                # Create database record
                image = Image.objects.create(
                    file_path=file_path,
                    file_hash=file_hash,
                    original_filename=uploaded_file.name,
                    file_size=uploaded_file.size,
                    uploaded_by=request.user
                )
                
                results.append({
                    'index': i + 1,
                    'filename': uploaded_file.name,
                    'status': 'success',
                    'message': 'Image uploaded successfully',
                    'image_id': image.id,
                    'file_path': image.file_path,
                    'file_hash': image.file_hash,
                    'file_size': image.file_size,
                    'uploaded_at': image.uploaded_at.isoformat()
                })
                
                successful_uploads += 1
                
            except Exception as e:
                errors.append(f"File {i+1} ({uploaded_file.name}): {str(e)}")
        
        logger.info(f"Batch upload completed: {successful_uploads} successful, {len(errors)} errors by {request.user.email}")
        
        return JsonResponse({
            'success': True,
            'message': f'Batch upload completed: {successful_uploads}/{len(uploaded_files)} files processed',
            'results': results,
            'successful_uploads': successful_uploads,
            'total_files': len(uploaded_files),
            'errors': errors
        })
        
    except Exception as e:
        logger.error(f"Error in batch upload: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def upload_base64_image(request):
    """
    Upload image from base64 data (requires JWT authentication)
    Expected JSON: {
        "image_data": "base64_string_here",
        "filename": "optional_filename.jpg"
    }
    """
    try:
        data = json.loads(request.body)
        base64_data = data.get('image_data', '')
        filename = data.get('filename', 'uploaded_image.jpg')
        
        if not base64_data:
            return JsonResponse({
                'success': False,
                'error': 'No base64 image data provided'
            }, status=400)
        
        # Decode base64 image
        uploaded_file, file_size = decode_base64_image(base64_data, filename)
        
        if not uploaded_file:
            return JsonResponse({
                'success': False,
                'error': 'Invalid base64 image data'
            }, status=400)
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            return JsonResponse({
                'success': False,
                'error': 'File too large. Maximum size is 10MB'
            }, status=400)
        
        # Get image content for hash calculation
        uploaded_file.seek(0)
        image_content = uploaded_file.read()
        
        # Calculate file hash
        file_hash = calculate_file_hash_from_content(image_content)
        
        # Check if image already exists
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
        file_path = save_image_from_content(image_content, file_hash, filename)
        
        # Create database record
        image = Image.objects.create(
            file_path=file_path,
            file_hash=file_hash,
            original_filename=filename,
            file_size=file_size,
            uploaded_by=request.user
        )
        
        logger.info(f"Base64 image uploaded successfully: {image.id} - {filename} by {request.user.email}")
        
        return JsonResponse({
            'success': True,
            'message': 'Base64 image uploaded successfully',
            'image_id': image.id,
            'file_path': image.file_path,
            'file_hash': image.file_hash,
            'original_filename': image.original_filename,
            'file_size': image.file_size,
            'uploaded_at': image.uploaded_at.isoformat(),
            'duplicate': False
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error uploading base64 image: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def upload_batch_base64_images(request):
    """
    Upload multiple images from base64 data (requires JWT authentication)
    Expected JSON: {
        "images": [
            {"image_data": "base64_string_1", "filename": "image1.jpg"},
            {"image_data": "base64_string_2", "filename": "image2.jpg"}
        ]
    }
    """
    try:
        data = json.loads(request.body)
        images_data = data.get('images', [])
        
        if not images_data:
            return JsonResponse({
                'success': False,
                'error': 'No images data provided'
            }, status=400)
        
        # Validate number of images (max 20 per batch)
        if len(images_data) > 20:
            return JsonResponse({
                'success': False,
                'error': 'Too many images. Maximum 20 images per batch'
            }, status=400)
        
        results = []
        successful_uploads = 0
        errors = []
        max_size = 10 * 1024 * 1024  # 10MB
        
        for i, img_data in enumerate(images_data):
            try:
                base64_data = img_data.get('image_data', '')
                filename = img_data.get('filename', f'uploaded_image_{i+1}.jpg')
                
                if not base64_data:
                    errors.append(f"Image {i+1}: No base64 data provided")
                    continue
                
                uploaded_file, file_size = decode_base64_image(base64_data, filename)
                
                if not uploaded_file:
                    errors.append(f"Image {i+1} ({filename}): Invalid base64 data")
                    continue
                
                # Validate file size
                if file_size > max_size:
                    errors.append(f"Image {i+1} ({filename}): File too large (max 10MB)")
                    continue
                
                # Get image content for hash calculation
                uploaded_file.seek(0)
                image_content = uploaded_file.read()
                
                # Calculate file hash
                file_hash = calculate_file_hash_from_content(image_content)
                
                # Check if image already exists
                existing_image = Image.objects.filter(file_hash=file_hash).first()
                if existing_image:
                    results.append({
                        'index': i + 1,
                        'filename': filename,
                        'status': 'duplicate',
                        'message': 'Image already exists',
                        'image_id': existing_image.id,
                        'file_path': existing_image.file_path
                    })
                    continue
                
                # Save file to disk
                file_path = save_image_from_content(image_content, file_hash, filename)
                
                # Create database record
                image = Image.objects.create(
                    file_path=file_path,
                    file_hash=file_hash,
                    original_filename=filename,
                    file_size=file_size,
                    uploaded_by=request.user
                )
                
                results.append({
                    'index': i + 1,
                    'filename': filename,
                    'status': 'success',
                    'message': 'Image uploaded successfully',
                    'image_id': image.id,
                    'file_path': image.file_path,
                    'file_hash': image.file_hash,
                    'file_size': image.file_size,
                    'uploaded_at': image.uploaded_at.isoformat()
                })
                
                successful_uploads += 1
                
            except Exception as e:
                errors.append(f"Image {i+1}: {str(e)}")
        
        logger.info(f"Batch base64 upload completed: {successful_uploads} successful, {len(errors)} errors by {request.user.email}")
        
        return JsonResponse({
            'success': True,
            'message': f'Batch base64 upload completed: {successful_uploads}/{len(images_data)} images processed',
            'results': results,
            'successful_uploads': successful_uploads,
            'total_images': len(images_data),
            'errors': errors
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in batch base64 upload: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@require_http_methods(["GET"])
def get_image_info(request, image_id):
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
    try:
        images = Image.objects.all().order_by('-uploaded_at')
        
        user_id = request.GET.get('user_id')
        if user_id:
            images = images.filter(uploaded_by_id=user_id)
        
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
    return render(request, 'images/upload_new.html')

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def upload_image_with_classification(request):
    """
    Upload image(s) with embedded classification
    Supports both single and batch upload with classification
    
    For multipart/form-data:
    - Single: image file + classification + comment
    - Batch: multiple image files + classifications array
    
    For JSON (base64):
    - Single: {"image_data": "base64", "filename": "name", "classification": "stage1", "comment": "text"}
    - Batch: {"images": [{"image_data": "base64", "classification": "stage1", ...}]}
    """
    try:
        from classification.models import Classification
        
        # Check content type to determine processing method
        content_type = request.content_type
        
        if 'multipart/form-data' in content_type:
            return _handle_multipart_upload_with_classification(request)
        elif 'application/json' in content_type:
            return _handle_json_upload_with_classification(request)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Unsupported content type. Use multipart/form-data or application/json'
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error in upload with classification: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

def _handle_multipart_upload_with_classification(request):
    """Handle multipart form upload with classification"""
    from classification.models import Classification
    
    # Get files
    uploaded_files = request.FILES.getlist('images') if 'images' in request.FILES else []
    single_file = request.FILES.get('image')
    
    if single_file:
        uploaded_files = [single_file]
    
    if not uploaded_files:
        return JsonResponse({
            'success': False,
            'error': 'No image files provided'
        }, status=400)
    
    # Get classifications - can be single value or array
    classifications = request.POST.getlist('classifications') if 'classifications' in request.POST else []
    single_classification = request.POST.get('classification')
    
    if single_classification and not classifications:
        classifications = [single_classification]
    
    # Get comments - can be single value or array
    comments = request.POST.getlist('comments') if 'comments' in request.POST else []
    single_comment = request.POST.get('comment', '')
    
    if single_comment and not comments:
        comments = [single_comment]
    
    # Validate classification choices
    valid_choices = [choice[0] for choice in Classification.CLASSIFICATION_CHOICES]
    
    results = []
    successful_uploads = 0
    errors = []
    
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    max_size = 10 * 1024 * 1024
    
    for i, uploaded_file in enumerate(uploaded_files):
        try:
            # Get classification for this file
            classification = classifications[i] if i < len(classifications) else classifications[0] if classifications else None
            comment = comments[i] if i < len(comments) else comments[0] if comments else ''
            
            if not classification:
                errors.append(f"File {i+1} ({uploaded_file.name}): No classification provided")
                continue
            
            if classification not in valid_choices:
                errors.append(f"File {i+1} ({uploaded_file.name}): Invalid classification '{classification}'")
                continue
            
            # Validate file
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            if file_extension not in allowed_extensions:
                errors.append(f"File {i+1} ({uploaded_file.name}): Invalid file type")
                continue
            
            if uploaded_file.size > max_size:
                errors.append(f"File {i+1} ({uploaded_file.name}): File too large (max 10MB)")
                continue
            
            # Calculate file hash
            file_hash = calculate_file_hash(uploaded_file)
            
            # Check if image already exists
            existing_image = Image.objects.filter(file_hash=file_hash).first()
            if existing_image:
                # Create classification for existing image
                classification_obj = Classification.objects.create(
                    user=request.user,
                    image=existing_image,
                    classification=classification,
                    comment=comment
                )
                
                results.append({
                    'index': i + 1,
                    'filename': uploaded_file.name,
                    'status': 'duplicate_with_classification',
                    'message': 'Image already exists, classification added',
                    'image_id': existing_image.id,
                    'file_path': existing_image.file_path,
                    'classification': {
                        'id': classification_obj.id,
                        'classification': classification_obj.classification,
                        'comment': classification_obj.comment
                    }
                })
                successful_uploads += 1
                continue
            
            # Save new image
            file_path = save_uploaded_file(uploaded_file, file_hash)
            
            image = Image.objects.create(
                file_path=file_path,
                file_hash=file_hash,
                original_filename=uploaded_file.name,
                file_size=uploaded_file.size,
                uploaded_by=request.user
            )
            
            # Create classification
            classification_obj = Classification.objects.create(
                user=request.user,
                image=image,
                classification=classification,
                comment=comment
            )
            
            results.append({
                'index': i + 1,
                'filename': uploaded_file.name,
                'status': 'success',
                'message': 'Image uploaded and classified successfully',
                'image_id': image.id,
                'file_path': image.file_path,
                'file_hash': image.file_hash,
                'file_size': image.file_size,
                'uploaded_at': image.uploaded_at.isoformat(),
                'classification': {
                    'id': classification_obj.id,
                    'classification': classification_obj.classification,
                    'comment': classification_obj.comment,
                    'created_at': classification_obj.created_at.isoformat()
                }
            })
            
            successful_uploads += 1
            
        except Exception as e:
            errors.append(f"File {i+1} ({uploaded_file.name}): {str(e)}")
    
    logger.info(f"Upload with classification completed: {successful_uploads} successful, {len(errors)} errors by {request.user.email}")
    
    return JsonResponse({
        'success': True,
        'message': f'Upload with classification completed: {successful_uploads}/{len(uploaded_files)} files processed',
        'results': results,
        'successful_uploads': successful_uploads,
        'total_files': len(uploaded_files),
        'errors': errors
    })

def _handle_json_upload_with_classification(request):
    """Handle JSON base64 upload with classification"""
    from classification.models import Classification
    
    data = json.loads(request.body)
    
    # Single image or batch?
    if 'image_data' in data:
        # Single image
        images_data = [data]
    elif 'images' in data:
        # Batch images
        images_data = data.get('images', [])
    else:
        return JsonResponse({
            'success': False,
            'error': 'No image data provided. Use "image_data" for single or "images" for batch'
        }, status=400)
    
    if len(images_data) > 20:
        return JsonResponse({
            'success': False,
            'error': 'Too many images. Maximum 20 images per batch'
        }, status=400)
    
    valid_choices = [choice[0] for choice in Classification.CLASSIFICATION_CHOICES]
    results = []
    successful_uploads = 0
    errors = []
    max_size = 10 * 1024 * 1024
    
    for i, img_data in enumerate(images_data):
        try:
            base64_data = img_data.get('image_data', '')
            filename = img_data.get('filename', f'uploaded_image_{i+1}.jpg')
            classification = img_data.get('classification', '')
            comment = img_data.get('comment', '')
            
            if not base64_data:
                errors.append(f"Image {i+1}: No base64 data provided")
                continue
            
            if not classification:
                errors.append(f"Image {i+1} ({filename}): No classification provided")
                continue
            
            if classification not in valid_choices:
                errors.append(f"Image {i+1} ({filename}): Invalid classification '{classification}'")
                continue
            
            # Decode base64 image
            uploaded_file, file_size = decode_base64_image(base64_data, filename)
            
            if not uploaded_file:
                errors.append(f"Image {i+1} ({filename}): Invalid base64 data")
                continue
            
            if file_size > max_size:
                errors.append(f"Image {i+1} ({filename}): File too large (max 10MB)")
                continue
            
            # Get image content for hash calculation
            uploaded_file.seek(0)
            image_content = uploaded_file.read()
            
            # Calculate file hash
            file_hash = calculate_file_hash_from_content(image_content)
            
            # Check if image already exists
            existing_image = Image.objects.filter(file_hash=file_hash).first()
            if existing_image:
                # Create classification for existing image
                classification_obj = Classification.objects.create(
                    user=request.user,
                    image=existing_image,
                    classification=classification,
                    comment=comment
                )
                
                results.append({
                    'index': i + 1,
                    'filename': filename,
                    'status': 'duplicate_with_classification',
                    'message': 'Image already exists, classification added',
                    'image_id': existing_image.id,
                    'file_path': existing_image.file_path,
                    'classification': {
                        'id': classification_obj.id,
                        'classification': classification_obj.classification,
                        'comment': classification_obj.comment
                    }
                })
                successful_uploads += 1
                continue
            
            # Save new image
            file_path = save_image_from_content(image_content, file_hash, filename)
            
            image = Image.objects.create(
                file_path=file_path,
                file_hash=file_hash,
                original_filename=filename,
                file_size=file_size,
                uploaded_by=request.user
            )
            
            # Create classification
            classification_obj = Classification.objects.create(
                user=request.user,
                image=image,
                classification=classification,
                comment=comment
            )
            
            results.append({
                'index': i + 1,
                'filename': filename,
                'status': 'success',
                'message': 'Image uploaded and classified successfully',
                'image_id': image.id,
                'file_path': image.file_path,
                'file_hash': image.file_hash,
                'file_size': image.file_size,
                'uploaded_at': image.uploaded_at.isoformat(),
                'classification': {
                    'id': classification_obj.id,
                    'classification': classification_obj.classification,
                    'comment': classification_obj.comment,
                    'created_at': classification_obj.created_at.isoformat()
                }
            })
            
            successful_uploads += 1
            
        except Exception as e:
            errors.append(f"Image {i+1}: {str(e)}")
    
    logger.info(f"JSON upload with classification completed: {successful_uploads} successful, {len(errors)} errors by {request.user.email}")
    
    return JsonResponse({
        'success': True,
        'message': f'Upload with classification completed: {successful_uploads}/{len(images_data)} images processed',
        'results': results,
        'successful_uploads': successful_uploads,
        'total_images': len(images_data),
        'errors': errors
    })

# New views matching API specification exactly

class ImageListItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    url = serializers.CharField(allow_null=True)

class UploadBatchResponseItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    url = serializers.CharField()
    status = serializers.CharField()

class UploadBatchResponseSerializer(serializers.Serializer):
    upload_batch_id = serializers.CharField()
    uploaded = UploadBatchResponseItemSerializer(many=True)

class UploadSingleResponseSerializer(serializers.Serializer):
    image = serializers.DictField()

class UploadSingleRequestSerializer(serializers.Serializer):
    image = serializers.FileField()

class UploadBatchRequestSerializer(serializers.Serializer):
    images = serializers.ListField(child=serializers.FileField())

@extend_schema(
    tags=["Images"],
    summary="List images",
    responses={200: ImageListItemSerializer(many=True), 500: OpenApiResponse(description='Internal server error')},
)
@api_view(["GET"])
@jwt_required
def list_images(request):
    """
    GET /images/
    Auth required
    Response: 200 OK, [ { id, url } ]
    """
    try:
        images = Image.objects.all().order_by('-uploaded_at')
        
        images_data = []
        for image in images:
            # Generate URL based on MEDIA_URL and file_path
            url = f"{settings.MEDIA_URL}{image.file_path}" if image.file_path else None
            images_data.append({
                'id': image.id,
                'url': url
            })
        
        return JsonResponse(images_data, safe=False, status=200)
        
    except Exception as e:
        logger.error(f"Error listing images: {str(e)}")
        return JsonResponse({
            'message': 'Internal server error'
        }, status=500)

@csrf_exempt
@extend_schema(
    tags=["Images"],
    summary="Upload images (batch)",
    request={
        'multipart/form-data': UploadBatchRequestSerializer,
    },
    responses={201: UploadBatchResponseSerializer, 400: OpenApiResponse(description='Bad request'), 500: OpenApiResponse(description='Internal server error')},
)
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
@jwt_required
def upload_batch_images(request):
    """
    POST /images/upload/
    Auth required
    Multipart form
    Field: images (repeatable) -> multiple files allowed
    Response: 201 Created, { upload_batch_id, uploaded }
    """
    try:
        import uuid
        
        # Get all image files
        uploaded_files = request.FILES.getlist('images')
        
        if not uploaded_files:
            return JsonResponse({
                'message': 'No image files provided'
            }, status=400)
        
        upload_batch_id = str(uuid.uuid4())
        uploaded = []
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        max_size = 10 * 1024 * 1024
        
        for uploaded_file in uploaded_files:
            try:
                # Validate file type
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                if file_extension not in allowed_extensions:
                    continue
                
                # Validate file size
                if uploaded_file.size > max_size:
                    continue
                
                # Calculate file hash
                file_hash = calculate_file_hash(uploaded_file)
                
                # Check if image already exists (skip if exists)
                existing_image = Image.objects.filter(file_hash=file_hash).first()
                if existing_image:
                    uploaded.append({
                        'id': existing_image.id,
                        'url': f"{settings.MEDIA_URL}{existing_image.file_path}",
                        'status': 'existing'
                    })
                    continue
                
                # Save file to disk
                file_path = save_uploaded_file(uploaded_file, file_hash)
                
                # Create database record
                image = Image.objects.create(
                    file_path=file_path,
                    file_hash=file_hash,
                    original_filename=uploaded_file.name,
                    file_size=uploaded_file.size,
                    uploaded_by=request.user
                )
                
                uploaded.append({
                    'id': image.id,
                    'url': f"{settings.MEDIA_URL}{image.file_path}",
                    'status': 'uploaded'
                })
                
            except Exception as e:
                logger.error(f"Error processing file {uploaded_file.name}: {str(e)}")
                continue
        
        logger.info(f"Batch upload completed: {len(uploaded)} files processed by {request.user.name}")
        
        return JsonResponse({
            'success': True,
            'upload_batch_id': upload_batch_id,
            'uploaded': uploaded
        }, status=201)
        
    except Exception as e:
        logger.error(f"Error in batch upload: {str(e)}")
        return JsonResponse({
            'message': 'Internal server error'
        }, status=500)

@csrf_exempt
@extend_schema(
    tags=["Images"],
    summary="Upload single image",
    request={
        'multipart/form-data': UploadSingleRequestSerializer,
    },
    responses={201: UploadSingleResponseSerializer, 400: OpenApiResponse(description='Bad request'), 500: OpenApiResponse(description='Internal server error')},
)
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
@jwt_required
def upload_single_image(request):
    """
    POST /images/upload/single/
    Auth required
    Multipart form
    Field: image
    Response: 201 Created, { image: { id, url } }
    """
    try:
        # Check if image file was provided
        if 'image' not in request.FILES:
            return JsonResponse({
                'message': 'No image file provided'
            }, status=400)
        
        uploaded_file = request.FILES['image']
        
        # Validate file type
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return JsonResponse({
                'message': f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'
            }, status=400)
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024
        if uploaded_file.size > max_size:
            return JsonResponse({
                'message': 'File too large. Maximum size is 10MB'
            }, status=400)
        
        # Calculate file hash
        file_hash = calculate_file_hash(uploaded_file)
        
        # Check if image already exists
        existing_image = Image.objects.filter(file_hash=file_hash).first()
        if existing_image:
            return JsonResponse({
                'image': {
                    'id': existing_image.id,
                    'url': f"{settings.MEDIA_URL}{existing_image.file_path}"
                }
            }, status=201)
        
        # Save file to disk
        file_path = save_uploaded_file(uploaded_file, file_hash)
        
        # Create database record
        image = Image.objects.create(
            file_path=file_path,
            file_hash=file_hash,
            original_filename=uploaded_file.name,
            file_size=uploaded_file.size,
            uploaded_by=request.user
        )
        
        logger.info(f"Single image uploaded: {image.id} - {uploaded_file.name} by {request.user.name}")
        
        return JsonResponse({
            'success': True,
            'image': {
                'id': image.id,
                'url': f"{settings.MEDIA_URL}{image.file_path}"
            }
        }, status=201)
        
    except Exception as e:
        logger.error(f"Error uploading single image: {str(e)}")
        return JsonResponse({
            'message': 'Internal server error'
        }, status=500)

@csrf_exempt
@extend_schema(
    tags=["Images"],
    summary="Upload images with stage",
    request={
        'multipart/form-data': UploadBatchRequestSerializer,
    },
    responses={201: UploadBatchResponseSerializer, 400: OpenApiResponse(description='Bad request'), 500: OpenApiResponse(description='Internal server error')},
)
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_with_stage(request):
    """
    POST /images/upload/with-stage/?stage=<estagio>
    Auth required
    Multipart form
    Field: images (repeatable)
    Query param: stage: "estagio1"|"estagio2"|"estagio3"|"estagio4"|"nao_classificavel"|"dtpi"
    Efeito: cria imagens e já registra classificação para cada uma
    Response: 201 Created, { upload_batch_id, uploaded, stage, classified }
    """
    try:
        import uuid
        from classification.models import Classification
        
        # Get stage from query parameter
        stage = request.GET.get('stage')
        if not stage:
            return JsonResponse({
                'message': 'Stage parameter is required'
            }, status=400)
        
        # Validate stage value
        valid_stages = [choice[0] for choice in Classification.CLASSIFICATION_CHOICES]
        if stage not in valid_stages:
            return JsonResponse({
                'message': f'Invalid stage. Valid options: {valid_stages}'
            }, status=400)
        
        # Get all image files
        uploaded_files = request.FILES.getlist('images')
        
        if not uploaded_files:
            return JsonResponse({
                'message': 'No image files provided'
            }, status=400)
        
        upload_batch_id = str(uuid.uuid4())
        uploaded = []
        classified = []
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        max_size = 10 * 1024 * 1024
        
        for uploaded_file in uploaded_files:
            try:
                # Validate file type
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                if file_extension not in allowed_extensions:
                    continue
                
                # Validate file size
                if uploaded_file.size > max_size:
                    continue
                
                # Calculate file hash
                file_hash = calculate_file_hash(uploaded_file)
                
                # Check if image already exists
                existing_image = Image.objects.filter(file_hash=file_hash).first()
                if existing_image:
                    image = existing_image
                    uploaded.append({
                        'id': image.id,
                        'url': f"{settings.MEDIA_URL}{image.file_path}",
                        'status': 'existing'
                    })
                else:
                    # Save new file
                    file_path = save_uploaded_file(uploaded_file, file_hash)
                    
                    # Create database record
                    image = Image.objects.create(
                        file_path=file_path,
                        file_hash=file_hash,
                        original_filename=uploaded_file.name,
                        file_size=uploaded_file.size,
                        uploaded_by=request.user
                    )
                    
                    uploaded.append({
                        'id': image.id,
                        'url': f"{settings.MEDIA_URL}{image.file_path}",
                        'status': 'uploaded'
                    })
                
                # Create classification for the image
                classification = Classification.objects.create(
                    user=request.user,
                    image=image,
                    stage=stage,
                    observations=''  # No observations for batch classification
                )
                
                classified.append({
                    'id': classification.id,
                    'image_id': image.id,
                    'stage': stage,
                    'created_at': classification.created_at.isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error processing file {uploaded_file.name}: {str(e)}")
                continue
        
        logger.info(f"Upload with stage completed: {len(uploaded)} files, {len(classified)} classified as {stage} by {request.user.name}")
        
        return JsonResponse({
            'success': True,
            'upload_batch_id': upload_batch_id,
            'uploaded': uploaded,
            'stage': stage,
            'classified': classified
        }, status=201)
        
    except Exception as e:
        logger.error(f"Error in upload with stage: {str(e)}")
        return JsonResponse({
            'message': 'Internal server error'
        }, status=500)

# Create your views here.
