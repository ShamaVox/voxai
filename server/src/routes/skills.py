from flask import jsonify
import random

from ..app import app 
from ..database import Skill

@app.route('/api/skills', methods=['GET'])
def get_skills():
    """Fetches available skills from the database."""
    # TODO: Move to queries.py
    skills = Skill.query.all()

    # TODO: Add type to skills in database
    skill_types = ['hard', 'soft', 'behavioral']
    skill_list = [{"skill_id": skill.skill_id, "skill_name": skill.skill_name, "type": random.choice(skill_types)} for skill in skills]
    return jsonify({"skills": skill_list}), 200
