from bs4 import BeautifulSoup
from unittest.mock import patch, Mock
import requests
from .utils.synthetic_data import create_test_account_and_set_token
import json
from server.app import app as flask_app
from server.src.database import db

def test_parse_greenhouse_jobs_success(client):
    """Test parsing a Greenhouse jobs page successfully."""
    # Sample Greenhouse HTML content (simplified for testing)
    html_content = """
    <html>
    <body>
    <a data-mapped="true" href="/job1">Job Title 1</a>
    <a data-mapped="true" href="/job2">Job Title 2</a>
    </body>
    </html>
    """

    create_test_account_and_set_token(client, "test_greenhouse@test.com", "AUTHTOKENGREENHOUSE", 10, 3)

    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html_content
        mock_get.return_value = mock_response

        response = client.post('/api/greenhouse', json={'url': 'https://example.com/jobs'})

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'job_data' in data
        assert len(data['job_data']) == 2
        assert data['job_data'][0]['title'] == 'Job Title 1'
        assert data['job_data'][0]['url'] == '/job1'
        assert data['job_data'][1]['title'] == 'Job Title 2'
        assert data['job_data'][1]['url'] == '/job2'

def test_parse_greenhouse_jobs_missing_url(client):
    """Test handling a missing URL parameter."""
    create_test_account_and_set_token(client, "test_greenhouse@test.com", "AUTHTOKENGREENHOUSE", 10, 3)
    response = client.post('/api/greenhouse', json={})

    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert "Missing 'url' parameter" in data['error']

def test_parse_greenhouse_jobs_request_error(client):
    """Test handling a request error when fetching the Greenhouse page."""
    create_test_account_and_set_token(client, "test_greenhouse@test.com", "AUTHTOKENGREENHOUSE", 10, 3)
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.RequestException('Test Exception')

        response = client.post('/api/greenhouse', json={'url': 'https://example.com/jobs'})

        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert "Error fetching Greenhouse page" in data['error']