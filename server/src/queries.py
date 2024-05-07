from .database import db, Application, Role, MetricHistory, Interview, Account, interview_interviewer_speaking_table
from datetime import datetime, timedelta
from .constants import MATCH_THRESHOLD, METRIC_HISTORY_DAYS_TO_AVERAGE, INTERVIEW_PACE_DAYS_TO_AVERAGE, INTERVIEW_PACE_CHANGE_DAYS_TO_AVERAGE

def fitting_job_applications_percentage(current_user_id, match_threshold=MATCH_THRESHOLD, days=METRIC_HISTORY_DAYS_TO_AVERAGE):
    """
    Gets the percentage of job applications posted by a user with candidate score over a certain threshold. 

    Args:
        match_threshold: The required candidate score for an application to be counted as "Fitting".
        current_user_id: The user's account id. 
        days: The number of days to consider for the average calculation.

    Returns:
        The percentage of job applications with score over match_threshold and the percentage change from the average.
    """
    fitting_job_applications_count = db.session.query(db.func.count(Application.application_id))\
        .join(Role, Application.role_id == Role.role_id)\
        .filter(Role.direct_manager_id == current_user_id)\
        .filter(Application.candidate_match > match_threshold)\
        .scalar()

    total_applications_count = db.session.query(db.func.count(Application.application_id))\
        .join(Role, Application.role_id == Role.role_id)\
        .filter(Role.direct_manager_id == current_user_id).scalar()

    fitting_job_applications_percentage = round((fitting_job_applications_count / total_applications_count) * 100 if total_applications_count > 0 else 0)

    if not fitting_job_applications_percentage:
        return 0, 0

    # Check if metric history has this account and the current day as an entry
    current_day = datetime.now().date()
    metric_history = MetricHistory.query.filter_by(account_id=current_user_id, metric_name='fitting_job_applications_percentage', metric_day=current_day).first()

    if metric_history:
        # Update the existing entry
        metric_history.metric_value = fitting_job_applications_percentage
    else:
        # Create a new entry for this day
        metric_history = MetricHistory(account_id=current_user_id, metric_name='fitting_job_applications_percentage', metric_value=fitting_job_applications_percentage, metric_day=current_day)
        db.session.add(metric_history)

    db.session.commit()

    # Calculate the average over the last N days
    start_date = current_day - timedelta(days=days)
    average_percentage = db.session.query(db.func.avg(MetricHistory.metric_value))\
        .filter(MetricHistory.account_id == current_user_id)\
        .filter(MetricHistory.metric_name == 'fitting_job_applications_percentage')\
        .filter(MetricHistory.metric_day >= start_date)\
        .filter(MetricHistory.metric_day != current_day)\
        .scalar()

    if average_percentage is None:
        # No entries found in the last N days, get the most recent value
        most_recent_entry = MetricHistory.query\
            .filter_by(account_id=current_user_id, metric_name='fitting_job_applications_percentage')\
            .order_by(MetricHistory.metric_day.desc()).first()

        if most_recent_entry:
            average_percentage = most_recent_entry.metric_value
        if not average_percentage:
            # No history available, return 0
            return fitting_job_applications_percentage, 0

    percentage_change = round((fitting_job_applications_percentage - average_percentage) / average_percentage * 100)

    return fitting_job_applications_percentage, percentage_change

