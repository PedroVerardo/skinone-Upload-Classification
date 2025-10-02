from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import check_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import jwt
import json
import logging
import re

try:
    from email_validator import validate_email as validate_email_advanced, EmailNotValidError
    EMAIL_VALIDATOR_AVAILABLE = True
except ImportError:
    EMAIL_VALIDATOR_AVAILABLE = False

from .models import User

logger = logging.getLogger(__name__)

def validate_email_format(email):
    if not email:
        return False, "Email is required"
    
    if not isinstance(email, str):
        return False, "Email must be a string"
    
    email = email.strip().lower()

    try:
        validate_email(email)
    except ValidationError:
        return False, "Invalid email format"
    
    if EMAIL_VALIDATOR_AVAILABLE:
        try:
            validated_email = validate_email_advanced(
                email,
                check_deliverability=False
            )
            email = validated_email.email
        except EmailNotValidError as e:
            return False, f"Invalid email: {str(e)}"
    
    if len(email) < 5:
        return False, "Email too short"
    
    if len(email) > 254:
        return False, "Email too long"

    if email.count('@') != 1:
        return False, "Email must contain exactly one @ symbol"
    
    local_part, domain = email.split('@')

    if len(local_part) < 1 or len(local_part) > 64:
        return False, "Invalid email local part length"

    if len(domain) < 1 or len(domain) > 253:
        return False, "Invalid email domain length"

    if '.' not in domain:
        return False, "Domain must contain at least one dot"
    
    if '..' in email:
        return False, "Email cannot contain consecutive dots"
    
    if email.startswith('.') or email.endswith('.'):
        return False, "Email cannot start or end with a dot"
    
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    if not email_pattern.match(email):
        return False, "Email format does not match required pattern"
    
    return True, "Valid email format"

def validate_password_strength(password):
    if not password:
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password too long (max 128 characters)"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    

    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least one letter"
    
    return True, "Valid password strength"

def generate_jwt_tokens(user):
    """
    Generate access and refresh JWT tokens for a user
    """
    import time
    current_time = int(time.time())
    
    # Token payload
    payload = {
        'user_id': user.id,
        'email': user.email,
        'exp': current_time + (24 * 60 * 60),  # Token expires in 24 hours
        'iat': current_time,  # Issued at
        'type': 'access'
    }
    
    # Refresh token payload (longer expiration)
    refresh_payload = {
        'user_id': user.id,
        'exp': current_time + (7 * 24 * 60 * 60),  # Refresh token expires in 7 days
        'iat': current_time,
        'type': 'refresh'
    }
    
    # Get secret key from settings (you should set this in your settings.py)
    secret_key = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
    
    # Generate tokens
    access_token = jwt.encode(payload, secret_key, algorithm='HS256')
    refresh_token = jwt.encode(refresh_payload, secret_key, algorithm='HS256')
    
    return access_token, refresh_token

def verify_jwt_token(token):
    """
    Verify and decode a JWT token
    Returns user_id if valid, None if invalid
    """
    try:
        secret_key = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        
        # Check if token is expired (JWT library handles this automatically, but we can double check)
        import time
        exp_timestamp = payload.get('exp')
        if exp_timestamp and exp_timestamp < time.time():
            return None, "Token expired"
        
        return payload.get('user_id'), None
        
    except jwt.ExpiredSignatureError:
        return None, "Token expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"
    except Exception as e:
        logger.error(f"JWT verification error: {str(e)}")
        return None, "Token verification failed"

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
        email_valid, email_error = validate_email_format(email)
        if not email_valid:
            return JsonResponse({
                'success': False,
                'error': f'Invalid email: {email_error}'
            }, status=400)
        email = email.strip().lower()
        
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


@require_http_methods(["GET"])
def get_all_users(request):
    try:
        users = User.objects.all().values('id', 'email', 'is_active', 'is_staff', 'date_joined')
        users_list = list(users)
        return JsonResponse({
            'success': True,
            'users': users_list
        })
    except Exception as e:
        logger.error(f"Unexpected error in fetching all users: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def register_user(request):
    """
    Register a new user
    Expected JSON: { name, email, password, coren, specialty, institution }
    Response: 201 Created, { id, name, email }
    """
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        coren = data.get('coren', '').strip()
        specialty = data.get('specialty', '').strip()
        
        # Validate required fields
        if not name or not email or not password:
            errors = {}
            if not name:
                errors['name'] = ['Name is required']
            if not email:
                errors['email'] = ['Email is required']
            if not password:
                errors['password'] = ['Password is required']
            if not specialty:
                errors['specialty'] = ['Specialty is required']
            
            return JsonResponse({
                'message': 'Validation failed',
                'errors': errors
            }, status=400)
        # Validate email format
        email_valid, email_error = validate_email_format(email)
        if not email_valid:
            return JsonResponse({
                'message': 'Validation failed',
                'errors': {
                    'email': [email_error]
                }
            }, status=400)
        
        # Validate password strength
        password_valid, password_error = validate_password_strength(password)
        if not password_valid:
            return JsonResponse({
                'message': 'Validation failed',
                'errors': {
                    'password': [password_error]
                }
            }, status=400)
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'message': 'Validation failed',
                'errors': {
                    'email': ['User with this email already exists']
                }
            }, status=400)
        
        # Create new user
        user = User.objects.create_user(
            email=email,
            password=password,
            name=name,
            coren=coren if coren else None,
        )
        
        logger.info(f"New user registered: {name} ({email})")
        
        return JsonResponse({
            'id': user.id,
            'name': user.name,
            'email': user.email
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in user registration: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def login_user(request):
    """
    Login user and return JWT token
    Expected JSON: { email, password }
    Response: 200 OK, { token, user: { id, name, email } }
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return JsonResponse({
                'message': 'Validation failed',
                'errors': {
                    'email': ['Email is required'] if not email else [],
                    'password': ['Password is required'] if not password else []
                }
            }, status=400)
        
        # Check if user exists and verify password
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({
                'message': 'Invalid credentials'
            }, status=401)
        
        # Check if user is active
        if not user.is_active:
            return JsonResponse({
                'message': 'User account is disabled'
            }, status=401)
        
        # Verify password
        if not user.check_password(password):
            return JsonResponse({
                'message': 'Invalid credentials'
            }, status=401)
        
        # Generate JWT token (only access token as per spec)
        access_token, _ = generate_jwt_tokens(user)
        
        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        logger.info(f"User logged in: {user.name} ({email})")
        
        return JsonResponse({
            'token': access_token,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email
            }
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in user login: {e}")
        return JsonResponse({
            'message': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def verify_token(request):
    """
    Verify if a JWT token is valid
    Expected JSON: {"token": "jwt_token_here"}
    """
    try:
        data = json.loads(request.body)
        token = data.get('token', '')
        
        if not token:
            return JsonResponse({
                'message': 'Token is required'
            }, status=400)
        
        # Verify token
        user_id, error = verify_jwt_token(token)
        
        if error:
            return JsonResponse({
                'message': error
            }, status=401)
        
        # Get user info
        try:
            user = User.objects.get(id=user_id)
            return JsonResponse({
                'message': 'Token is valid',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            }, status=200)
        except User.DoesNotExist:
            return JsonResponse({
                'message': 'User not found'
            }, status=401)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in token verification: {e}")
        return JsonResponse({
            'message': 'Internal server error'
        }, status=500)

@require_http_methods(["GET"])
def auth_page(request):
    """Render the JWT authentication test page"""
    return render(request, 'users/auth.html')