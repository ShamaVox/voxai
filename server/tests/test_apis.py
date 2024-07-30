import pytest
from flask import json
from server.src import input_validation, verification, database
from server.app import app as flask_app
from server.src.database import db, Interview, TranscriptLine
from server.src.apis import preprocess, get_sentiment, get_engagement
import server.src.utils 
from .utils.synthetic_data import create_synthetic_data
from unittest.mock import patch, Mock
import requests
import boto3
from datetime import datetime as datetime
from botocore.exceptions import BotoCoreError
from server.src.apis import (
    count_all_words,
    calculate_talk_duration,
    calculate_speaking_rate_variations,
    calculate_engagement_metrics
)
from unittest import mock


EXPECTED_WORD_COUNT_TRANSCRIPT = {
    'hello': 1, 'how': 1, 'are': 1, 'you': 2, 'today': 1, 'i\'m': 1, 'doing': 1, 'well': 1, 'thank': 1, 'for': 1, 'asking': 1, 'great': 1, 'let\'s': 1, 'begin': 1, 'the': 1, 'interview': 1
}

EXPECTED_WORD_COUNT_TRANSCRIPT_LINES = {
    'hello': 1, 'how': 1, 'are': 1, 'you': 2, 'today': 1,
    'i\'m': 1, 'doing': 1, 'well': 1, 'thank': 1, 'for': 1,
    'asking': 1, 'great': 1, 'let\'s': 1, 'begin': 1, 'the': 1,
    'interview': 1 }

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

@pytest.fixture
def sample_data():
    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        # Generate synthetic data
        create_synthetic_data(10,1)
        
        # TODO: Use mock_interview to get the first interview and have this fixture merely generate the data
        # Get the first interview
        interview = Interview.query.filter_by(recall_id='test_bot_id').first()
        if interview is None:
            interview = Interview.query.first()
            interview.recall_id = 'test_bot_id'
        db.session.commit()

        # Return the interview 
        return interview.interview_id

def mock_interview(sample_data):
    """Returns the interview object instead of the interview id."""
    with flask_app.app_context():
        interview = Interview.query.get(sample_data)
        assert interview is not None, "Interview not found"
        return interview

@pytest.fixture
def sample_transcript(sample_data):
    with flask_app.app_context():
        transcript_lines = [
            TranscriptLine(
                interview_id=sample_data,
                text="Hello, how are you?",
                start=0,
                end=3000,
                confidence=0.95,
                sentiment="positive",
                engagement="high",
                speaker="interviewer",
                labels="greeting"
            ),
            TranscriptLine(
                interview_id=sample_data,
                text="I'm doing well, thank you.",
                start=3500,
                end=6000,
                confidence=0.98,
                sentiment="positive",
                engagement="medium",
                speaker="candidate",
                labels="response"
            )
        ]
        db.session.add_all(transcript_lines)
        db.session.commit()
        return [line.id for line in transcript_lines]

@pytest.fixture
def sample_transcript_lines():
    return [
        TranscriptLine(
            interview_id=1,
            text="Hello, how are you today?",
            start=0,
            end=3000,
            confidence=0.95,
            sentiment="positive",
            speaker="interviewer"
        ),
        TranscriptLine(
            interview_id=1,
            text="I'm doing well, thank you for asking.",
            start=3500,
            end=7000,
            confidence=0.98,
            sentiment="positive",
            speaker="candidate"
        ),
        TranscriptLine(
            interview_id=1,
            text="Great! Let's begin the interview.",
            start=7500,
            end=10000,
            confidence=0.97,
            sentiment="positive",
            speaker="interviewer"
        )
    ]

@patch('requests.post')  # Mock external API calls
def test_preprocess(mock_post):
    """Test the preprocess function."""

    # Create a mock Interview object 
    # TODO: Use a real Interview here instead of a mock one
    mock_interview = Mock()
    mock_interview.audio_url = "s3://test-bucket/audio.mp3"
    mock_interview.video_url = "s3://test-bucket/video.mp4"

    # Set up mock response from the preprocessing API
    mock_response = Mock(ok=True)
    mock_response.status_code = 200
    mock_response.json = lambda: {
        'audio_url_preprocessed': 's3://processed/audio.mp3',
        'video_url_preprocessed': 's3://processed/video.mp4',
    }
    mock_post.return_value = mock_response 

    # Call the preprocess function 
    preprocess(mock_interview, audio=True, video=True)

    # Assertions 
    mock_post.assert_called_once()
    assert mock_interview.audio_url_preprocessed == 's3://processed/audio.mp3'
    assert mock_interview.video_url_preprocessed == 's3://processed/video.mp4'

