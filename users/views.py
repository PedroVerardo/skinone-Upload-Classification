from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import check_password
from google.oauth2 import id_token
from google.auth.transport import requests
import json
import logging

from .models import User

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def verify_email_password(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JsonResponse({
                'success': False,
                'error': 'Email and password are required'
            }, status=400)
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            return JsonResponse({
                'success': True,
                'message': 'Email and password verification successful',
                'user_id': user.id
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'user credential invalid'
            })
                
                
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        logger.error(f"Unexpected error in email/password verification: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)
