from .app import app as app
from .constants import AWS_CREDENTIAL_FILEPATH, DEBUG_RECALL_INTELLIGENCE
from .database import Interview, db
from .utils import get_recall_headers, api_error_response
# from .routes import handle_auth_token, valid_token_response
from flask import request, jsonify
from botocore.exceptions import BotoCoreError, ClientError
import requests
import hashlib
import random
import boto3 
import json
import os

# Configure S3 settings and create an S3 client
S3_BUCKET_NAME = 'voxai-test-audio-video'
aws_credentials = json.load(open(AWS_CREDENTIAL_FILEPATH))
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

def get_analysis(url, analysis_type, video=False):
    """
    Calls the sentiment or engagement API.
    Args:
        url: The audio or video URL to load the interview recording file from.
        analysis_type: Either 'sentiment' or 'engagement'.
        video: Whether to process video (if true) or audio (if false).
    Returns:
        A single score for the content at the URL.
    """
    with app.test_client() as client:
        response = client.post(f'/test/{analysis_type}', json={'url': url, 'video': video})
    if response.status_code == 200:
        return response.json[f'{analysis_type}_score']
    else:
        print(f"{analysis_type.capitalize()} API error: {response.status_code}")
        return None

def get_sentiment(url, video=False):
    """
    Calls get_analysis with analysis_type="sentiment". 
    """
    return get_analysis(url, "sentiment", video)

def get_engagement(url, video=False):
    """
    Calls get_analysis with analysis_type="engagement". 
    """
    return get_analysis(url, "engagement", video)


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
        return api_error_response("No URL provided", 400)
    if (audio_url and "s3://" not in audio_url) or (video_url and "s3://" not in video_url):
        return api_error_response("Invalid URL provided", 400)
    
    data = {}
    
    def download_and_reupload_file(input_url, output_key):
        """Download a file from input_url and re-upload it to a new S3 key."""
        try:
            bucket_name = input_url.split('/')[2]
            input_key = input_url.split('/')[-1]
            
            # Download the original file
            file_content = s3_client.get_object(Bucket=bucket_name, Key=input_key)['Body'].read()
            
            # Upload to the new location
            s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=output_key, Body=file_content)
            
            # Return the new S3 URL
            return f's3://{S3_BUCKET_NAME}/{output_key}'
        except (BotoCoreError, ClientError) as e:
            print(f"Error in S3 operation: {str(e)}")
            return None
    
    if audio_url:
        audio_output_key = 'file_example_MP3_700KB.mp3'
        data['audio_url_preprocessed'] = download_and_reupload_file(audio_url, audio_output_key)
    
    if video_url:
        video_output_key = 'file_example_MP4_480_1_5MG.mp4'
        data['video_url_preprocessed'] = download_and_reupload_file(video_url, video_output_key)

    if (audio_url and data['audio_url_preprocessed'] is None) or (video_url and data['video_url_preprocessed'] is None):
        return api_error_response("Invalid S3 file", 500)
    
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
        return api_error_response("Invalid URL", 400)
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
        return api_error_response("Invalid URL", 400)
    # (Temporary) Return a random number based on hashing the URL (in a different way than sentiment)
    return jsonify({"engagement_score": int(hashlib.md5(url.encode()).hexdigest(), 16) % 100}), 200

@app.route('/api/join_meeting', methods=['POST'])
def join_meeting():
    """Joins and begins recording a meeting on Zoom, Google Meet, Microsoft Teams, or Slack with the bot account."""
    url = request.json.get('url')
    headers = get_recall_headers()
    if "error" in headers: 
        return api_error_response(headers["error"], 500)
    
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
    
    # TODO: only pass full response to client when some debug flag is set 
    if response.status_code == 201:
        return jsonify(response.json()), 201
    else:
        return jsonify(response.json()), 400

