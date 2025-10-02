import json
import logging
from functools import wraps
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from .models import Classification
from images.models import Image

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
                'error': error
            }, status=401)
        
        # Add user to request
        try:
            request.user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=401)
        
        return f(request, *args, **kwargs)
    return decorated_function

@csrf_exempt
@require_http_methods(["POST", "GET"])
@jwt_required
def create_classification(request):
    """
    POST /classifications/
    Auth required
    Request: { image_id: string, stage: "estagio1"|"estagio2"|"estagio3"|"estagio4"|"nao_classificavel"|"dtpi", observations?: string }
    Response: 201 Created, { id, image_id, stage, created_at }
    """
    if request.method == 'GET':
        return list_classifications(request)
    
    try:
        data = json.loads(request.body)
        image_id = data.get('image_id')
        stage = data.get('stage')
        observations = data.get('observations', '')
        
        if not image_id or not stage:
            return JsonResponse({
                'message': 'Validation failed',
                'errors': {
                    'image_id': ['Image ID is required'] if not image_id else [],
                    'stage': ['Stage is required'] if not stage else []
                }
            }, status=400)
        
        # Validate stage choice
        valid_choices = [choice[0] for choice in Classification.CLASSIFICATION_CHOICES]
        if stage not in valid_choices:
            return JsonResponse({
                'message': 'Validation failed',
                'errors': {
                    'stage': [f'Invalid stage. Valid choices: {valid_choices}']
                }
            }, status=400)
        
        # Check if image exists
        try:
            image = Image.objects.get(id=image_id)
        except Image.DoesNotExist:
            return JsonResponse({
                'message': 'Image not found'
            }, status=404)
        
        # Create classification
        classification_obj = Classification.objects.create(
            user=request.user,
            image=image,
            stage=stage,
            observations=observations
        )
        
        logger.info(f"Classification created: {classification_obj.id} by {request.user.name}")
        
        return JsonResponse({
            'id': classification_obj.id,
            'image_id': str(classification_obj.image.id),
            'stage': classification_obj.stage,
            'created_at': classification_obj.created_at.isoformat()
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error creating classification: {str(e)}")
        return JsonResponse({
            'message': 'Internal server error'
        }, status=500)

@require_http_methods(["GET"])
@jwt_required  
def list_classifications(request):
    """
    GET /classifications/?image_id=<id>
    Auth required
    Response: 200 OK, [ { id, image_id, stage, created_at } ]
    """
    try:
        classifications = Classification.objects.all().order_by('-created_at')
        
        # Filter by image_id if provided
        image_id = request.GET.get('image_id')
        if image_id:
            classifications = classifications.filter(image_id=image_id)
        
        classifications_data = []
        for classification in classifications:
            classifications_data.append({
                'id': classification.id,
                'image_id': str(classification.image.id),
                'stage': classification.stage,
                'created_at': classification.created_at.isoformat()
            })
        
        return JsonResponse(classifications_data, safe=False, status=200)
        
    except Exception as e:
        logger.error(f"Error listing classifications: {str(e)}")
        return JsonResponse({
            'message': 'Internal server error'
        }, status=500)

@require_http_methods(["GET"])
@jwt_required
def get_classification(request, classification_id):
    """Get a specific classification"""
    try:
        classification = Classification.objects.get(id=classification_id)
        
        return JsonResponse({
            'success': True,
            'classification': {
                'id': classification.id,
                'image_id': classification.image.id,
                'classification': classification.classification,
                'classification_display': classification.get_classification_display(),
                'comment': classification.comment,
                'created_at': classification.created_at.isoformat(),
                'updated_at': classification.updated_at.isoformat(),
                'user_email': classification.user.email,
                'image_info': {
                    'original_filename': classification.image.original_filename,
                    'file_path': classification.image.file_path
                }
            }
        })
        
    except Classification.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Classification not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error getting classification: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
@jwt_required
def update_classification(request, classification_id):
    """Update an existing classification"""
    try:
        data = json.loads(request.body)
        classification = data.get('classification')
        comment = data.get('comment')
        
        try:
            classification_obj = Classification.objects.get(id=classification_id)
        except Classification.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Classification not found'
            }, status=404)
        
        # Check if user owns this classification or is admin
        if classification_obj.user != request.user and not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'error': 'Permission denied'
            }, status=403)
        
        # Update fields if provided
        if classification:
            valid_choices = [choice[0] for choice in Classification.CLASSIFICATION_CHOICES]
            if classification not in valid_choices:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid classification. Valid choices: {valid_choices}'
                }, status=400)
            classification_obj.classification = classification
        
        if comment is not None:
            classification_obj.comment = comment
        
        classification_obj.save()
        
        logger.info(f"Classification updated: {classification_obj.id} by {request.user.email}")
        
        return JsonResponse({
            'success': True,
            'message': 'Classification updated successfully',
            'classification': {
                'id': classification_obj.id,
                'image_id': classification_obj.image.id,
                'classification': classification_obj.classification,
                'comment': classification_obj.comment,
                'updated_at': classification_obj.updated_at.isoformat(),
                'user_email': classification_obj.user.email
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error updating classification: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
@jwt_required
def delete_classification(request, classification_id):
    """Delete a classification"""
    try:
        try:
            classification = Classification.objects.get(id=classification_id)
        except Classification.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Classification not found'
            }, status=404)
        
        # Check if user owns this classification or is admin
        if classification.user != request.user and not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'error': 'Permission denied'
            }, status=403)
        
        classification.delete()
        
        logger.info(f"Classification deleted: {classification_id} by {request.user.email}")
        
        return JsonResponse({
            'success': True,
            'message': 'Classification deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting classification: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@require_http_methods(["GET"])
@jwt_required
def list_classifications(request):
    """List classifications with optional filtering"""
    try:
        classifications = Classification.objects.all().order_by('-created_at')
        
        # Filter by image_id
        image_id = request.GET.get('image_id')
        if image_id:
            classifications = classifications.filter(image_id=image_id)
        
        # Filter by classification type
        classification_type = request.GET.get('classification')
        if classification_type:
            classifications = classifications.filter(classification=classification_type)
        
        # Filter by user (only show own classifications unless admin)
        if not request.user.is_staff:
            user_id = request.GET.get('user_id')
            if user_id:
                classifications = classifications.filter(user_id=user_id)
            else:
                classifications = classifications.filter(user=request.user)
        else:
            user_id = request.GET.get('user_id')
            if user_id:
                classifications = classifications.filter(user_id=user_id)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))
        
        paginator = Paginator(classifications, limit)
        page_obj = paginator.get_page(page)
        
        classifications_data = []
        for classification in page_obj:
            classifications_data.append({
                'id': classification.id,
                'image_id': classification.image.id,
                'classification': classification.classification,
                'classification_display': classification.get_classification_display(),
                'comment': classification.comment,
                'created_at': classification.created_at.isoformat(),
                'updated_at': classification.updated_at.isoformat(),
                'user_email': classification.user.email,
                'image_info': {
                    'original_filename': classification.image.original_filename,
                    'file_path': classification.image.file_path
                }
            })
        
        return JsonResponse({
            'success': True,
            'classifications': classifications_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing classifications: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@require_http_methods(["GET"])
def get_classification_choices(request):
    """Get available classification choices"""
    return JsonResponse({
        'success': True,
        'choices': [
            {'value': choice[0], 'display': choice[1]} 
            for choice in Classification.CLASSIFICATION_CHOICES
        ]
    })

# Create your views here.
