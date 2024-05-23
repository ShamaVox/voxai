from .app import app as app
from .database import Interview
from flask import request, jsonify
import requests
import hashlib
import random
import boto3 
import json
import os

# Configure S3 settings and create an S3 client
S3_BUCKET_NAME = 'voxai-test-audio-video'
aws_credentials = json.load(open(os.path.expanduser("~/.aws/credentials.json")))
s3_client = boto3.client('s3', aws_access_key_id=aws_credentials['aws_access_key_id'], aws_secret_access_key=aws_credentials['aws_secret_access_key'])

def preprocess(interview, audio=False, video=False):
    """
    Mocks a call to the preprocessing API, which cleans up audio or video data.
    Args:
        interview: A row in the Interview table, which contains the URLs to the audio and/or video to preprocess.
        audio: Whether or not to preprocess audio data. 
        video: Whether or not to preprocess video data.
    Returns:
        The URLs of the preprocessed audio and video files.
    """
    if not audio and not video:
        # No need to preprocess
        return 

    # Construct data to send to API
    data = {}
    if audio:
        data['audio_url'] = interview.audio_url
    if video:
        data['video_url'] = interview.video_url

    # Make a request to the preprocess API
    # TODO: Replace test implementation with real API call
    with app.test_client() as client:
        response = client.post('/test/preprocess', json=data)

    # Handle response and update Interview object
    if response.status_code == 200:
        interview.audio_url_preprocessed = response.json['audio_url_preprocessed']
        interview.video_url_preprocessed = response.json['video_url_preprocessed']
    else:
        # Handle API error
        print(f"Preprocessing API error: {response.status_code}")

def get_sentiment(url, video=False):
    """
    Calls the sentiment API.
    Args:
        url: The audio or video URL to load the interview recording file from.
        video: Whether to process video (if true) or audio (if false).
    Returns:
        A single sentiment score for the content at the URL.
    """
    # Make a request to the sentiment API
    # TODO: Replace test implementation with real API call
    with app.test_client() as client:
        response = client.post('/test/sentiment', json={'url': url, 'video': video})
    if response.status_code == 200:
        return response.json['sentiment_score']
    else:
        # Handle API error
        print(f"Sentiment API error: {response.status_code}")
        return None

def get_engagement(url, video=False):
    """
    Calls the engagement API.
    Args:
        url: The audio or video URL to load the interview recording file from.
        video: Whether to process video (if true) or audio (if false).
    Returns:
        A single sentiment score for the content at the URL.
    """
    # Make a request to the engagement API
    # TODO: Replace test implementation with real API call
    with app.test_client() as client:
        response = client.post('/test/engagement', json={'url': url, 'video': video})
    if response.status_code == 200:
        return response.json['engagement_score']
    else:
        # Handle API error
        print(f"Engagement API error: {response.status_code}")
        return None


# Temporary implementations of APIs
@app.route('/test/preprocess', methods=['POST'])
def preprocess_media():
    """A mock route to mimic preprocessing.

    Returns:
        A response with preprocessed URLs set in the JSON data
    """
    audio_url = request.json.get('audio_url')
    video_url = request.json.get('video_url')
    
    if not audio_url and not video_url:
        return jsonify({"error": "No URL provided"}), 400
    if (audio_url and "s3://" not in audio_url) or (video_url and "s3://" not in video_url):
        return jsonify({"error": "Invalid URL provided"}), 400
    
    data = {}
    
    def download_and_reupload_file(input_url, output_key):
        """Download a file from input_url and re-upload it to a new S3 key."""
        bucket_name = input_url.split('/')[2]
        input_key = input_url.split('/')[-1]
        
        # Download the original file
        file_content = s3_client.get_object(Bucket=bucket_name, Key=input_key)['Body'].read()
        
        # Upload to the new location
        # TODO: Don't wait for this upload to finish
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=output_key, Body=file_content)
        
        # Return the new S3 URL
        return f's3://{S3_BUCKET_NAME}/{output_key}'
    
    if audio_url:
        audio_output_key = 'file_example_MP3_700KB.mp3'
        data['audio_url_preprocessed'] = download_and_reupload_file(audio_url, audio_output_key)
    
    if video_url:
        video_output_key = 'file_example_MP4_480_1_5MG.mp4'
        data['video_url_preprocessed'] = download_and_reupload_file(video_url, video_output_key)
    
    return jsonify(data), 200

@app.route('/test/sentiment', methods=['POST'])
def calculate_sentiment():
    """A mock route to mimic sentiment analysis.

    Returns:
        A single integer value representing the sentiment score of an interview.
    """
    url = request.json.get('url')
    # Simulate loading from S3 if URL is an S3 URL
    if url.startswith("s3://"):
        s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=url.split("/")[-1]) 
    else:
        return jsonify({"error": "Invalid URL"}), 400
    # (Temporary) Return a random number based on hashing the URL
    return jsonify({"sentiment_score": int(hashlib.sha256(url.encode()).hexdigest(), 16) % 100}), 200

@app.route('/test/engagement', methods=['POST'])
def calculate_engagement():
    """A mock route to mimic engagement analysis.

    Returns:
        A single integer value representing the engagement score of an interview.
    """
    url = request.json.get('url')
    # Simulate loading from S3 if URL is an S3 URL
    if url.startswith("s3://"):
        s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=url.split("/")[-1]) 
    else:
        return jsonify({"error": "Invalid URL"}), 400
    # (Temporary) Return a random number based on hashing the URL (in a different way than sentiment)
    return jsonify({"engagement_score": int(hashlib.md5(url.encode()).hexdigest(), 16) % 100}), 200

@app.route('/api/join_meeting', methods=['POST'])
def join_meeting():
    """Joins and begins recording a meeting on Zoom, Google Meet, Microsoft Teams, or Slack with the bot account."""
    url = request.json.get('url')
    try:
        with open(os.path.expanduser("~/.aws/credentials.json")) as f:
            credentials = json.load(f)
        recall_api_key = credentials["recall_api_key"]
    except (FileNotFoundError, KeyError):
        return jsonify({"error": "Missing or incorrect Recall API credentials"}), 500
    
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'Authorization': f'Token {recall_api_key}'
    }
    
    data = {
        'meeting_url': url,
        'bot_name': 'VoxAI Bot',
        # 'real_time_transcription': {
        # },
        'automatic_leave': {
            'everyone_left_timeout': 150
        },
        'recording_mode': 'speaker_view'
    }
    
    response = requests.post('https://us-west-2.recall.ai/api/v1/bot/', headers=headers, json=data)
    
    if response.status_code == 201:
        return jsonify(response.json()), 201
    else:
        return jsonify(response.json()), 400