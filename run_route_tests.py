#!/usr/bin/env python3
"""
Simple Route Test Runner using Django's manage.py test command
"""
import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print('='*60)
    
    result = subprocess.run(command, shell=True, cwd=os.getcwd())
    
    if result.returncode == 0:
        print(f"✅ {description} - PASSED")
        return True
    else:
        print(f"❌ {description} - FAILED")
        return False

def main():
    """Run all route tests"""
    print("Comprehensive Route Tests for skinone-Upload-Classification")
    
    # Ensure we're in the right directory
    if not os.path.exists('manage.py'):
        print("Error: manage.py not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Get python executable path
    python_path = sys.executable
    if '.venv' in os.getcwd():
        python_path = f"{os.getcwd()}/.venv/bin/python"
    elif os.path.exists('.venv/bin/python'):
        python_path = f"{os.getcwd()}/.venv/bin/python"
    
    # Test commands to run
    test_commands = [
        (f"{python_path} manage.py test users.test_routes", "User Authentication Routes"),
        (f"{python_path} manage.py test users.test_admin_routes", "Admin Routes"), 
        (f"{python_path} manage.py test images.test_routes", "Image Management Routes"),
        (f"{python_path} manage.py test classification.test_routes", "Classification Routes"),
    ]
    
    # Run individual test suites
    results = []
    for command, description in test_commands:
        success = run_command(command, description)
        results.append((description, success))
    
    # Run all tests together
    print(f"\n{'='*60}")
    print("Running All Route Tests Together")
    print('='*60)
    
    all_tests_command = f"{python_path} manage.py test users.test_routes users.test_admin_routes images.test_routes classification.test_routes"
    all_success = run_command(all_tests_command, "All Route Tests Combined")
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{description:<40} {status}")
    
    print(f"{'All Tests Combined':<40} {'✅ PASSED' if all_success else '❌ FAILED'}")
    
    # Overall result
    total_passed = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print(f"\nOverall Result: {total_passed}/{total_tests} test suites passed")
    
    if all_success and total_passed == total_tests:
        print("🎉 ALL ROUTE TESTS PASSED! 🎉")
        sys.exit(0)
    else:
        print("⚠️  SOME TESTS FAILED ⚠️")
        sys.exit(1)

if __name__ == "__main__":
    main()