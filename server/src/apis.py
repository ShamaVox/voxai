from .app import app as app
from .database import Interview, db
from flask import request, jsonify
import requests
import hashlib
import random
import boto3 
import json
import os

# Configure S3 settings and create an S3 client
S3_BUCKET_NAME = 'test-audio-video'
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
    with app.test_request_context():
        response = requests.post(app.url_for("preprocess_media", _external=True), json=data)

    # Handle response and update Interview object
    if response.status_code == 200:
        interview.audio_url_preprocessed = response.json().get('audio_url_preprocessed')
        interview.video_url_preprocessed = response.json().get('video_url_preprocessed')
        db.session.commit()
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
    with app.test_request_context():
        response = requests.post(app.url_for("calculate_sentiment", _external=True), json={'url': url, 'video': video})
    if response.status_code == 200:
        return response.json().get('sentiment_score')
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
    with app.test_request_context():
        response = requests.post(app.url_for("calculate_engagement", _external=True), json={'url': url, 'video': video})
    if response.status_code == 200:
        return response.json().get('engagement_score')
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
    # Load the audio and/or video from AWS S3 depending on whether APIs are passed or not
    audio_url = request.json.get('audio_url')
    video_url = request.json.get('video_url')
    if not audio_url and not video_url:
        return jsonify({"error": "No URL provided"}), 400
    if (audio_url and "s3://" not in audio_url) or (video_url and "s3://" not in video_url):
        return jsonify({"error": "Invalid URL provided"}), 400
    data = {}
    # (Temporary) Always set returned URLs to:
        # s3://test-audio-video/file_example_MP3_700KB.mp3 (for audio) 
        # s3://test-audio-video/file_example_MP4_480_1_5MG.mp4 (for video)
    if audio_url:
        s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=audio_url.split("/")[-1])
        data['audio_url_preprocessed'] = 's3://test-audio-video/file_example_MP3_700KB.mp3'
    if video_url:
        s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=video_url.split("/")[-1])
        data['video_url_preprocessed'] = 's3://test-audio-video/file_example_MP4_480_1_5MG.mp4'
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