def average_interview_pace(current_user_id, days=INTERVIEW_PACE_DAYS_TO_AVERAGE, percentage_days=INTERVIEW_PACE_CHANGE_DAYS_TO_AVERAGE):
    """
    Calculates the average interview pace for a user over the last N days and the percentage change compared to the last M days.

    Args:
        current_user_id: The user's account id.
        days: The number of days to consider for the average interview pace calculation (default: 7).
        percentage_days: The number of days to consider for the percentage change calculation (default: 30).

    Returns:
        The average interview pace in days and the percentage change.
    """
    current_date = datetime.now().date()
    start_date = current_date - timedelta(days=days)
    percentage_start_date = current_date - timedelta(days=percentage_days)

    # Get all interviews in the last N days where the account is an interviewer
    interviews = Interview.query.join(Interview.interviewers).filter(Account.account_id == current_user_id).filter(Interview.interview_time >= start_date).order_by(Interview.interview_time).all()

    if not interviews:
        return 0, 0

    total_time_diff = timedelta()
    prev_interview_time = None

    for interview in interviews:
        if prev_interview_time is None:
            # For the first interview, use the application time as the previous date/time
            application = Application.query.filter_by(application_id=interview.application_id).first()
            if application:
                prev_interview_time = application.application_time
        else:
            total_time_diff += interview.interview_time - prev_interview_time
            prev_interview_time = interview.interview_time

    average_pace = round(total_time_diff.days / len(interviews))

    # Calculate the average interview pace over the last M days excluding the last N days
    percentage_interviews = Interview.query.join(Interview.interviewers).filter(Account.account_id == current_user_id).filter(Interview.interview_time >= percentage_start_date).filter(Interview.interview_time < start_date).order_by(Interview.interview_time).all()

    if not percentage_interviews:
        return average_pace, 0

    percentage_total_time_diff = timedelta()
    percentage_prev_interview_time = None

    for interview in percentage_interviews:
        if percentage_prev_interview_time is None:
            application = Application.query.filter_by(application_id=interview.application_id).first()
            if application:
                percentage_prev_interview_time = application.application_time
        else:
            percentage_total_time_diff += interview.interview_time - percentage_prev_interview_time
            percentage_prev_interview_time = interview.interview_time

    percentage_average_pace = round(percentage_total_time_diff.days / len(percentage_interviews))

    if percentage_average_pace == 0:
        return average_pace, 0

    percentage_change = round((average_pace - percentage_average_pace) / percentage_average_pace * 100)

    return average_pace, percentage_change

def average_compensation_range(current_user_id):
    """
    Calculates the average lower and upper compensation range for the roles posted by an account.

    Args:
        current_user_id: The user's account id.

    Returns:
        The average lower and upper compensation range.
    """
    roles = Role.query.filter_by(direct_manager_id=current_user_id).all()

    if not roles:
        return 0, 0

    total_lower_compensation = 0
    total_upper_compensation = 0

    for role in roles:
        total_lower_compensation += role.base_compensation_min
        total_upper_compensation += role.base_compensation_max

    average_lower_compensation = round(total_lower_compensation / (1000 * len(roles)))
    average_upper_compensation = round(total_upper_compensation / (1000 * len(roles)))

    return average_lower_compensation, average_upper_compensation

def get_account_interviews(account_id, interviewer=True):
    """
    Retrieves interview data for a specific candidate or interviewer.

    Args:
        account_id: The candidate or interviewer's account ID.
        interviewer: Whether to search for candidates (if True) or interviewers (if False).

    Returns:
        A list of interview data for the candidate.
    """
    if interviewer:
        interviews = (
            db.session.query(Interview)
            .join(interview_interviewer_speaking_table, Interview.interview_id == interview_interviewer_speaking_table.c.interview_id)
            .filter(interview_interviewer_speaking_table.c.interviewer_id == account_id)
            .all()
        )
    else: 
        interviews = Interview.query.filter_by(candidate_id=candidate_id).all()

    interview_data = []
    for interview in interviews:
        role = Role.query.filter_by(role_id=interview.applications.role_id).first()
        interviewers = ", ".join([interviewer.name for interviewer in interview.interviewers])

        interview_data.append({
            "id": interview.interview_id,
            "date": interview.interview_time.strftime("%Y-%m-%d"),
            "time": interview.interview_time.strftime("%H:%M"),
            "candidateName": interview.candidate.candidate_name,
            "currentCompany": interview.candidate.current_company,
            "interviewers": interviewers,
            "role": role.role_name if role else "Unknown",
        })

    return interview_data