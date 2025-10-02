import json
import jwt
import os
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from images.models import Image
from classification.models import Classification

User = get_user_model()

class AdminRoutesTestCase(TestCase):
    """Test cases for admin routes"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # URLs
        self.admin_metrics_url = reverse('admin_metrics')
        self.admin_users_url = reverse('admin_users')
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            name='Admin User',
            coren='ADMIN123',
            specialty='Administration',
            institution='Test Hospital'
        )
        self.admin_user.is_staff = True
        self.admin_user.save()
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='regularpass123',
            name='Regular User',
            coren='REG456',
            specialty='Dermatologia',
            institution='Test Hospital'
        )
        
        # Get admin token
        admin_login_data = {
            'email': 'admin@example.com',
            'password': 'adminpass123'
        }
        
        admin_login_response = self.client.post(
            reverse('users:login_user'),
            data=json.dumps(admin_login_data),
            content_type='application/json'
        )
        
        self.admin_token = admin_login_response.json()['token']
        self.admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Get regular user token
        regular_login_data = {
            'email': 'regular@example.com',
            'password': 'regularpass123'
        }
        
        regular_login_response = self.client.post(
            reverse('users:login_user'),
            data=json.dumps(regular_login_data),
            content_type='application/json'
        )
        
        self.regular_token = regular_login_response.json()['token']
        self.regular_headers = {'Authorization': f'Bearer {self.regular_token}'}
        
        # Create test data for metrics
        self.test_image = Image.objects.create(
            file_path='test/path/test_image.jpg',
            file_hash='test_hash_123',
            original_filename='test_image.jpg',
            description='Test image for metrics',
            file_size=1024,
            uploaded_by=self.regular_user
        )
        
        self.test_classification = Classification.objects.create(
            user=self.regular_user,
            image=self.test_image,
            stage='stage1',
            observations='Test classification for metrics'
        )
    
    def test_admin_metrics_success(self):
        """Test successful admin metrics retrieval"""
        response = self.client.get(self.admin_metrics_url, **self.admin_headers)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Check required metrics fields
        self.assertIn('total_users', response_data)
        self.assertIn('total_images', response_data)
        self.assertIn('total_classifications', response_data)
        self.assertIn('classifications_by_stage', response_data)
        self.assertIn('users_by_specialty', response_data)
        self.assertIn('generated_at', response_data)
        
        # Check that metrics are numbers
        self.assertIsInstance(response_data['total_users'], int)
        self.assertIsInstance(response_data['total_images'], int)
        self.assertIsInstance(response_data['total_classifications'], int)
        
        # Check that we have at least our test data
        self.assertGreaterEqual(response_data['total_users'], 2)  # admin + regular user
        self.assertGreaterEqual(response_data['total_images'], 1)
        self.assertGreaterEqual(response_data['total_classifications'], 1)
        
        # Check structure of nested data
        self.assertIsInstance(response_data['classifications_by_stage'], dict)
        self.assertIsInstance(response_data['users_by_specialty'], dict)
    
    def test_admin_metrics_unauthorized_regular_user(self):
        """Test admin metrics access with regular user token"""
        response = self.client.get(self.admin_metrics_url, **self.regular_headers)
        
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertIn('administrador', response_data['message'].lower())
    
    def test_admin_metrics_unauthorized_no_token(self):
        """Test admin metrics access without token"""
        response = self.client.get(self.admin_metrics_url)
        
        self.assertEqual(response.status_code, 401)
        response_data = response.json()
        self.assertIn('message', response_data)
    
    def test_admin_metrics_invalid_token(self):
        """Test admin metrics access with invalid token"""
        invalid_headers = {'Authorization': 'Bearer invalid-token'}
        response = self.client.get(self.admin_metrics_url, **invalid_headers)
        
        self.assertEqual(response.status_code, 401)
        response_data = response.json()
        self.assertIn('message', response_data)
    
    def test_admin_users_success(self):
        """Test successful admin users list retrieval"""
        response = self.client.get(self.admin_users_url, **self.admin_headers)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Check response structure
        self.assertIn('users', response_data)
        self.assertIn('total_count', response_data)
        
        # Check that we have our test users
        users = response_data['users']
        self.assertIsInstance(users, list)
        self.assertGreaterEqual(len(users), 2)
        self.assertEqual(response_data['total_count'], len(users))
        
        # Check user data structure
        for user_data in users:
            self.assertIn('id', user_data)
            self.assertIn('email', user_data)
            self.assertIn('name', user_data)
            self.assertIn('coren', user_data)
            self.assertIn('specialty', user_data)
            self.assertIn('institution', user_data)
            self.assertIn('is_staff', user_data)
            self.assertIn('is_active', user_data)
            self.assertIn('date_joined', user_data)
            self.assertIn('last_login', user_data)
        
        # Check that admin user is in the list
        admin_in_list = any(user['email'] == self.admin_user.email for user in users)
        self.assertTrue(admin_in_list)
        
        # Check that regular user is in the list
        regular_in_list = any(user['email'] == self.regular_user.email for user in users)
        self.assertTrue(regular_in_list)
    
    def test_admin_users_unauthorized_regular_user(self):
        """Test admin users access with regular user token"""
        response = self.client.get(self.admin_users_url, **self.regular_headers)
        
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertIn('administrador', response_data['message'].lower())
    
    def test_admin_users_unauthorized_no_token(self):
        """Test admin users access without token"""
        response = self.client.get(self.admin_users_url)
        
        self.assertEqual(response.status_code, 401)
        response_data = response.json()
        self.assertIn('message', response_data)
    
    def test_admin_users_invalid_token(self):
        """Test admin users access with invalid token"""
        invalid_headers = {'Authorization': 'Bearer invalid-token'}
        response = self.client.get(self.admin_users_url, **invalid_headers)
        
        self.assertEqual(response.status_code, 401)
        response_data = response.json()
        self.assertIn('message', response_data)
    
    def test_admin_endpoints_method_not_allowed(self):
        """Test that admin endpoints only accept GET method"""
        # Test POST on metrics
        response = self.client.post(self.admin_metrics_url, **self.admin_headers)
        self.assertEqual(response.status_code, 405)
        
        # Test PUT on metrics
        response = self.client.put(self.admin_metrics_url, **self.admin_headers)
        self.assertEqual(response.status_code, 405)
        
        # Test DELETE on metrics
        response = self.client.delete(self.admin_metrics_url, **self.admin_headers)
        self.assertEqual(response.status_code, 405)
        
        # Test POST on users
        response = self.client.post(self.admin_users_url, **self.admin_headers)
        self.assertEqual(response.status_code, 405)
        
        # Test PUT on users
        response = self.client.put(self.admin_users_url, **self.admin_headers)
        self.assertEqual(response.status_code, 405)
        
        # Test DELETE on users
        response = self.client.delete(self.admin_users_url, **self.admin_headers)
        self.assertEqual(response.status_code, 405)
    
    def test_admin_metrics_data_accuracy(self):
        """Test that admin metrics return accurate counts"""
        # Create additional test data
        another_user = User.objects.create_user(
            email='another@example.com',
            password='anotherpass123',
            name='Another User',
            coren='ANOTHER789',
            specialty='Cardiologia',
            institution='Another Hospital'
        )
        
        another_image = Image.objects.create(
            file_path='test/path/another_image.jpg',
            file_hash='another_hash_456',
            original_filename='another_image.jpg',
            description='Another test image',
            file_size=2048,
            uploaded_by=another_user
        )
        
        Classification.objects.create(
            user=another_user,
            image=another_image,
            stage='stage2',
            observations='Another classification'
        )
        
        response = self.client.get(self.admin_metrics_url, **self.admin_headers)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Check updated counts
        self.assertGreaterEqual(response_data['total_users'], 3)
        self.assertGreaterEqual(response_data['total_images'], 2)
        self.assertGreaterEqual(response_data['total_classifications'], 2)
        
        # Check specialty breakdown
        self.assertIn('Dermatologia', response_data['users_by_specialty'])
        self.assertIn('Cardiologia', response_data['users_by_specialty'])
        
        # Check stage breakdown
        classifications_by_stage = response_data['classifications_by_stage']
        self.assertIn('stage1', classifications_by_stage)
        self.assertIn('stage2', classifications_by_stage)