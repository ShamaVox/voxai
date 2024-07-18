from .app import app as app
from .constants import AWS_CREDENTIAL_FILEPATH, DEBUG_RECALL_INTELLIGENCE, DEBUG_RECALL_RECORDING_RETRIEVAL
from .database import Interview, db, TranscriptLine
from .queries import get_transcript_lines_in_order
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
from sqlalchemy import func
from collections import Counter
import re
from itertools import groupby
from operator import attrgetter
from collections import Counter

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

import requests
from urllib.parse import urlparse

def download_and_reupload_file(input_url, output_key):
    """Download a file from input_url (S3 or HTTP) and re-upload it to a new S3 key."""
    try:
        parsed_url = urlparse(input_url)
        
        if parsed_url.scheme in ['http', 'https']:
            # Handle HTTP/HTTPS URL
            response = requests.get(input_url)
            response.raise_for_status()  # Raise an exception for bad status codes
            file_content = response.content
        elif parsed_url.scheme == 's3':
            # Handle S3 URL
            bucket_name = parsed_url.netloc
            input_key = parsed_url.path.lstrip('/')
            file_content = s3_client.get_object(Bucket=bucket_name, Key=input_key)['Body'].read()
        else:
            raise ValueError(f"Unsupported URL scheme: {parsed_url.scheme}")
        
        # Upload to the new location
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=output_key, Body=file_content)
        
        # Return the new S3 URL
        return f's3://{S3_BUCKET_NAME}/{output_key}'
    except (BotoCoreError, ClientError) as e:
        print(f"Error in S3 operation: {str(e)}")
        return None
    except requests.RequestException as e:
        print(f"Error downloading file from URL: {str(e)}")
        return None
    except ValueError as e:
        print(str(e))
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
        return api_error_response("No URL provided", 400)
    if (audio_url and "s3://" not in audio_url) or (video_url and "s3://" not in video_url):
        return api_error_response("Invalid URL provided", 400)
    
    data = {}
    
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
        interview.keywords = list(top_5_topics.keys())

        # Process and save TranscriptLines
        process_transcript_lines(interview.interview_id, intelligence_data)
        db.session.commit()

    return jsonify({
        "summary": summary,
        "topics": top_5_topics,
        "sentiment_analysis": sentiment_analysis,
        "transcript": transcript_response.json(),
        "debug_intelligence_response": intelligence_response.json() if DEBUG_RECALL_INTELLIGENCE else None 
    }), 200

    return jsonify({"transcript_response": transcript_response.json(), "intelligence_response": intelligence_response.json()}), 200


@app.route('/api/interviews/<int:interview_id>/transcript', methods=['GET'])
def get_interview_transcript(interview_id):
    """Gets the transcript for a given interview."""
    # Check if the interview exists
    interview = db.session.get(Interview, interview_id)
    if not interview:
        return jsonify({"error": "Interview not found"}), 404

    # Retrieve all transcript lines for this interview using the existing function
    transcript_lines = get_transcript_lines_in_order(interview_id)

    # Serialize the transcript lines
    transcript_data = []
    for line in transcript_lines:
        transcript_data.append({
            "id": line.id,
            "text": line.text,
            "start": line.start,
            "end": line.end,
            "confidence": line.confidence,
            "sentiment": line.sentiment,
            "engagement": line.engagement,
            "speaker": line.speaker,
            "labels": line.labels
        })

    return jsonify(transcript_data), 200

def process_transcript_lines(interview_id, intelligence_data):
    # Create a dictionary to store labels for each time range
    label_dict = {}
    for result in intelligence_data['assembly_ai.iab_categories_result']['results']:
        start = result['timestamp']['start']
        end = result['timestamp']['end']
        labels = [f"{label['label']}:{label['relevance']}" for label in result['labels']]
        label_dict[(start, end)] = labels

    # Process each utterance from the transcript
    utterances = intelligence_data.get("assembly_ai.iab_categories_result", {}).get("sentiment_analysis_results", {})
    for utterance in utterances:
        # Find matching labels
        matching_labels = []
        for (start, end), labels in label_dict.items():
            if utterance['start'] >= start and utterance['end'] <= end:
                matching_labels = labels
                break

        # Find matching sentiment analysis
        matching_sentiment = next((s for s in intelligence_data['assembly_ai.iab_categories_result']['sentiment_analysis_results']
                                   if s['start'] <= utterance['start'] and s['end'] >= utterance['end']), None)

        # Create or update TranscriptLine
        transcript_line = TranscriptLine.query.filter_by(
            interview_id=interview_id,
            start=utterance['start'],
            end=utterance['end']
        ).first()

        if transcript_line:
            # Update existing TranscriptLine
            transcript_line.text = utterance['text']
            transcript_line.confidence = utterance['confidence']
            transcript_line.speaker = utterance['speaker']
            transcript_line.labels = json.dumps(matching_labels)
            transcript_line.sentiment = matching_sentiment['sentiment'] if matching_sentiment else None
        else:
            # Create new TranscriptLine
            transcript_line = TranscriptLine(
                interview_id=interview_id,
                text=utterance['text'],
                start=utterance['start'],
                end=utterance['end'],
                confidence=utterance['confidence'],
                speaker=utterance['speaker'],
                labels=json.dumps(matching_labels),
                sentiment=matching_sentiment['sentiment'] if matching_sentiment else None
            )
            db.session.add(transcript_line)

    # Calculate and update interview metrics
    update_interview_metrics(interview_id)

