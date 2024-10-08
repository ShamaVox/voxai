from flask import jsonify, request
import json
import requests

from ..app import app
from ..constants import DEBUG_RECALL_INTELLIGENCE, DEBUG_RECALL_RECORDING_RETRIEVAL
from ..database import db, Interview, TranscriptLine
from ..sessions import sessions
from ..utils import get_recall_headers, api_error_response, valid_token_response, handle_auth_token, download_and_reupload_file

from .transcript import process_transcript_lines

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