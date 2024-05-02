from .database import db, Application, Role

def fitting_job_applications_percentage(match_threshold, current_user_id):
    """
    Gets the percentage of job applications posted by a user with candidate score over a certain threshold. 

    Args:
        match_threshold: The required candidate score for an application to be counted as "Fitting".
        current_user_id: The user's account id. 

    Returns:
        The percentage of job applications with score over match_threshold. 
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