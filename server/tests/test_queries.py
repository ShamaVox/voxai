import pytest
from datetime import datetime, timedelta
from .utils.synthetic_data import create_synthetic_data_for_fitting_percentage, create_synthetic_data_for_average_interview_pace
from server.src.queries import fitting_job_applications_percentage, average_interview_pace
from server.app import app as flask_app

# Define test cases with expected outcomes
test_cases = [
    # (match_threshold, days, expected_percentage, expected_change)
    (80, 7, 60, 20), 
    (50, 2, 90, 100),
    (10, 30, 21, -30),
    (75, 17, 50, -99),
    (0, 10, 100, 0),
    (100, 5, 0, 0),
]

@pytest.mark.parametrize(
    "match_threshold, days, expected_percentage, expected_change",
    test_cases
)
def test_fitting_job_applications_percentage(
    client, match_threshold, days, expected_percentage, expected_change
):
    with flask_app.app_context():
        # Create synthetic data for the test 
        current_user_id = create_synthetic_data_for_fitting_percentage(match_threshold, days, expected_percentage, expected_change)

        # Call the function with test parameters
        percentage, change = fitting_job_applications_percentage(current_user_id, match_threshold, days)

    # Assert the results
    assert percentage == expected_percentage
    assert change == expected_change

@pytest.mark.parametrize(
    "days, percentage_days, expected_average_pace, expected_percentage_change",
    [
    (30, 90, 15, 0),
    (10, 30, 5, 25),
    (14, 60, 9, -10)
]
)
def test_average_interview_pace(
    client, days, percentage_days, expected_average_pace, expected_percentage_change
):
    with flask_app.app_context():
        # Create synthetic data for the test
        current_user_id = create_synthetic_data_for_average_interview_pace(days, percentage_days, expected_average_pace, expected_percentage_change)

        # Call the function with test parameters
        average_pace, percentage_change = average_interview_pace(current_user_id, days, percentage_days)

    # Assert the results
    assert average_pace == expected_average_pace
    assert percentage_change == expected_percentage_change