@patch('requests.post')
def test_get_sentiment(mock_post):
    """Test the get_sentiment function."""

    url = "s3://voxai-test-audio-video/file_example_MP3_700KB.mp3"

    sentiment = get_sentiment(url)

    assert sentiment == 4


@patch('requests.post')
def test_get_engagement(mock_post):
    """Test the get_engagement function."""

    url = "s3://voxai-test-audio-video/file_example_MP4_480_1_5MG.mp4"

    engagement = get_engagement(url, video=True)

    assert engagement == 55

@pytest.mark.parametrize(
    "url, sentiment, video, expected_status, expected_score",
    [
        ("s3://voxai-test-audio-video/file_example_MP3_700KB.mp3", True, False, 200, 4),  
        ("s3://voxai-test-audio-video/file_example_MP4_480_1_5MG.mp4", True, True, 200, 87), 
        ("s3://voxai-test-audio-video/file_example_MP3_700KB.mp3", False, False, 200, 34), 
        ("s3://voxai-test-audio-video/file_example_MP4_480_1_5MG.mp4", False, True, 200, 55), 
        ("invalid-url", True, False, 400, None),
        ("invalid-url", False, False, 400, None),
    ],
)

def test_sentiment_and_engagement(
    client, url, sentiment, video, expected_status, expected_score
):
    """Test sentiment and engagement analysis API calls."""

    if expected_status == 200:
        if sentiment:
            mock_response_json = {"sentiment_score": expected_score} 
        else:
            mock_response_json = {"engagement_score": expected_score}

    if sentiment:
        response = client.post('/test/sentiment', json={'url': url, 'video': video})
    else:
        response = client.post('/test/engagement', json={'url': url, 'video': video})

    assert response.status_code == expected_status

    if expected_status == 200:
        assert response.json == mock_response_json
    else:
        assert "error" in response.json


@pytest.mark.parametrize(
    "audio_url, video_url, expected_status, expected_preprocessed_audio, expected_preprocessed_video",
    [
        ("s3://voxai-test-audio-video/file_example_MP3_700KB.mp3", None, 200, "s3://voxai-test-audio-video/file_example_MP3_700KB.mp3", None), 
        (None, "s3://voxai-test-audio-video/file_example_MP4_480_1_5MG.mp4", 200, None, "s3://voxai-test-audio-video/file_example_MP4_480_1_5MG.mp4"), 
        (None, None, 400, None, None), 
        ("s3://voxai-test-audio-video/file_example_MP3_700KB.mp3", "s3://voxai-test-audio-video/file_example_MP4_480_1_5MG.mp4", 200, "s3://voxai-test-audio-video/file_example_MP3_700KB.mp3", "s3://voxai-test-audio-video/file_example_MP4_480_1_5MG.mp4"), 
        ("invalid-url", None, 400, None, None),
        (None, "invalid-url", 400, None, None),
        ("invalid-url", "invalid-url", 400, None, None),
    ],
)

def test_preprocess(client, audio_url, video_url, expected_status, expected_preprocessed_audio, expected_preprocessed_video):
    """Test the preprocess API route."""

    mock_response_json = {}
    if expected_preprocessed_audio is not None:
        mock_response_json['audio_url_preprocessed'] = expected_preprocessed_audio
    if expected_preprocessed_video is not None:
        mock_response_json['video_url_preprocessed'] = expected_preprocessed_video

    response = client.post('/test/preprocess', json={"audio_url": audio_url, "video_url": video_url})

    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json == mock_response_json
    else:
        assert "error" in response.json

