from .database import db, Application, Role, MetricHistory
from datetime import datetime, timedelta

def fitting_job_applications_percentage(match_threshold, current_user_id, days):
    """
    Gets the percentage of job applications posted by a user with candidate score over a certain threshold. 

    Args:
        match_threshold: The required candidate score for an application to be counted as "Fitting".
        current_user_id: The user's account id. 
        days: The number of days to consider for the average calculation (default: 7).

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

    fitting_job_applications_percentage = round((fitting_applications_count / total_applications_count) * 100 if total_applications_count > 0 else 0)

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