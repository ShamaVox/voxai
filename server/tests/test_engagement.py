import pytest
from server.src.database import TranscriptLine, Interview, db
from server.app import app as flask_app
from server.src.apis import (
    count_all_words,
    calculate_talk_duration,
    calculate_speaking_rate_variations,
    calculate_engagement_metrics,
    update_interview_metrics
)
from datetime import datetime as datetime

from .test_apis import sample_data

EXPECTED_WORD_COUNT_TRANSCRIPT = {
    'hello': 1, 'how': 1, 'are': 1, 'you': 2, 'today': 1, 'i\'m': 1, 'doing': 1, 'well': 1, 'thank': 1, 'for': 1, 'asking': 1, 'great': 1, 'let\'s': 1, 'begin': 1, 'the': 1, 'interview': 1
}

EXPECTED_WORD_COUNT_TRANSCRIPT_LINES = {
    'hello': 1, 'how': 1, 'are': 1, 'you': 2, 'today': 1,
    'i\'m': 1, 'doing': 1, 'well': 1, 'thank': 1, 'for': 1,
    'asking': 1, 'great': 1, 'let\'s': 1, 'begin': 1, 'the': 1,
    'interview': 1 }

EXPECTED_WORD_COUNT_EXTENDED = {
        'you': 3, 'i\'m': 1, 'the': 1, 'hello': 1, 'how': 1, 'are': 1, 'today': 1, 'doing': 1,
        'well': 1, 'thank': 1, 'for': 1, 'asking': 1, 'great': 1, 'let\'s': 1, 
        'begin': 1, 'interview': 1, 'could': 1, 'tell': 1, 'me': 1, 'about': 1,
        'your': 1, 'experience': 2, 'sure': 1, 'i': 1, 'have': 1, 'five': 1, 'years': 1,
        'of': 1, 'in': 1, 'software': 1, 'development': 1
    }

@pytest.fixture
def sample_transcript_lines():
    return [
        TranscriptLine(
            interview_id=1,
            text="Hello, how are you today?",
            start=0,
            end=3000,
            confidence=0.95,
            sentiment="positive",
            speaker="interviewer"
        ),
        TranscriptLine(
            interview_id=1,
            text="I'm doing well, thank you for asking.",
            start=3500,
            end=7000,
            confidence=0.98,
            sentiment="positive",
            speaker="candidate"
        ),
        TranscriptLine(
            interview_id=1,
            text="Great! Let's begin the interview.",
            start=7500,
            end=10000,
            confidence=0.97,
            sentiment="positive",
            speaker="interviewer"
        )
    ]

@pytest.fixture
def extended_sample_transcript_lines():
    return [
        TranscriptLine(
            interview_id=1,
            text="Hello, how are you today?",
            start=0,
            end=3000,
            confidence=0.95,
            sentiment="positive",
            speaker="interviewer"
        ),
        TranscriptLine(
            interview_id=1,
            text="I'm doing well, thank you for asking.",
            start=3500,
            end=7000,
            confidence=0.98,
            sentiment="positive",
            speaker="candidate"
        ),
        TranscriptLine(
            interview_id=1,
            text="Great! Let's begin the interview.",
            start=7500,
            end=10000,
            confidence=0.97,
            sentiment="positive",
            speaker="interviewer"
        ),
        TranscriptLine(
            interview_id=1,
            text="Could you tell me about your experience?",
            start=11000,
            end=13000,
            confidence=0.96,
            sentiment="neutral",
            speaker="interviewer"
        ),
        TranscriptLine(
            interview_id=1,
            text="Sure! I have five years of experience in software development.",
            start=14000,
            end=18000,
            confidence=0.99,
            sentiment="positive",
            speaker="candidate"
        )
    ]

@pytest.mark.parametrize("transcript_lines, expected_word_count", [
    ("sample_transcript_lines", EXPECTED_WORD_COUNT_TRANSCRIPT_LINES),
    ("extended_sample_transcript_lines", EXPECTED_WORD_COUNT_EXTENDED)
])
    
def test_count_all_words(transcript_lines, expected_word_count, request):
    lines = request.getfixturevalue(transcript_lines)
    word_count = count_all_words(lines)
    assert word_count == expected_word_count

@pytest.mark.parametrize("transcript_lines, expected_durations", [
    ("sample_transcript_lines", {
        'interviewer': 5500,
        'candidate': 3500
    }),
    ("extended_sample_transcript_lines", {
        'interviewer': 7500,
        'candidate': 7500
    })
])