@patch('requests.post')
def test_join_meeting_success(mock_post, client):
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {'id': 'test_bot_id'}
    mock_post.return_value = mock_response

    response = client.post('/api/join_meeting', json={'url': 'https://zoom.us/test'})
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'id' in data

@patch('requests.post')
def test_join_meeting_failure(mock_post, client):
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {'error': 'Invalid meeting URL'}
    mock_post.return_value = mock_response

    response = client.post('/api/join_meeting', json={'url': 'invalid_url'})
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_join_meeting_missing_url(client):
    response = client.post('/api/join_meeting', json={})
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'meeting_url' in data
    assert data['meeting_url'] == ['This field may not be null.']

@patch('requests.post')
def test_generate_transcript_success(mock_post, client):
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {'transcript_id': 'test_transcript_id'}
    mock_post.return_value = mock_response

    response = client.post('/api/generate_transcript', json={'id': 'test_bot_id'})
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'transcript_id' in data

@patch('requests.post')
def test_generate_transcript_failure(mock_post, client):
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {'error': 'Invalid bot ID'}
    mock_post.return_value = mock_response

    response = client.post('/api/generate_transcript', json={'id': 'invalid_id'})
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_generate_transcript_missing_id(client):
    response = client.post('/api/generate_transcript', json={})
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'id' in data['error']

@patch('requests.get')
def test_analyze_interview_success(mock_requests_get, client, sample_data, sample_transcript):
    # Mock the responses
    mock_transcript_response = Mock()
    mock_transcript_response.status_code = 200
    mock_transcript_response.json.return_value = {
        "transcript": [
            {
                "text": "Hello, how are you?",
                "start": 0,
                "end": 3000,
                "confidence": 0.95,
                "speaker": "interviewer"
            },
            {
                "text": "I'm doing well, thank you.",
                "start": 3500,
                "end": 6000,
                "confidence": 0.98,
                "speaker": "candidate"
            }
        ]
    }

    mock_intelligence_response = Mock()
    mock_intelligence_response.status_code = 200
    mock_intelligence_response.json.return_value = {
        "assembly_ai.summary": "This is a test summary",
        "assembly_ai.iab_categories_result": {
            "summary": {
                "topic1": 0.9,
                "topic2": 0.8,
                "topic3": 0.7,
                "topic4": 0.6,
                "topic5": 0.5,
                "topic6": 0.4
            },
            "results": []  # Add this empty list to avoid KeyError
        },
        "assembly_ai.sentiment_analysis_results": [
            {"sentiment": "positive", "confidence": 0.8, "text": "Sample text", "start": 0, "end": 1000}
        ]
    }

    mock_requests_get.side_effect = [mock_transcript_response, mock_intelligence_response]

    response = client.post('/api/analyze_interview', json={'id': 'test_bot_id'})

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "summary" in data
    assert data["summary"] == "This is a test summary"
    assert len(data["topics"]) == 5
    assert "sentiment_analysis" in data
    assert "transcript" in data
    assert len(data["transcript"]["transcript"]) == 2

    # Check that the interview record was updated in the database
    with flask_app.app_context():
        updated_interview = Interview.query.filter_by(recall_id='test_bot_id').first()
        assert updated_interview is not None
        assert updated_interview.summary == "This is a test summary"
        assert set(updated_interview.keywords) == set(["topic1", "topic2", "topic3", "topic4", "topic5"])

        # Check that TranscriptLines were updated
        transcript_lines = TranscriptLine.query.filter_by(interview_id=updated_interview.interview_id).all()
        assert len(transcript_lines) == 2
        assert transcript_lines[0].text == "Hello, how are you?"
        assert transcript_lines[1].text == "I'm doing well, thank you."

@patch('server.src.utils.get_recall_headers')
def test_analyze_interview_header_error(mock_get_recall_headers, client):
    # Mock the get_recall_headers function to return an error
    mock_get_recall_headers.return_value = {"error": "Failed to get headers"}
    
    # Make the request
    response = client.post('/api/analyze_interview', json={'id': 'test_bot_id'})
    
    # Assert the response
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data

@patch('requests.get')
def test_analyze_interview_api_error(mock_requests_get, client):
    # Mock a failed response
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_requests_get.return_value = mock_response

    response = client.post('/api/analyze_interview', json={'id': 'test_bot_id'})
    
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data
    assert "API request failed with status code 404" in data["error"]
    assert "details" in data
    assert data["details"] == "Not Found"

