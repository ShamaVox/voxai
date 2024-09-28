from collections import Counter, defaultdict
from flask import jsonify, request
from itertools import groupby
import json
from operator import attrgetter
import re
from sqlalchemy import func

from ..app import app
from ..database import db, Interview, TranscriptLine
from ..queries import get_transcript_lines_in_order

# TODO: add docstrings

def calculate_silence_by_speaker(transcript_lines):
    # TODO: calculate different counts of pauses in consecutive lines by the same speaker, and pauses when switching between speakers
    silence_by_speaker = {}
    previous_line = None

    for line in transcript_lines:
        if previous_line:
            silence_duration = line.start - previous_line.end
            # Attribute silence to the next speaker
            if silence_duration > 0:
                silence_by_speaker[line.speaker] = silence_by_speaker.get(line.speaker, 0) + silence_duration
        previous_line = line

    return silence_by_speaker

def calculate_talk_duration(transcript_lines):
    durations = defaultdict(int)
    for line in transcript_lines:
        durations[line.speaker] += line.end - line.start
    return dict(durations)

def calculate_speaking_rate_variations(transcript_lines, window_size=60):
    variations = []
    
    for line in transcript_lines:
        words = len(line.text.split())
        duration = (line.end - line.start) / 60000  # Convert to minutes
        wpm = words / duration if duration > 0 else 0
        
        variations.append({
            "speaker": line.speaker,
            "start_time": line.start,
            "end_time": line.end,
            "wpm": round(wpm, 2)
        })
    
    return variations

def calculate_engagement_metrics(interview_id):
    with app.app_context():
        transcript_lines = TranscriptLine.query.filter_by(interview_id=interview_id).order_by(TranscriptLine.start).all()
    
    if not transcript_lines:
        return None
    
    interview_duration = transcript_lines[-1].end - transcript_lines[0].start
    
    # Calculate silence duration
    total_talk_time = sum(line.end - line.start for line in transcript_lines)
    silence_duration = interview_duration - total_talk_time
    
    engagement_json = {
        "interview_duration": interview_duration,
        "conversation_silence_duration": silence_duration,
        "word_count": count_all_words(transcript_lines),
        "talk_duration_by_speaker": calculate_talk_duration(transcript_lines),
        "speaking_rate_variations": calculate_speaking_rate_variations(transcript_lines)
    }
    
    return engagement_json

def count_words(text):
    return len(re.findall(r"\b[a-z']+\b", text.lower()))

def count_words_by_speaker(transcript_lines):
    # Sort the transcript lines by speaker first
    sorted_lines = sorted(transcript_lines, key=attrgetter('speaker'))
    
    word_count_by_speaker = {}
    for speaker, lines in groupby(sorted_lines, key=attrgetter('speaker')):
        # Convert the grouped iterator to a list before summing
        word_count_by_speaker[speaker] = sum(count_words(line.text) for line in list(lines))
    
    return word_count_by_speaker

def count_all_words(transcript_lines):
    word_counter = Counter()
    
    for line in transcript_lines:
        words = re.findall(r"\b[a-z']+\b", line.text.lower())
        word_counter.update(words)
    
    # Convert to a regular dictionary and sort by count (descending)
    word_count_dict = dict(word_counter)
    sorted_word_count = dict(sorted(word_count_dict.items(), key=lambda item: item[1], reverse=True))
    
    return sorted_word_count

@app.route('/api/interviews/<int:interview_id>/transcript', methods=['GET'])
def get_interview_transcript(interview_id):
    """Gets the transcript for a given interview."""
    # Check if the interview exists
    interview = db.session.get(Interview, interview_id)
    if not interview:
        return jsonify({"error": "Interview not found"}), 404

    # Retrieve all transcript lines for this interview using the existing function
    transcript_lines = get_transcript_lines_in_order(interview_id)

    # Serialize the transcript lines
    transcript_data = []
    for line in transcript_lines:
        transcript_data.append({
            "id": line.id,
            "text": line.text,
            "start": line.start,
            "end": line.end,
            "confidence": line.confidence,
            "sentiment": line.sentiment,
            "engagement": line.engagement,
            "speaker": line.speaker,
            "labels": line.labels
        })

    return jsonify(transcript_data), 200

def process_transcript_lines(interview_id, intelligence_data):
    # Create a dictionary to store labels for each time range
    label_dict = {}
    for result in intelligence_data['assembly_ai.iab_categories_result']['results']:
        start = result['timestamp']['start']
        end = result['timestamp']['end']
        labels = [f"{label['label']}:{label['relevance']}" for label in result['labels']]
        label_dict[(start, end)] = labels

    # Process each utterance from the transcript
    utterances = intelligence_data.get("assembly_ai.iab_categories_result", {}).get("sentiment_analysis_results", {})
    for utterance in utterances:
        # Find matching labels
        matching_labels = []
        for (start, end), labels in label_dict.items():
            if utterance['start'] >= start and utterance['end'] <= end:
                matching_labels = labels
                break

        # Find matching sentiment analysis
        matching_sentiment = next((s for s in intelligence_data['assembly_ai.iab_categories_result']['sentiment_analysis_results']
                                   if s['start'] <= utterance['start'] and s['end'] >= utterance['end']), None)

        # Create or update TranscriptLine
        transcript_line = TranscriptLine.query.filter_by(
            interview_id=interview_id,
            start=utterance['start'],
            end=utterance['end']
        ).first()

        if transcript_line:
            # Update existing TranscriptLine
            transcript_line.text = utterance['text']
            transcript_line.confidence = utterance['confidence']
            transcript_line.speaker = utterance['speaker']
            transcript_line.labels = json.dumps(matching_labels)
            transcript_line.sentiment = matching_sentiment['sentiment'] if matching_sentiment else None
        else:
            # Create new TranscriptLine
            transcript_line = TranscriptLine(
                interview_id=interview_id,
                text=utterance['text'],
                start=utterance['start'],
                end=utterance['end'],
                confidence=utterance['confidence'],
                speaker=utterance['speaker'],
                labels=json.dumps(matching_labels),
                sentiment=matching_sentiment['sentiment'] if matching_sentiment else None
            )
            db.session.add(transcript_line)

    # Calculate and update interview metrics
    update_interview_metrics(interview_id)

