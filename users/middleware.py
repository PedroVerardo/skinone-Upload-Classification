"""
JWT Authentication Middleware
This middleware automatically checks for JWT tokens in requests and adds user info to the request
"""

import json
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from users.views import verify_jwt_token

logger = logging.getLogger(__name__)
User = get_user_model()


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to handle JWT authentication
    
    This middleware:
    1. Checks for Authorization header with Bearer token
    2. Verifies the JWT token
    3. Adds user object to request if token is valid
    4. Allows protected views to access request.user
    """
    
    def process_request(self, request):
        """Process incoming request to check for JWT token"""
        
        # Skip JWT check for certain paths
        skip_paths = [
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/auth/verify-email-password/',
            '/admin/',
            '/media/',
            '/static/',
        ]
        
        # Check if current path should skip JWT verification
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Get Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            # No token provided - set anonymous user
            request.user = None
            return None
        
        # Check if it's a Bearer token
        if not auth_header.startswith('Bearer '):
            request.user = None
            return None
        
        # Extract token
        token = auth_header.split(' ')[1] if len(auth_header.split(' ')) == 2 else ''
        
        if not token:
            request.user = None
            return None
        
        # Verify token
        user_id, error = verify_jwt_token(token)
        
        if error or not user_id:
            # Invalid token
            request.user = None
            return None
        
        # Get user from database
        try:
            user = User.objects.get(id=user_id, is_active=True)
            request.user = user
            return None
        except User.DoesNotExist:
            request.user = None
            return None


def jwt_required(view_func):
    """
    Decorator to require JWT authentication for a view
    Usage: @jwt_required
    """
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'user') or request.user is None:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def get_user_from_request(request):
    """
    Helper function to get user from request
    Returns None if no user is authenticated
    """
    return getattr(request, 'user', None)