@patch('requests.get')
def test_analyze_interview_missing_data(mock_requests_get, client, sample_data):
    # Mock the requests.get responses with missing data
    mock_transcript_response = Mock()
    mock_transcript_response.status_code = 200
    mock_transcript_response.json.return_value = {}
    
    mock_intelligence_response = Mock()
    mock_intelligence_response.status_code = 200
    mock_intelligence_response.json.return_value = {
        "assembly_ai.summary": "",
        "assembly_ai.iab_categories_result": {
            "summary": {},
            "results": []
        },
        "assembly_ai.sentiment_analysis_results": []
    }
    
    mock_requests_get.side_effect = [mock_transcript_response, mock_intelligence_response]
    
    # Make the request
    response = client.post('/api/analyze_interview', json={'id': 'test_bot_id'})
    
    # Assert the response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["summary"] == ""
    assert data["topics"] == {}
    assert data["sentiment_analysis"] == []
    assert data["transcript"] == {}

    # Check that the interview record in the database was not updated
    with flask_app.app_context():
        updated_interview = Interview.query.filter_by(recall_id='test_bot_id').first()
        assert updated_interview is not None
        assert updated_interview.summary is None or updated_interview.summary == ""
        assert updated_interview.keywords is None or updated_interview.keywords == []

        # Check that no new TranscriptLines were added
        transcript_lines = TranscriptLine.query.filter_by(interview_id=updated_interview.interview_id).all()
        assert len(transcript_lines) == 0

def test_analyze_interview_nonexistent_id(client):
    response = client.post('/api/analyze_interview', json={'id': 'nonexistent_id'})
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "error" in data
    assert "Interview not found" in data["error"]

def test_create_transcript_line(client, sample_data):
    new_line = {
        "interview_id": sample_data,
        "text": "This is a test line.",
        "start": 6500,
        "end": 9000,
        "confidence": 0.92,
        "sentiment": "neutral",
        "engagement": "medium",
        "speaker": "interviewer",
        "labels": "question"
    }
    
    response = client.post('/api/transcript_lines', json=new_line)
    assert response.status_code == 201
    data = json.loads(response.data)
    assert "id" in data
    assert data["text"] == "This is a test line."

def test_get_transcript_lines(client, sample_data, sample_transcript):
    response = client.get(f'/api/interviews/{sample_data}/transcript')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]["text"] == "Hello, how are you?"
    assert data[1]["text"] == "I'm doing well, thank you."
    
    # Additional assertions to check the structure of the response
    assert "id" in data[0]
    assert "start" in data[0]
    assert "end" in data[0]
    assert "confidence" in data[0]
    assert "sentiment" in data[0]
    assert "engagement" in data[0]
    assert "speaker" in data[0]
    assert "labels" in data[0]

