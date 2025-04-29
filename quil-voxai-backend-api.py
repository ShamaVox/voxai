# --------------------------
# Backend: app.py (Flask + AI Summary + Delta Parser + MongoDB Integration)
# --------------------------

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from bson import ObjectId
import json
import os
import openai
from pymongo import MongoClient
import logging

# Configuration
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "voxai"
COLLECTION = "transcripts"
API_KEY = "your-api-key"
OPENAI_API_KEY = "your-openai-key"

openai.api_key = OPENAI_API_KEY

app = Flask(__name__)
CORS(app)

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION]

# AI Agent: Generates summary from HTML content (or Delta later)
def generate_summary(html_content):
    prompt = f"""
    Analyze the following interview transcript content and write a concise summary of the candidate’s skills, communication ability, and team fit.

    Transcript:
    {html_content}

    Summary:
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    return response['choices'][0]['message']['content'].strip()

@app.route('/notes', methods=['POST'])
def save_notes():
    try:
        data = request.json
        candidate_id = data.get('candidateId')
        html = data.get('notes')
        delta = data.get('delta', None)

        if not candidate_id or not html:
            return jsonify({'error': 'Missing candidateId or notes'}), 400

        summary = generate_summary(html)

        entry = {
            "candidateId": candidate_id,
            "notes_html": html,
            "delta": delta,
            "summary": summary,
            "created_at": datetime.utcnow()
        }

        result = collection.insert_one(entry)
        return jsonify({"message": "Notes saved successfully", "id": str(result.inserted_id), "summary": summary}), 200

    except Exception as e:
        logging.exception("Error in /notes endpoint")
        return jsonify({'error': str(e)}), 500

@app.route('/notes/<candidate_id>', methods=['GET'])
def get_notes(candidate_id):
    record = collection.find_one({"candidateId": candidate_id})
    if not record:
        return jsonify({'error': 'No record found'}), 404
    record['_id'] = str(record['_id'])
    return jsonify(record), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)

