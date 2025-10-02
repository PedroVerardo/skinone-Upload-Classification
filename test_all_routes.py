#!/usr/bin/env python3
"""
Comprehensive Route Test Runner
Runs all route tests for the skinone-Upload-Classification project
"""
import os
import sys
import django
from django.test.utils import get_runner
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skinrest.settings')
django.setup()

class RouteTestRunner:
    """Custom test runner for all route tests"""
    
    def __init__(self):
        self.test_modules = [
            'users.test_routes',
            'users.test_admin_routes', 
            'images.test_routes',
            'classification.test_routes'
        ]
    
    def run_tests(self):
        """Run all route tests"""
        print("=" * 60)
        print("Running Comprehensive Route Tests")
        print("=" * 60)
        
        # Get Django test runner
        TestRunner = get_runner(settings)
        test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)
        
        # Run tests for each module
        failures = test_runner.run_tests(self.test_modules)
        
        print("=" * 60)
        if failures:
            print(f"FAILED: {failures} test(s) failed")
            return False
        else:
            print("SUCCESS: All route tests passed!")
            return True
    
    def run_individual_module(self, module_name):
        """Run tests for a specific module"""
        if module_name not in self.test_modules:
            print(f"Error: Module '{module_name}' not found in test modules")
            print(f"Available modules: {', '.join(self.test_modules)}")
            return False
        
        print(f"Running tests for module: {module_name}")
        print("-" * 40)
        
        TestRunner = get_runner(settings)
        test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)
        
        failures = test_runner.run_tests([module_name])
        
        if failures:
            print(f"FAILED: {failures} test(s) failed in {module_name}")
            return False
        else:
            print(f"SUCCESS: All tests passed in {module_name}")
            return True
    
    def list_test_modules(self):
        """List all available test modules"""
        print("Available test modules:")
        for i, module in enumerate(self.test_modules, 1):
            print(f"  {i}. {module}")


def main():
    """Main function to handle command line arguments"""
    runner = RouteTestRunner()
    
    if len(sys.argv) == 1:
        # Run all tests
        success = runner.run_tests()
        sys.exit(0 if success else 1)
    
    elif len(sys.argv) == 2:
        arg = sys.argv[1]
        
        if arg == '--list':
            runner.list_test_modules()
            sys.exit(0)
        
        elif arg == '--help':
            print("Usage:")
            print("  python test_all_routes.py                    # Run all route tests")
            print("  python test_all_routes.py MODULE_NAME        # Run specific module tests")
            print("  python test_all_routes.py --list             # List available modules")
            print("  python test_all_routes.py --help             # Show this help")
            print()
            runner.list_test_modules()
            sys.exit(0)
        
        else:
            # Try to run specific module
            success = runner.run_individual_module(arg)
            sys.exit(0 if success else 1)
    
    else:
        print("Error: Too many arguments")
        print("Use 'python test_all_routes.py --help' for usage information")
        sys.exit(1)


if __name__ == "__main__":
    main()