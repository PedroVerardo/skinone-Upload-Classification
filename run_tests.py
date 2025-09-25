#!/usr/bin/env python3
"""
Test runner script for AUTH_USER_MODEL functionality
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skinrest.settings')
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Run specific tests for AUTH_USER_MODEL functionality
    test_labels = [
        'users.tests.UserModelTest',
        'images.tests.ImageModelTest',
        'images.tests.ImageUserIntegrationTest'
    ]
    
    print("🧪 Running AUTH_USER_MODEL functionality tests...")
    print("=" * 60)
    
    failures = test_runner.run_tests(test_labels)
    
    if failures:
        print(f"\n❌ {failures} test(s) failed!")
        sys.exit(1)
    else:
        print("\n✅ All AUTH_USER_MODEL tests passed!")
        sys.exit(0)
