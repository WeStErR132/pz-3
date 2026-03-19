import unittest
import json
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

class TestApp(unittest.TestCase):
    """Тесты для Flask-приложения"""
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_hello_endpoint(self):
        """Тест главной страницы"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hello from Jenkins', response.data)
        self.assertIn(b'Student', response.data)
    
    def test_health_endpoint(self):
        """Тест health check"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'python-app')
    
    def test_api_info_endpoint(self):
        """Тест API info"""
        response = self.app.get('/api/info')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('app', data)
        self.assertIn('version', data)
        self.assertIn('endpoints', data)
    
    def test_404_endpoint(self):
        """Тест несуществующего endpoint"""
        response = self.app.get('/nonexistent')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main(verbosity=2)
