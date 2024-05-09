import pytest
from flask import json
from .utils.synthetic_data import create_test_account_and_set_token

def test_get_insights(client):
    create_test_account_and_set_token(client, "test_insights@test.com", "AUTHTOKENINSIGHTS")
    # Send a GET request to the endpoint
    response = client.get("/api/insights")

    # Assert the response
    assert response.status_code == 200
    insights = json.loads(response.data)
    assert isinstance(insights, dict)
    assert "candidateStage" in insights
    assert isinstance(insights["candidateStage"], int)
    assert "fittingJobApplication" in insights
    assert isinstance(insights["fittingJobApplication"], int)
    assert "fittingJobApplicationPercentage" in insights
    assert isinstance(insights["fittingJobApplicationPercentage"], int)
    assert "averageInterviewPace" in insights
    assert isinstance(insights["averageInterviewPace"], int)
    assert "averageInterviewPacePercentage" in insights
    assert isinstance(insights["averageInterviewPacePercentage"], int)
    assert "lowerCompensationRange" in insights
    assert isinstance(insights["lowerCompensationRange"], int)
    assert "upperCompensationRange" in insights
    assert isinstance(insights["upperCompensationRange"], int)

# TODO: Test updating metric history