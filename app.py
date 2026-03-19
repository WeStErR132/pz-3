#!/usr/bin/env python3
"""
Flask-приложение для демонстрации CI/CD
"""
from flask import Flask, jsonify
import os
import socket

app = Flask(__name__)

@app.route('/')
def hello():
    """Главная страница"""
    student_name = os.environ.get('STUDENT_NAME', 'Student')
    environment = os.environ.get('ENVIRONMENT', 'dev')
    version = "2.0.0"
    
    return f"""
    <html>
    <head><title>CI/CD Demo - {environment.upper()}</title></head>
    <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; min-height: 100vh;">
        <div style="background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; display: inline-block; box-shadow: 0 8px 32px rgba(0,0,0,0.3);">
            <h1 style="color: #4CAF50; margin-bottom: 20px;">🚀 Hello from Jenkins CI/CD Pipeline!</h1>
            <p><strong>Student:</strong> {student_name}</p>
            <p><strong>Environment:</strong> {environment.upper()}</p>
            <p><strong>Hostname:</strong> {socket.gethostname()}</p>
            <p><strong>Version:</strong> {version}</p>
            <p><strong>Build:</strong> #{os.environ.get('BUILD_NUMBER', 'N/A')}</p>
            <hr style="margin: 20px 0; border: 1px solid rgba(255,255,255,0.3);">
            <p style="font-size: 0.9em; opacity: 0.8;">Deployed with ❤️ via Jenkins</p>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "python-app",
        "version": "2.0.0",
        "environment": os.environ.get('ENVIRONMENT', 'dev')
    })

@app.route('/api/info')
def api_info():
    """API информация"""
    return jsonify({
        "app": "Student CI/CD Demo",
        "version": "2.0.0",
        "endpoints": ["/", "/health", "/api/info"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