def update_interview_metrics(interview_id):
    # Calculate total duration
    duration = db.session.query(func.max(TranscriptLine.end) - func.min(TranscriptLine.start)).filter_by(interview_id=interview_id).scalar()

    # Calculate speaking time and word count
    speaking_time = db.session.query(func.sum(TranscriptLine.end - TranscriptLine.start)).filter_by(interview_id=interview_id).scalar()
    word_count = db.session.query(func.sum(func.array_length(func.string_to_array(TranscriptLine.text, ' '), 1))).filter_by(interview_id=interview_id).scalar()

    # Calculate WPM
    wpm = int((word_count / (speaking_time / 60)) if speaking_time is not None and speaking_time > 0 else 0)

    # Calculate overall sentiment
    sentiments = db.session.query(TranscriptLine.sentiment).filter_by(interview_id=interview_id).all()
    sentiment_scores = {'POSITIVE': 1, 'NEUTRAL': 0, 'NEGATIVE': -1}
    overall_sentiment = sum(sentiment_scores.get(s[0], 0) for s in sentiments if s[0]) / len(sentiments) if sentiments else 0

    transcript_lines = db.session.query(TranscriptLine).filter_by(interview_id=interview_id) # TODO: add an order_by here? 
    engagement_json= {
        #"interview_duration": calculated_duration,
        #"conversation_silence_duration": calculated_silence,
        "word_counts": count_all_words(transcript_lines),
        "talk_duration_by_speaker": calculate_talk_duration(transcript_lines),
        "speaking_rate_variations": calculate_speaking_rate_variations(transcript_lines)
    }

    # Update Interview object
    interview = db.session.get(Interview, interview_id)
    if interview:
        interview.duration = duration
        interview.speaking_time = speaking_time
        interview.wpm = wpm
        interview.sentiment = int((overall_sentiment + 1) * 50)  # Convert to 0-100 scale
        interview.engagement_json = engagement_json

    db.session.commit()

@app.route('/api/transcript_lines', methods=['POST'])
def create_transcript_line():
    data = request.json
    
    # Validate input
    required_fields = ['interview_id', 'text', 'start', 'end', 'confidence', 'sentiment', 'engagement', 'speaker', 'labels']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        new_line = TranscriptLine(
            interview_id=data['interview_id'],
            text=data['text'],
            start=float(data['start']),
            end=float(data['end']),
            confidence=float(data['confidence']),
            sentiment=data['sentiment'],
            engagement=data['engagement'],
            speaker=data['speaker'],
            labels=data['labels']
        )
        
        # Additional validations
        if not (0 <= new_line.confidence <= 1):
            return jsonify({"error": "Confidence must be between 0 and 1"}), 400
        
        if new_line.sentiment not in ['positive', 'negative', 'neutral', 'very positive', 'very negative']:
            return jsonify({"error": "Invalid sentiment value"}), 400
        
        if new_line.engagement not in ['low', 'medium', 'high']:
            return jsonify({"error": "Invalid engagement value"}), 400
        
        db.session.add(new_line)
        db.session.commit()
        
        return jsonify({
            "id": new_line.id,
            "text": new_line.text,
            "start": new_line.start,
            "end": new_line.end,
            "confidence": new_line.confidence,
            "sentiment": new_line.sentiment,
            "engagement": new_line.engagement,
            "speaker": new_line.speaker,
            "labels": new_line.labels
        }), 201
    except ValueError:
        return jsonify({"error": "Invalid data types provided"}), 400

