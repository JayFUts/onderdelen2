#!/usr/bin/env python3
"""
Simple test app for Railway deployment
"""
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "test"}), 200

@app.route('/')
def index():
    return jsonify({
        "message": "OnderdelenLijn Scraper is running!",
        "port": os.environ.get('PORT', '8080'),
        "status": "ok"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)