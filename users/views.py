from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import check_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from google.oauth2 import id_token
from google.auth.transport import requests
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
    """
    Validate email format using multiple validation methods
    Returns tuple: (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"
    
    if not isinstance(email, str):
        return False, "Email must be a string"
    
    # First, normalize the email (strip whitespace and lowercase)
    email = email.strip().lower()
    
    # Basic format validation using Django's validator
    try:
        validate_email(email)
    except ValidationError:
        return False, "Invalid email format"
    
    # Use advanced email validation if available
    if EMAIL_VALIDATOR_AVAILABLE:
        try:
            # This will check DNS records and other advanced validations
            validated_email = validate_email_advanced(
                email,
                check_deliverability=False  # Set to True for DNS checking
            )
            email = validated_email.email
        except EmailNotValidError as e:
            return False, f"Invalid email: {str(e)}"
    
    # Additional custom validation
    # Email is already normalized above
    
    # Check for common email format issues
    if len(email) < 5:  # Minimum realistic email length (a@b.c)
        return False, "Email too short"
    
    if len(email) > 254:  # RFC 5321 limit
        return False, "Email too long"
    
    # Check for multiple @ symbols
    if email.count('@') != 1:
        return False, "Email must contain exactly one @ symbol"
    
    local_part, domain = email.split('@')
    
    # Validate local part (before @)
    if len(local_part) < 1 or len(local_part) > 64:
        return False, "Invalid email local part length"
    
    # Validate domain part
    if len(domain) < 1 or len(domain) > 253:
        return False, "Invalid email domain length"
    
    # Check for valid domain format (at least one dot)
    if '.' not in domain:
        return False, "Domain must contain at least one dot"
    
    # Check for consecutive dots
    if '..' in email:
        return False, "Email cannot contain consecutive dots"
    
    # Check if starts or ends with dot
    if email.startswith('.') or email.endswith('.'):
        return False, "Email cannot start or end with a dot"
    
    # Additional regex validation for stricter checking
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    if not email_pattern.match(email):
        return False, "Email format does not match required pattern"
    
    return True, "Valid email format"

def validate_password_strength(password):
    """
    Validate password strength
    Returns tuple: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password too long (max 128 characters)"
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    # Check for at least one letter
    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least one letter"
    
    return True, "Valid password strength"

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