def update_interview_metrics(interview_id):
    transcript_lines = db.session.query(TranscriptLine).filter_by(interview_id=interview_id).order_by(TranscriptLine.start).all()
    
    if not transcript_lines:
        return

    # 1. Interview duration
    duration = transcript_lines[-1].end - transcript_lines[0].start

    # 2. Word count by speaker and overall
    word_count_by_speaker = count_words_by_speaker(transcript_lines)

    word_count = count_all_words(transcript_lines)

    # 3. Overall silence duration
    total_speech_duration = sum(line.end - line.start for line in transcript_lines)
    overall_silence_duration = duration - total_speech_duration

    # 4. Silence duration by speaker
    silence_duration_by_speaker = calculate_silence_by_speaker(transcript_lines)

    # Calculate speaking time and word count
    word_count = sum(word_count.values())

    # Calculate WPM
    wpm = (word_count / (total_speech_duration / 60000) if total_speech_duration > 0 else 0)

    # Calculate overall sentiment
    sentiments = [line.sentiment for line in transcript_lines if line.sentiment]
    sentiment_scores = {'POSITIVE': 1, 'NEUTRAL': 0, 'NEGATIVE': -1}
    overall_sentiment = sum(sentiment_scores.get(s, 0) for s in sentiments) / len(sentiments) if sentiments else 0

    engagement_json = {
        "interview_duration": duration,
        "word_count_by_speaker": word_count_by_speaker,
        "overall_silence_duration": overall_silence_duration,
        "silence_duration_by_speaker": silence_duration_by_speaker,
        "word_counts": count_all_words(transcript_lines),
        "talk_duration_by_speaker": calculate_talk_duration(transcript_lines),
        "speaking_rate_variations": calculate_speaking_rate_variations(transcript_lines)
    }

    # Update Interview object
    interview = db.session.get(Interview, interview_id)
    if interview:
        interview.duration = duration
        interview.speaking_time = total_speech_duration
        interview.wpm = wpm
        interview.sentiment = int((overall_sentiment + 1) * 50)  # Convert to 0-100 scale
        interview.engagement_json = engagement_json

    db.session.commit()

@app.route('/api/transcript_lines', methods=['POST'])
def create_transcript_line():
    data = request.json
    
    # Validate input
    required_fields = ['interview_id', 'text', 'start', 'end', 'confidence', 'sentiment', 'engagement', 'speaker', 'labels']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        new_line = TranscriptLine(
            interview_id=data['interview_id'],
            text=data['text'],
            start=float(data['start']),
            end=float(data['end']),
            confidence=float(data['confidence']),
            sentiment=data['sentiment'],
            engagement=data['engagement'],
            speaker=data['speaker'],
            labels=data['labels']
        )
        
        # Additional validations
        if not (0 <= new_line.confidence <= 1):
            return jsonify({"error": "Confidence must be between 0 and 1"}), 400
        
        if new_line.sentiment not in ['positive', 'negative', 'neutral', 'very positive', 'very negative']:
            return jsonify({"error": "Invalid sentiment value"}), 400
        
        if new_line.engagement not in ['low', 'medium', 'high']:
            return jsonify({"error": "Invalid engagement value"}), 400
        
        db.session.add(new_line)
        db.session.commit()
        
        return jsonify({
            "id": new_line.id,
            "text": new_line.text,
            "start": new_line.start,
            "end": new_line.end,
            "confidence": new_line.confidence,
            "sentiment": new_line.sentiment,
            "engagement": new_line.engagement,
            "speaker": new_line.speaker,
            "labels": new_line.labels
        }), 201
    except ValueError:
        return jsonify({"error": "Invalid data types provided"}), 400

@app.route('/api/transcript_lines/<int:line_id>', methods=['PUT'])
def update_transcript_line(line_id):
    line = db.session.get(TranscriptLine, line_id)
    if not line:
        return jsonify({"error": "Transcript line not found"}), 404
    
    data = request.json
    
    try:
        if 'text' in data:
            line.text = data['text']
        if 'start' in data:
            line.start = float(data['start'])
        if 'end' in data:
            line.end = float(data['end'])
        if 'confidence' in data:
            line.confidence = float(data['confidence'])
        if 'sentiment' in data:
            line.sentiment = data['sentiment']
        if 'engagement' in data:
            line.engagement = data['engagement']
        if 'speaker' in data:
            line.speaker = data['speaker']
        if 'labels' in data:
            line.labels = data['labels']
        
        db.session.commit()
        
        return jsonify({
            "id": line.id,
            "text": line.text,
            "start": line.start,
            "end": line.end,
            "confidence": line.confidence,
            "sentiment": line.sentiment,
            "engagement": line.engagement,
            "speaker": line.speaker,
            "labels": line.labels
        }), 200
    except ValueError:
        return jsonify({"error": "Invalid data types provided"}), 400

@app.route('/api/transcript_lines/<int:line_id>', methods=['DELETE'])
def delete_transcript_line(line_id):
    line = db.session.get(TranscriptLine, line_id)
    if not line:
        return jsonify({"error": "Transcript line not found"}), 404
    
    db.session.delete(line)
    db.session.commit()
    
    return '', 204