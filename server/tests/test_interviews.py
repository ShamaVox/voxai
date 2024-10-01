from flask import json
import pytest
import requests

from .utils.synthetic_data import create_test_account_and_set_token

def test_get_interviews(client):
    create_test_account_and_set_token(client, "test_interviews@test.com", "AUTHTOKENINTERVIEWS", 10, 3)
    # Send a GET request to the endpoint
    response = client.get("/api/interviews")

    # Assert the response
    assert response.status_code == 200
    interviews = json.loads(response.data)
    assert isinstance(interviews, list)
    assert len(interviews) == 10 * 3

    for interview in interviews:
        assert isinstance(interview, dict)
        assert "id" in interview
        assert isinstance(interview["id"], int)
        assert "date" in interview
        assert isinstance(interview["date"], str)
        assert "time" in interview
        assert isinstance(interview["time"], str)
        assert "candidateName" in interview
        assert isinstance(interview["candidateName"], str)
        assert "currentCompany" in interview
        assert isinstance(interview["currentCompany"], str)
        assert "interviewers" in interview
        assert isinstance(interview["interviewers"], str)
        assert "role" in interview
        assert isinstance(interview["role"], str)