def test_update_transcript_line(client, sample_transcript):
    line_id = sample_transcript[0]
    updated_data = {
        "text": "Updated text",
        "sentiment": "very positive"
    }
    
    response = client.put(f'/api/transcript_lines/{line_id}', json=updated_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["text"] == "Updated text"
    assert data["sentiment"] == "very positive"

def test_delete_transcript_line(client, sample_transcript):
    line_id = sample_transcript[0]
    
    response = client.delete(f'/api/transcript_lines/{line_id}')
    assert response.status_code == 204

    # Verify the line has been deleted
    with flask_app.app_context():
        deleted_line = db.session.get(TranscriptLine, line_id)
        assert deleted_line is None

def test_get_nonexistent_transcript(client):
    response = client.get('/api/interviews/9999/transcript')
    assert response.status_code == 404

def test_get_transcript_nonexistent_interview(client):
    response = client.get('/api/interviews/99999/transcript')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "Interview not found"

def test_create_invalid_transcript_line(client, sample_data):
    invalid_line = {
        "interview_id": sample_data,
        "text": "Invalid line",
        "start": "not a number",  # Invalid start time
        "end": 3000,
        "confidence": 1.5,  # Invalid confidence (should be between 0 and 1)
        "sentiment": "invalid_sentiment",
        "engagement": "super high",  # Invalid engagement level
        "speaker": "interviewer",
        "labels": ["label1", "label2"]  # Invalid labels format (should be a string)
    }
    
    response = client.post('/api/transcript_lines', json=invalid_line)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data

def test_update_nonexistent_transcript_line(client):
    response = client.put('/api/transcript_lines/9999', json={"text": "Updated text"})
    assert response.status_code == 404

def test_delete_nonexistent_transcript_line(client):
    response = client.delete('/api/transcript_lines/9999')
    assert response.status_code == 404

@patch('requests.get')
@patch('server.src.apis.download_and_reupload_file')
def test_save_recording_success(mock_download, mock_requests_get, client, sample_data):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'video_url': 'https://example.com/video.mp4',
        'meeting_url': 'https://zoom.us/j/123456789'
    }
    mock_requests_get.return_value = mock_response
    
    mock_download.return_value = 's3://your-bucket/test_bot_id.mp4'

    response = client.get('/api/save_recording/test_bot_id')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['bot_id'] == 'test_bot_id'
    assert data['meeting_url'] == 'https://zoom.us/j/123456789'
    
    mock_requests_get.assert_called_once()
    mock_download.assert_called_once_with('https://example.com/video.mp4', 'test_bot_id.mp4')
    
    updated_interview = Interview.query.filter_by(recall_id='test_bot_id').first()
    assert updated_interview.video_url == 'https://example.com/video.mp4'

@patch('requests.get')
def test_save_recording_api_error(mock_requests_get, client, sample_data):
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.text = "Bot not found"
    mock_requests_get.return_value = mock_response
    
    response = client.get('/api/save_recording/test_bot_id')
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "error" in data
    assert "Failed to retrieve bot information: Bot not found" in data["error"]

@patch('requests.get')
def test_save_recording_interview_not_found(mock_requests_get, client, sample_data):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_requests_get.return_value = mock_response
    response = client.get('/api/save_recording/nonexistent_bot_id')
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "Interview not found"
    
def test_count_all_words(sample_transcript_lines):
    word_count = count_all_words(sample_transcript_lines)
    assert word_count == EXPECTED_WORD_COUNT_TRANSCRIPT

def test_calculate_talk_duration(sample_transcript_lines):
    durations = calculate_talk_duration(sample_transcript_lines)
    assert durations == {
        'interviewer': 2500,
        'candidate': 3500
    }

def test_calculate_speaking_rate_variations(sample_transcript_lines):
    variations = calculate_speaking_rate_variations(sample_transcript_lines)
    assert len(variations) == 3
    assert variations[0] == {
        'speaker': 'interviewer',
        'start_time': 0,
        'end_time': 3000,
        'wpm': 100.0
    }
    assert variations[1] == {
        'speaker': 'candidate',
        'start_time': 3500,
        'end_time': 7000,
        'wpm': 120.0
    }
    assert variations[2] == {
        'speaker': 'interviewer',
        'start_time': 7500,
        'end_time': 10000,
        'wpm': 120.0
    }

@pytest.fixture
def mock_interview(sample_transcript_lines):
    return Interview(
        interview_id=1,
        interview_time=datetime.utcnow(),
        recall_id='test_bot_id'
    )

def test_calculate_engagement_metrics(mock_interview, sample_transcript_lines):
    with flask_app.app_context():
        # Add the sample transcript lines to the database
        for line in sample_transcript_lines:
            line.interview_id = mock_interview.interview_id
            db.session.add(line)
        db.session.commit()

        engagement_metrics = calculate_engagement_metrics(mock_interview.interview_id)
        
        assert engagement_metrics is not None
        assert engagement_metrics['interview_duration'] == 10000
        assert engagement_metrics['conversation_silence_duration'] == 1000
        assert engagement_metrics['word_count'] == EXPECTED_WORD_COUNT_TRANSCRIPT_LINES
        assert engagement_metrics['talk_duration_by_speaker'] == {
            'interviewer': 2500,
            'candidate': 3500
        }
        assert len(engagement_metrics['speaking_rate_variations']) == 3