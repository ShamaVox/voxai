from collections import Counter, defaultdict
from operator import attrgetter
import re
from itertools import groupby

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