@app.route('/api/generate_transcript', methods=['POST'])
def generate_transcript():
    """Generates a transcript from a meeting recorded by the bot account."""
    bot_id = request.json.get('id')
    if not bot_id:
        return api_error_response("Missing required field: id", 400)

    headers = get_recall_headers()
    if "error" in headers: 
        return api_error_response(headers["error"], 500)

    data = {
        'assemblyai_async_transcription': {
            # 'language': 'US English',
            'language_code': 'en_us',
            'speaker_labels': True, 
            'disfluencies': True, # keep filler words
            'sentiment_analysis': True,
            'summarization': True,
            'entity_detection': True,
            'iab_categories': True,
            # 'summary_model': 'informative',
            # 'summary_type': 'bullets',
            # 'word_boost': ['word 1', 'word 2'], # improve accuracy by specifying words likely to be in the transcript
            # 'boost_param': 'default', # low, default, or high
        }
    }

    response = requests.post('https://us-west-2.recall.ai/api/v2beta/bot/' + bot_id + '/analyze', headers=headers, json=data) 

    # TODO: only pass full response to client when some debug flag is set 
    if response.status_code == 201:
        return jsonify(response.json()), 201
    else:
        return jsonify(response.json()), 400
    """
    Other possible parameters to the transcription API:

    auto_highlights
    boolean
    Docs: https://www.assemblyai.com/docs/audio-intelligence#detect-important-phrases-and-words

    custom_spelling
    array of objects
    Docs: https://www.assemblyai.com/docs/core-transcription#custom-spelling

    language_detection
    boolean
    Docs: https://www.assemblyai.com/docs/core-transcription#automatic-language-detection

    redact_pii_policies
    array of strings
    Docs: https://www.assemblyai.com/docs/audio-intelligence#pii-redaction

    content_safety
    boolean
    Docs: https://www.assemblyai.com/docs/audio-intelligence#content-moderation

    auto_chapters
    boolean
    Docs: https://www.assemblyai.com/docs/audio-intelligence#auto-chapters

    """

@app.route('/api/analyze_interview', methods=['POST'])
def analyze_interview():
    """Gets the result of the interview analysis for a given interview."""
    # TODO: check auth here (can't currently due to circular import)
    # current_user_id = handle_auth_token(sessions)
    # if current_user_id is None:
    #     return valid_token_response(False) 

    headers = get_recall_headers()
    if "error" in headers: 
        return api_error_response(headers["error"], 500)

    bot_id = request.json.get('id')

    interview = Interview.query.filter_by(recall_id=bot_id).first()
    if not interview:
        return api_error_response("Interview not found", 404)

    transcript_response = requests.get('https://us-west-2.recall.ai/api/v1/bot/' + bot_id + '/transcript', headers=headers)
    intelligence_response = requests.get('https://us-west-2.recall.ai/api/v1/bot/' + bot_id + '/intelligence', headers=headers)

    # Check for HTTP errors in transcript response
    if transcript_response.status_code != 200:
        return jsonify({
            "error": f"Transcript API request failed with status code {transcript_response.status_code}",
            "details": transcript_response.text
        }), 500

    # Check for HTTP errors in intelligence response
    if intelligence_response.status_code != 200:
        return jsonify({
            "error": f"Intelligence API request failed with status code {intelligence_response.status_code}",
            "details": intelligence_response.text
        }), 500

    intelligence_data = intelligence_response.json()

    summary = intelligence_data.get("assembly_ai.summary", "")
    topics = intelligence_data.get("assembly_ai.iab_categories_result", {}).get("summary", {})
    top_5_topics = dict(sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5])
    sentiment_analysis = intelligence_data.get("assembly_ai.sentiment_analysis_results", [])

    # TODO: Verify auth privileges for user making this request
    if interview:
        interview.summary = summary
        db.session.commit()

    return jsonify({
        "summary": summary,
        "topics": top_5_topics,
        "sentiment_analysis": sentiment_analysis,
        "transcript": transcript_response.json(),
        "debug_intelligence_response": intelligence_response.json() if DEBUG_RECALL_INTELLIGENCE else None 
    }), 200

    return jsonify({"transcript_response": transcript_response.json(), "intelligence_response": intelligence_response.json()}), 200