def test_calculate_talk_duration(transcript_lines, expected_durations, request):
    lines = request.getfixturevalue(transcript_lines)
    durations = calculate_talk_duration(lines)
    assert durations == expected_durations

@pytest.mark.parametrize("transcript_lines, expected_variations", [
    ("sample_transcript_lines", [
        {
            'speaker': 'interviewer',
            'start_time': 0,
            'end_time': 3000,
            'wpm': 100.0
        },
        {
            'speaker': 'candidate',
            'start_time': 3500,
            'end_time': 7000,
            'wpm': 120.0
        },
        {
            'speaker': 'interviewer',
            'start_time': 7500,
            'end_time': 10000,
            'wpm': 120.0
        }
    ]),
    ("extended_sample_transcript_lines", [
        {
            'speaker': 'interviewer',
            'start_time': 0,
            'end_time': 3000,
            'wpm': 100.0
        },
        {
            'speaker': 'candidate',
            'start_time': 3500,
            'end_time': 7000,
            'wpm': 120.0
        },
        {
            'speaker': 'interviewer',
            'start_time': 7500,
            'end_time': 10000,
            'wpm': 120.0
        },
        {
            'speaker': 'interviewer',
            'start_time': 11000,
            'end_time': 13000,
            'wpm': 210.0
        },
        {
            'speaker': 'candidate',
            'start_time': 14000,
            'end_time': 18000,
            'wpm': 150.0
        }
    ])
])

def test_calculate_speaking_rate_variations(transcript_lines, expected_variations, request):
    lines = request.getfixturevalue(transcript_lines)
    variations = calculate_speaking_rate_variations(lines)
    
    assert len(variations) == len(expected_variations)
    
    for actual, expected in zip(variations, expected_variations):
        assert actual['speaker'] == expected['speaker']
        assert actual['start_time'] == expected['start_time']
        assert actual['end_time'] == expected['end_time']
        assert round(actual['wpm'], 1) == expected['wpm']

@pytest.fixture
def mock_interview(sample_transcript_lines):
    return Interview(
        interview_id=1,
        interview_time=datetime.now(datetime.timezone.utc),
        recall_id='test_bot_id'
    )

def test_update_interview_metrics(sample_data, extended_sample_transcript_lines):
    with flask_app.app_context():
        interview = db.session.get(Interview, sample_data)
        
        # Clear existing transcript lines
        TranscriptLine.query.filter_by(interview_id=interview.interview_id).delete()
        
        # Add new transcript lines
        for line in extended_sample_transcript_lines:
            line.interview_id = interview.interview_id
            db.session.add(line)
        
        db.session.commit()

        update_interview_metrics(interview.interview_id)

        updated_interview = db.session.get(Interview, interview.interview_id)
        assert updated_interview.duration == 18000
        assert updated_interview.speaking_time == 15000
        assert round(updated_interview.wpm, 2) == 136.0
        
        engagement_json = updated_interview.engagement_json
        assert engagement_json['interview_duration'] == 18000
        assert engagement_json['overall_silence_duration'] == 3000
        assert engagement_json['word_count_by_speaker'] == {'interviewer': 17, 'candidate': 17}
        assert engagement_json['silence_duration_by_speaker'] == {'interviewer': 1500, 'candidate': 1500}

def test_engagement_metrics_single_speaker(sample_data):
    with flask_app.app_context():
        interview = db.session.get(Interview, sample_data)
        
        # Clear existing transcript lines
        TranscriptLine.query.filter_by(interview_id=interview.interview_id).delete()
        
        # Add a single transcript line
        transcript_line = TranscriptLine(
            interview_id=interview.interview_id,
            text="This is a test with only one speaker.",
            start=0,
            end=5000,
            confidence=0.95,
            sentiment="neutral",
            speaker="interviewer"
        )
        db.session.add(transcript_line)
        db.session.commit()

        update_interview_metrics(interview.interview_id)

        updated_interview = db.session.get(Interview, interview.interview_id)
        assert updated_interview.duration == 5000
        assert updated_interview.speaking_time == 5000
        assert round(updated_interview.wpm, 2) == 96.0
        
        engagement_json = updated_interview.engagement_json
        assert engagement_json['interview_duration'] == 5000
        assert engagement_json['overall_silence_duration'] == 0
        assert engagement_json['word_count_by_speaker'] == {'interviewer': 8}
        assert engagement_json['silence_duration_by_speaker'] == {}