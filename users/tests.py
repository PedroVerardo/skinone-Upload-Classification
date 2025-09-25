from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.conf import settings
import json

User = get_user_model()

class UserModelTest(TestCase):
    """Test cases for the custom User model"""
    
    def setUp(self):
        """Set up test data"""
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
    
    def test_auth_user_model_setting(self):
        """Test that AUTH_USER_MODEL is correctly configured"""
        self.assertEqual(settings.AUTH_USER_MODEL, 'users.User')
    
    def test_create_user_with_email(self):
        """Test creating a user with email"""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        self.assertEqual(user.email, self.user_data['email'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertEqual(admin_user.email, 'admin@example.com')
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
    
    def test_user_email_unique(self):
        """Test that email must be unique"""
        User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email=self.user_data['email'],
                password='anotherpass123'
            )
    
    def test_user_string_representation(self):
        """Test the string representation of user"""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        self.assertEqual(str(user), self.user_data['email'])
    
    def test_user_email_field_is_username_field(self):
        """Test that email is used as USERNAME_FIELD"""
        self.assertEqual(User.USERNAME_FIELD, 'email')
    
    def test_user_has_no_username_field(self):
        """Test that username field is None"""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        # Should not have username attribute or it should be None
        self.assertIsNone(getattr(user, 'username', None))
    
    def test_user_required_fields(self):
        """Test REQUIRED_FIELDS configuration"""
        self.assertEqual(User.REQUIRED_FIELDS, [])
    
    def test_get_user_model_returns_custom_user(self):
        """Test that get_user_model() returns our custom User model"""
        UserModel = get_user_model()
        self.assertEqual(UserModel, User)
        self.assertEqual(UserModel._meta.app_label, 'users')
        self.assertEqual(UserModel._meta.model_name, 'user')


class EmailValidationTest(TestCase):
    """Test cases for email validation in views"""
    
    def setUp(self):
        """Set up test client and user data"""
        from django.test import Client
        self.client = Client()
        self.valid_user = User.objects.create_user(
            email='valid@example.com',
            password='validpass123'
        )
    
    def test_validate_email_format_function(self):
        """Test the validate_email_format function directly"""
        from users.views import validate_email_format
        
        # Valid emails
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'first.last+tag@subdomain.example.org',
            'x@y.co'  # minimum valid length
        ]
        
        for email in valid_emails:
            is_valid, message = validate_email_format(email)
            self.assertTrue(is_valid, f"Email {email} should be valid: {message}")
    
    def test_validate_email_format_invalid_emails(self):
        """Test invalid email formats"""
        from users.views import validate_email_format
        
        invalid_emails = [
            '',  # empty
            'notanemail',  # no @
            '@example.com',  # no local part
            'user@',  # no domain
            'user@@example.com',  # double @
            'user@.com',  # domain starts with dot
            'user@com.',  # domain ends with dot
            'user@com',  # no dot in domain
            'user..name@example.com',  # consecutive dots
            'user@exam..ple.com',  # consecutive dots in domain
            'a@b',  # domain without dot
            'a' * 65 + '@example.com',  # local part too long
            'user@' + 'a' * 254 + '.com',  # domain too long
            'ab',  # too short overall
            'user@domain.c',  # TLD too short (less than 2 chars)
            None,  # None value
            123,  # not a string
        ]
        
        for email in invalid_emails:
            is_valid, message = validate_email_format(email)
            self.assertFalse(is_valid, f"Email {email} should be invalid but was considered valid")
    
    def test_email_validation_in_login_view(self):
        """Test email validation in the login API endpoint"""
        import json
        
        # Test with invalid email format
        response = self.client.post(
            '/users/verify-email-password/',
            data=json.dumps({
                'email': 'invalid-email-format',
                'password': 'somepassword'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Invalid email', data['error'])
    
    def test_email_validation_empty_email(self):
        """Test validation with empty email"""
        import json
        
        response = self.client.post(
            '/users/verify-email-password/',
            data=json.dumps({
                'email': '',
                'password': 'somepassword'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Email and password are required', data['error'])
    
    def test_valid_email_format_in_login(self):
        """Test successful login with valid email format"""
        import json
        
        response = self.client.post(
            '/users/verify-email-password/',
            data=json.dumps({
                'email': 'valid@example.com',
                'password': 'validpass123'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['user_id'], self.valid_user.id)
    
    def test_email_normalization(self):
        """Test that emails are normalized (lowercase, trimmed)"""
        import json
        
        # Create user with normalized email
        test_user = User.objects.create_user(
            email='normalize@example.com',
            password='testpass123'
        )
        
        # Test login with different case and whitespace
        response = self.client.post(
            '/users/verify-email-password/',
            data=json.dumps({
                'email': '  NORMALIZE@Example.COM  ',
                'password': 'testpass123'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['user_id'], test_user.id)


class PasswordValidationTest(TestCase):
    """Test cases for password validation"""
    
    def test_validate_password_strength_function(self):
        """Test the validate_password_strength function"""
        from users.views import validate_password_strength
        
        # Valid passwords
        valid_passwords = [
            'password123',  # has letter and digit
            'Test123456',   # mixed case with digit
            'mypassword1',  # lowercase with digit
            'PASSWORD2',    # uppercase with digit
            'complex1Pass', # mixed case with digit
        ]
        
        for password in valid_passwords:
            is_valid, message = validate_password_strength(password)
            self.assertTrue(is_valid, f"Password '{password}' should be valid: {message}")
    
    def test_validate_password_strength_invalid_passwords(self):
        """Test invalid passwords"""
        from users.views import validate_password_strength
        
        invalid_passwords = [
            '',              # empty
            'short',         # too short
            'onlyletters',   # no digits
            '12345678',      # no letters
            'a' * 129,       # too long
            None,            # None value
        ]
        
        for password in invalid_passwords:
            is_valid, message = validate_password_strength(password)
            self.assertFalse(is_valid, f"Password '{password}' should be invalid but was considered valid")


class GoogleSSOValidationTest(TestCase):
    """Test cases for Google SSO validation"""
    
    def setUp(self):
        """Set up test client"""
        from django.test import Client
        self.client = Client()
    
    def test_google_sso_missing_token(self):
        """Test Google SSO with missing token"""
        import json
        
        response = self.client.post(
            '/users/verify-google-sso/',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Google token is required', data['error'])
    
    def test_google_sso_invalid_json(self):
        """Test Google SSO with invalid JSON"""
        response = self.client.post(
            '/users/verify-google-sso/',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Invalid JSON data', data['error'])
    
    def test_google_sso_client_id_not_configured(self):
        """Test Google SSO when client ID is not configured"""
        import json
        from unittest.mock import patch
        
        # Mock settings to return None for GOOGLE_CLIENT_ID
        with patch('users.views.getattr') as mock_getattr:
            mock_getattr.return_value = None
            
            response = self.client.post(
                '/users/verify-google-sso/',
                data=json.dumps({'token': 'fake-token'}),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertFalse(data['success'])
            self.assertIn('Google Client ID not configured', data['error'])


class ViewsIntegrationTest(TestCase):
    """Integration tests for all authentication views"""
    
    def setUp(self):
        """Set up test data"""
        from django.test import Client
        self.client = Client()
        self.user_data = {
            'email': 'integration@example.com',
            'password': 'integration123'
        }
        self.user = User.objects.create_user(**self.user_data)
    
    def test_complete_email_password_flow(self):
        """Test complete email/password authentication flow"""
        import json
        
        # Test successful authentication
        response = self.client.post(
            '/users/verify-email-password/',
            data=json.dumps(self.user_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['user_id'], self.user.id)
        self.assertIn('verification successful', data['message'])
        
        # Test failed authentication
        response = self.client.post(
            '/users/verify-email-password/',
            data=json.dumps({
                'email': self.user_data['email'],
                'password': 'wrongpassword'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)  # Django returns 200 for failed auth
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('credential invalid', data['message'])
    
    def test_error_handling_malformed_requests(self):
        """Test error handling for malformed requests"""
        
        # Test missing content type
        response = self.client.post('/users/verify-email-password/', data='{}')
        self.assertEqual(response.status_code, 400)
        
        # Test invalid JSON
        response = self.client.post(
            '/users/verify-email-password/',
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Invalid JSON', data['error'])
