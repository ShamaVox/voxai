# apis/analysis.py
from flask import jsonify, request
import hashlib
import json

from ..app import app
from ..utils import api_error_response

@app.route('/test/sentiment', methods=['POST'])
def calculate_sentiment():
    url = request.json.get('url')
    if url.startswith("s3://"):
        # In real implementation, load from S3
        pass
    else:
        return api_error_response("Invalid URL", 400)
    return jsonify({"sentiment_score": int(hashlib.sha256(url.encode()).hexdigest(), 16) % 100}), 200

@app.route('/test/engagement', methods=['POST'])
def calculate_engagement():
    url = request.json.get('url')
    if url.startswith("s3://"):
        # In real implementation, load from S3
        pass
    else:
         return api_error_response("Invalid URL", 400)
    return jsonify({"engagement_score": int(hashlib.md5(url.encode()).hexdigest(), 16) % 100}), 200

def get_analysis(url, analysis_type, video=False):
    with app.test_client() as client:
        response = client.post(f'/test/{analysis_type}', json={'url': url, 'video': video})
    if response.status_code == 200:
        return response.json[f'{analysis_type}_score']
    else:
        print(f"{analysis_type.capitalize()} API error: {response.status_code}")
        return None

def get_sentiment(url, video=False):
    return get_analysis(url, "sentiment", video)

def get_engagement(url, video=False):
    return get_analysis(url, "engagement", video)