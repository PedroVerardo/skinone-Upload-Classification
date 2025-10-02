import json
import jwt
import os
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

User = get_user_model()

class UserRoutesTestCase(TestCase):
    """Test cases for user authentication routes"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.register_url = reverse('users:register_user')
        self.login_url = reverse('users:login_user')
        self.verify_token_url = reverse('users:verify_token')
        
        # Test user data
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User',
            'coren': '123456',
        }
        
        # Create a test user for login tests
        self.existing_user = User.objects.create_user(
            email='existing@example.com',
            password='existingpass123',
            coren='654321',
        )
    
    def test_user_registration_success(self):
        """Test successful user registration"""
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.user_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        print(response_data)
        
        self.assertIn('name', response_data)

        self.assertEqual(response_data['email'], self.user_data['email'])
        self.assertEqual(response_data['name'], self.user_data['name'])

        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())
    
    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        duplicate_data = self.user_data.copy()
        duplicate_data['email'] = self.existing_user.email
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(duplicate_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertIn('errors', response_data)
    
    def test_user_registration_missing_fields(self):
        """Test registration with missing required fields"""
        incomplete_data = {
            'email': 'incomplete@example.com',
            # Missing password, name
        }
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertIn('errors', response_data)
    
    def test_user_registration_invalid_email(self):
        """Test registration with invalid email format"""
        invalid_data = self.user_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertIn('errors', response_data)
    
    def test_user_login_success(self):
        """Test successful user login"""
        login_data = {
            'email': self.existing_user.email,
            'password': 'existingpass123'
        }
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Check response structure
        self.assertIn('user', response_data)
        
        # Check user data
        self.assertEqual(response_data['user']['email'], self.existing_user.email)
        self.assertEqual(response_data['user']['name'], self.existing_user.name)

        # Check token is valid JWT
        token = response_data['token']
        try:
            payload = jwt.decode(
                token,
                getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY),
                algorithms=['HS256']
            )
            self.assertEqual(payload['user_id'], self.existing_user.id)
        except jwt.InvalidTokenError:
            self.fail("Invalid JWT token returned")
    
    def test_user_login_wrong_password(self):
        """Test login with wrong password"""
        login_data = {
            'email': self.existing_user.email,
            'password': 'wrongpassword'
        }
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        response_data = response.json()
        self.assertIn('message', response_data)
    
    def test_user_login_nonexistent_email(self):
        """Test login with non-existent email"""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'anypassword'
        }
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        response_data = response.json()
        self.assertIn('message', response_data)
    
    def test_user_login_missing_fields(self):
        """Test login with missing fields"""
        login_data = {
            'email': self.existing_user.email,
            # Missing password
        }
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertIn('errors', response_data)
    
    def test_verify_token_valid(self):
        """Test token verification with valid token"""
        # First login to get a token
        login_data = {
            'email': self.existing_user.email,
            'password': 'existingpass123'
        }
        
        login_response = self.client.post(
            self.login_url,
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        token = login_response.json()['token']
        
        # Now verify the token
        response = self.client.get(
            self.verify_token_url,
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('valid', response_data)
        self.assertTrue(response_data['valid'])
        self.assertIn('name', response_data)

    def test_verify_token_invalid(self):
        """Test token verification with invalid token"""
        response = self.client.get(
            self.verify_token_url,
            HTTP_AUTHORIZATION='Bearer invalid-token'
        )
        
        self.assertEqual(response.status_code, 405)
        response_data = response.json()
        print(response_data)
        self.assertIn('message', response_data)
    
    def test_verify_token_missing(self):
        """Test token verification without token"""
        response = self.client.get(self.verify_token_url)
        
        self.assertEqual(response.status_code, 405)
        response_data = response.json()
        print(response_data)
        self.assertIn('message', response_data)
    
    def test_method_not_allowed(self):
        """Test that wrong HTTP methods return 405"""
        # GET on register endpoint
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 405)
        
        # GET on login endpoint
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 405)
        
        # POST on verify token endpoint
        response = self.client.post(self.verify_token_url)
        self.assertEqual(response.status_code, 400)