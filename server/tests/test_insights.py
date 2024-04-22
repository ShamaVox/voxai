import pytest
from flask import json

def test_get_insights(client):
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
