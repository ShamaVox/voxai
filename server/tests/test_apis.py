import pytest
from flask import json
from server.src import input_validation, verification, database
from server.app import app as flask_app
from server.src.apis import preprocess, get_sentiment, get_engagement
from .utils.synthetic_data import create_synthetic_data
from unittest.mock import patch, Mock
import boto3

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

    url = "s3://test-bucket/audio.mp3"

    mock_response = Mock(ok=True)
    mock_response.status_code = 200
    mock_response.json = lambda: {'sentiment_score': 80}
    mock_post.return_value = mock_response

    sentiment = get_sentiment(url)

    mock_post.assert_called_once()
    assert sentiment == 80


@patch('requests.post')
def test_get_engagement(mock_post):
    """Test the get_engagement function."""

    url = "s3://test-bucket/video.mp4"

    mock_response = Mock(ok=True)
    mock_response.status_code = 200
    mock_response.json = lambda: {'engagement_score': 60}
    mock_post.return_value = mock_response

    engagement = get_engagement(url, video=True)

    mock_post.assert_called_once()
    assert engagement == 60

@pytest.mark.parametrize(
    "url, sentiment, video, expected_status, expected_score",
    [
        ("s3://test-audio-video/file_example_MP3_700KB.mp3", True, False, 200, 69),  
        ("s3://test-audio-video/file_example_MP4_480_1_5MG.mp4", True, True, 200, 13), 
        ("s3://test-audio-video/file_example_MP3_700KB.mp3", False, False, 200, 80), 
        ("s3://test-audio-video/file_example_MP4_480_1_5MG.mp4", False, True, 200, 73), 
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
        ("s3://test-audio-video/file_example_MP3_700KB.mp3", None, 200, "s3://test-audio-video/file_example_MP3_700KB.mp3", None), 
        (None, "s3://test-audio-video/file_example_MP4_480_1_5MG.mp4", 200, None, "s3://test-audio-video/file_example_MP4_480_1_5MG.mp4"), 
        (None, None, 400, None, None), 
        ("s3://test-audio-video/file_example_MP3_700KB.mp3", "s3://test-audio-video/file_example_MP4_480_1_5MG.mp4", 200, "s3://test-audio-video/file_example_MP3_700KB.mp3", "s3://test-audio-video/file_example_MP4_480_1_5MG.mp4"), 
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