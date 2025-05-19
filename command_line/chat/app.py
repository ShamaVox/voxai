import os
import json
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

# --- Configuration ---
CREDENTIALS_FILE = "credentials.json"
# Updated SYSTEM_PROMPT for analyzing recruiter conversation
SYSTEM_PROMPT = """
You are an AI assistant specializing in talent acquisition and role definition.
You will be given a transcript of an intake call conversation between a Recruiter and a Hiring Manager (HM). The purpose of this call is to define and clarify the requirements for a new or existing role.

Your task is to analyze the provided transcript and identify insightful and relevant questions that either the Recruiter or the Hiring Manager could ask next to ensure a comprehensive understanding of the role. These questions should aim to:

1.  **Clarify Ambiguities:** Identify areas where information is vague, missing, or potentially contradictory.
2.  **Deepen Understanding:** Probe for more specific details about responsibilities, skills, experience, team dynamics, success metrics, or challenges associated with the role.
3.  **Ensure Alignment:** Help both the Recruiter and HM confirm they have a shared understanding of the ideal candidate profile and the role's objectives.
4.  **Uncover Unstated Assumptions:** Surface any implicit expectations or assumptions that haven't been explicitly discussed.
5.  **Facilitate Effective Sourcing:** Elicit information crucial for the Recruiter to effectively source and attract qualified candidates.
6.  **Streamline the Hiring Process:** Touch upon aspects like the interview process, key stakeholders, or timelines if not already covered.

Avoid questions that have already been clearly answered by either participant. The questions should be pertinent to the specific details (or lack thereof) in the conversation.

Based on the conversation transcript, suggest 3 key questions. If a question seems more pertinent for one party to ask the other (e.g., Recruiter to HM, or HM to Recruiter for clarification on market/sourcing), you can subtly indicate this. Otherwise, frame them as general clarification questions for the role.

Present the questions clearly, each on their own line. Keep your response concise and only include the questions.
"""

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Load API Key and Configure Gemini ---
api_key = None
try:
    with open(CREDENTIALS_FILE, 'r') as f:
        credentials = json.load(f)
        api_key = credentials.get("gemini_api_key")
except FileNotFoundError:
    print(f"ERROR: The credentials file '{CREDENTIALS_FILE}' was not found.")
    print("Please create it with your Gemini API key.")
    exit(1)
except json.JSONDecodeError:
    print(f"ERROR: The credentials file '{CREDENTIALS_FILE}' is not valid JSON.")
    exit(1)

if not api_key:
    print(f"ERROR: 'gemini_api_key' not found in '{CREDENTIALS_FILE}'.")
    exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash-latest') # or 'gemini-pro' for potentially more nuanced analysis


# --- Routes ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/api/ask_gemini', methods=['POST'])
def ask_gemini():
    """Handles API requests to Gemini."""
    try:
        data = request.get_json()
        if not data or 'prompt' not in data: # 'prompt' here refers to the transcript
            return jsonify({"error": "No transcript provided"}), 400

        transcript_text = data['prompt'] # The user input is now the transcript
        if not transcript_text.strip():
            return jsonify({"error": "Transcript cannot be empty"}), 400

        # The full prompt now combines the system prompt with the user's transcript
        full_prompt = f"{SYSTEM_PROMPT}\n\n--- CONVERSATION TRANSCRIPT ---\n{transcript_text}\n\n--- END OF TRANSCRIPT ---"

        print(f"Sending to Gemini (first 100 chars of transcript): {transcript_text[:100]}...")

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]

        response = model.generate_content(
            full_prompt,
            safety_settings=safety_settings,
        )

        if response.parts:
            gemini_text = ''.join(part.text for part in response.parts if hasattr(part, 'text'))
        else:
            block_reason = response.prompt_feedback.block_reason if response.prompt_feedback else "Unknown"
            gemini_text = f"Blocked by safety settings or no content generated. Reason: {block_reason}"
            if response.prompt_feedback and response.prompt_feedback.safety_ratings:
                 gemini_text += f"\nSafety Ratings: {response.prompt_feedback.safety_ratings}"


        return jsonify({"response": gemini_text})

    except Exception as e:
        print(f"Error in /api/ask_gemini: {e}")
        error_message = str(e)
        if hasattr(e, 'message'): error_message = e.message
        elif hasattr(e, 'args') and e.args: error_message = str(e.args[0])
        return jsonify({"error": f"An internal error occurred: {error_message}"}), 500

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True, port=5001)