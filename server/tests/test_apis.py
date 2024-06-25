import pytest
from flask import json
from server.src import input_validation, verification, database
from server.app import app as flask_app
from server.src.database import db, Interview
from server.src.apis import preprocess, get_sentiment, get_engagement
import server.src.utils 
from .utils.synthetic_data import create_synthetic_data
from unittest.mock import patch, Mock
import requests
import boto3
from datetime import datetime as datetime
from botocore.exceptions import BotoCoreError

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

@pytest.fixture
def sample_data(client):
    # TODO: wipe previous database
    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        # Generate synthetic data
        create_synthetic_data(10,1)
        
        # Get the first interview
        interview = Interview.query.filter_by(recall_id='test_bot_id').first()
        if interview is None:
            interview = Interview.query.first()
            interview.recall_id = 'test_bot_id'
        db.session.commit()

        return interview

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
def test_analyze_interview_success(mock_requests_get, client, sample_data):
    # Mock the responses
    mock_transcript_response = Mock()
    mock_transcript_response.status_code = 200
    mock_transcript_response.json.return_value = {"transcript": "This is a test transcript"}

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
            }
        },
        "assembly_ai.sentiment_analysis_results": [
            {"sentiment": "positive", "confidence": 0.8}
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

    # Check that the interview record was updated in the database
    with flask_app.app_context():
        updated_interview = Interview.query.filter_by(recall_id='test_bot_id').first()
        assert updated_interview is not None
        assert updated_interview.summary == "This is a test summary"

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
def test_analyze_interview_missing_data(mock_requests_get, client):
    # TODO: Add handling for missing data and update this test to verify behavior
    # Mock the requests.get responses with missing data
    mock_transcript_response = Mock()
    mock_transcript_response.status_code = 200
    mock_transcript_response.json.return_value = {}
    
    mock_intelligence_response = Mock()
    mock_intelligence_response.status_code = 200
    mock_intelligence_response.json.return_value = {}
    
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

def test_analyze_interview_nonexistent_id(client):
    response = client.post('/api/analyze_interview', json={'id': 'nonexistent_id'})
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "error" in data
    assert "Interview not found" in data["error"]