@app.route('/api/transcript_lines/<int:line_id>', methods=['PUT'])
def update_transcript_line(line_id):
    line = db.session.get(TranscriptLine, line_id)
    if not line:
        return jsonify({"error": "Transcript line not found"}), 404
    
    data = request.json
    
    try:
        if 'text' in data:
            line.text = data['text']
        if 'start' in data:
            line.start = float(data['start'])
        if 'end' in data:
            line.end = float(data['end'])
        if 'confidence' in data:
            line.confidence = float(data['confidence'])
        if 'sentiment' in data:
            line.sentiment = data['sentiment']
        if 'engagement' in data:
            line.engagement = data['engagement']
        if 'speaker' in data:
            line.speaker = data['speaker']
        if 'labels' in data:
            line.labels = data['labels']
        
        db.session.commit()
        
        return jsonify({
            "id": line.id,
            "text": line.text,
            "start": line.start,
            "end": line.end,
            "confidence": line.confidence,
            "sentiment": line.sentiment,
            "engagement": line.engagement,
            "speaker": line.speaker,
            "labels": line.labels
        }), 200
    except ValueError:
        return jsonify({"error": "Invalid data types provided"}), 400

@app.route('/api/transcript_lines/<int:line_id>', methods=['DELETE'])
def delete_transcript_line(line_id):
    line = db.session.get(TranscriptLine, line_id)
    if not line:
        return jsonify({"error": "Transcript line not found"}), 404
    
    db.session.delete(line)
    db.session.commit()
    
    return '', 204

@app.route('/api/save_recording/<string:bot_id>', methods=['GET'])
def save_recording(bot_id):
    """Saves the recording from a specific bot."""
    headers = get_recall_headers()
    if "error" in headers:
        return api_error_response(headers["error"], 500)

    response = requests.get(f'https://us-west-2.recall.ai/api/v1/bot/{bot_id}/', headers=headers)

    if response.status_code == 200:
        interview = Interview.query.filter_by(recall_id=bot_id).first()
        if not interview:
            return api_error_response("Interview not found", 404)
        data = response.json()
        video_url = data.get('video_url')
        download_and_reupload_file(video_url, bot_id + ".mp4")
        meeting_url = data.get('meeting_url')

        # Save video URL to database
        interview.video_url = video_url
        db.session.commit()

        return jsonify({
            "bot_id": bot_id,
            "meeting_url": meeting_url,
            "full_response": data if DEBUG_RECALL_RECORDING_RETRIEVAL else None 
        }), 200
    else:
        return api_error_response(f"Failed to retrieve bot information: {response.text}", response.status_code)

def calculate_talk_duration(transcript_lines):
    durations = {}
    
    for speaker, group in groupby(transcript_lines, key=attrgetter('speaker')):
        total_duration = sum((line.end - line.start) for line in group)
        durations[speaker] = total_duration
    
    return durations

def calculate_speaking_rate_variations(transcript_lines, window_size=60):
    variations = []
    
    for line in transcript_lines:
        words = len(line.text.split())
        duration = (line.end - line.start) / 60  # Convert to minutes
        wpm = words / duration if duration > 0 else 0
        
        variations.append({
            "speaker": line.speaker,
            "start_time": line.start,
            "end_time": line.end,
            "wpm": round(wpm, 2)
        })
    
    return variations

def calculate_engagement_metrics(interview_id):
    transcript_lines = TranscriptLine.query.filter_by(interview_id=interview_id).order_by(TranscriptLine.start).all()
    
    if not transcript_lines:
        return None
    
    interview_duration = transcript_lines[-1].end - transcript_lines[0].start
    
    # Calculate silence duration
    total_talk_time = sum(line.end - line.start for line in transcript_lines)
    silence_duration = interview_duration - total_talk_time
    
    engagement_json = {
        "interview_duration": interview_duration,
        "conversation_silence_duration": silence_duration,
        "common_words_utterance_count": count_common_words(transcript_lines),
        "talk_duration_by_speaker": calculate_talk_duration(transcript_lines),
        "speaking_rate_variations": calculate_speaking_rate_variations(transcript_lines)
    }
    
    return engagement_json

def count_all_words(transcript_lines):
    word_counter = Counter()
    
    for line in transcript_lines:
        # Convert to lowercase and split into words
        # This regex splits on any non-word character, effectively separating words and removing punctuation
        words = re.findall(r'\w+', line.text.lower())
        word_counter.update(words)
    
    # Convert to a regular dictionary and sort by count (descending)
    word_count_dict = dict(word_counter)
    sorted_word_count = dict(sorted(word_count_dict.items(), key=lambda item: item[1], reverse=True))
    
    return sorted_word_count

# Error handling for methods not allowed
@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405