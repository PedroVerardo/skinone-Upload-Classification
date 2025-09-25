from django.test import TestCase, Client
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

User = get_user_model()

class AuthenticationTest(TestCase):
    """Test authentication functionality with custom User model"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user_data = {
            'email': 'auth_test@example.com',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)
    
    def test_authentication_with_email(self):
        """Test that authentication works with email instead of username"""
        # Test successful authentication
        authenticated_user = authenticate(
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        self.assertIsNotNone(authenticated_user)
        self.assertEqual(authenticated_user, self.user)
        
        # Test failed authentication with wrong password
        failed_auth = authenticate(
            email=self.user_data['email'],
            password='wrongpassword'
        )
        self.assertIsNone(failed_auth)
        
        # Test failed authentication with wrong email
        failed_auth_email = authenticate(
            email='wrong@example.com',
            password=self.user_data['password']
        )
        self.assertIsNone(failed_auth_email)
    
    def test_login_logout_functionality(self):
        """Test login and logout with custom user model"""
        # Test login
        login_successful = self.client.login(
            username=self.user_data['email'],  # Django uses 'username' parameter even for email
            password=self.user_data['password']
        )
        self.assertTrue(login_successful)
        
        # Verify user is logged in
        response = self.client.get('/')  # Assuming you have a root URL
        if hasattr(response, 'wsgi_request'):
            self.assertTrue(response.wsgi_request.user.is_authenticated)
        
        # Test logout
        self.client.logout()
    
    def test_user_permissions_and_groups(self):
        """Test that user permissions and groups work with custom model"""
        from django.contrib.auth.models import Permission, Group
        from django.contrib.contenttypes.models import ContentType
        
        # Create a permission
        content_type = ContentType.objects.get_for_model(User)
        permission = Permission.objects.create(
            codename='can_test',
            name='Can Test',
            content_type=content_type,
        )
        
        # Create a group
        group = Group.objects.create(name='Test Group')
        group.permissions.add(permission)
        
        # Add user to group
        self.user.groups.add(group)
        
        # Test user has permission
        self.assertTrue(self.user.has_perm('users.can_test'))
        
        # Test user is in group
        self.assertIn(group, self.user.groups.all())


class CustomUserManagerTest(TestCase):
    """Test the custom user manager functionality"""
    
    def test_create_user_method(self):
        """Test the create_user method"""
        user = User.objects.create_user(
            email='manager_test@example.com',
            password='testpass123'
        )
        
        self.assertEqual(user.email, 'manager_test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_superuser_method(self):
        """Test the create_superuser method"""
        superuser = User.objects.create_superuser(
            email='super@example.com',
            password='superpass123'
        )
        
        self.assertEqual(superuser.email, 'super@example.com')
        self.assertTrue(superuser.check_password('superpass123'))
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
    
    def test_create_user_without_email_fails(self):
        """Test that creating user without email raises error"""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='testpass123')
        
        with self.assertRaises(ValueError):
            User.objects.create_user(email=None, password='testpass123')


class DatabaseConstraintsTest(TestCase):
    """Test database constraints work correctly"""
    
    def test_email_unique_constraint(self):
        """Test that email uniqueness is enforced at database level"""
        from django.db import IntegrityError
        
        # Create first user
        User.objects.create_user(
            email='unique@example.com',
            password='pass1'
        )
        
        # Try to create second user with same email
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email='unique@example.com',
                password='pass2'
            )
    
    def test_email_case_sensitivity(self):
        """Test email case sensitivity behavior"""
        # Create user with lowercase email
        user1 = User.objects.create_user(
            email='case@example.com',
            password='pass1'
        )
        
        # Django's default behavior - emails are case sensitive in database
        # You might want to override this in your model's clean() method
        user2 = User.objects.create_user(
            email='CASE@EXAMPLE.COM',
            password='pass2'
        )
        
        self.assertNotEqual(user1.email, user2.email)
        self.assertEqual(User.objects.filter(email__icontains='case@example.com').count(), 2)


class ModelMetaTest(TestCase):
    """Test model meta configuration"""
    
    def test_user_model_meta(self):
        """Test User model meta configuration"""
        meta = User._meta
        
        # Test app label
        self.assertEqual(meta.app_label, 'users')
        
        # Test model name
        self.assertEqual(meta.model_name, 'user')
        
        # Test verbose names (if you add them later)
        # self.assertEqual(meta.verbose_name, 'User')
        # self.assertEqual(meta.verbose_name_plural, 'Users')
    
    def test_image_model_meta(self):
        """Test Image model meta configuration"""
        from images.models import Image
        
        meta = Image._meta
        
        # Test app label
        self.assertEqual(meta.app_label, 'images')
        
        # Test model name
        self.assertEqual(meta.model_name, 'image')
