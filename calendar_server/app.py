from flask import Flask, request, jsonify
import threading
import time
import os
import logging

# Configuration flags
REALTIME_TRANSCRIPTION = False  # Set to True for real-time transcription, False for post-meeting

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Dictionary to track active meetings
active_meetings = {}

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """
    Flask route that handles incoming webhook notifications from Google Calendar.
    
    Expected payload includes meeting details like:
    - meeting_id
    - start_time
    - organizer
    - meeting_link
    
    Returns:
        JSON response confirming receipt of webhook data
    """
    try:
        # Extract webhook data from request
        webhook_data = request.get_json()
        
        # Process the webhook data
        respond_to_webhook(webhook_data)
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def respond_to_webhook(webhook_data):
    """
    Process webhook notifications from Google Calendar about upcoming meetings.
    
    Args:
        webhook_data: JSON data containing meeting details
    """
    try:
        # Extract meeting information
        meeting_id = webhook_data.get('meeting_id')
        meeting_link = webhook_data.get('meeting_link')
        
        logger.info(f"Received webhook for meeting: {meeting_id}")
        
        # Validate meeting data
        if not meeting_id or not meeting_link:
            logger.error("Invalid meeting data received")
            return
        
        # Start transcription process in a background thread
        transcription_thread = threading.Thread(
            target=transcribe_meeting,
            args=(meeting_id, meeting_link),
            daemon=True
        )
        transcription_thread.start()
        
        # Track the meeting in our active meetings dictionary
        # Need this for duplicate detection if we have multiple users in the same call
        active_meetings[meeting_id] = {
            'thread': transcription_thread,
            'start_time': time.time(),
            'link': meeting_link,
            'status': 'started'
        }
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")

def transcribe_meeting(meeting_id, meeting_link, output_location=None):
    """
    Coordinate the transcription process for a meeting.
    
    Args:
        meeting_id: Unique identifier for the meeting
        meeting_link: URL to join the meeting
        output_location: Where to save the transcript (defaults to meeting_id.txt)
    """
    try:
        if output_location is None:
            output_location = f"transcripts/{meeting_id}.txt"
            
        # Ensure the transcripts directory exists
        os.makedirs(os.path.dirname(output_location), exist_ok=True)
        
        logger.info(f"Starting transcription for meeting {meeting_id}")
        
        # Join the meeting using browser automation (not implemented here)
        # TODO: Implement browser automation to join the meeting
        
        # Choose transcription method based on configuration
        if REALTIME_TRANSCRIPTION:
            get_transcription_realtime(meeting_id, output_location)
        else:
            # Start a background process to monitor the meeting
            query_ongoing_call(meeting_id, output_location)
            
        logger.info(f"Transcription complete for meeting {meeting_id}")
        
        # Update meeting status
        if meeting_id in active_meetings:
            active_meetings[meeting_id]['status'] = 'completed'
            
    except Exception as e:
        logger.error(f"Error transcribing meeting {meeting_id}: {str(e)}")
        if meeting_id in active_meetings:
            active_meetings[meeting_id]['status'] = 'error'
            active_meetings[meeting_id]['error'] = str(e)

def get_transcription_realtime(meeting_id, output_location):
    """
    Handle real-time transcription by processing audio stream during the meeting.
    
    Args:
        meeting_id: Unique identifier for the meeting
        output_location: Where to save the transcript
    """
    # TODO: Not planning to have this fully functional in the short term, but the goal is to set up a skeleton that calls the Google audio stream API so we can implement realtime transcription easily later
    try:
        logger.info(f"Starting real-time transcription for meeting {meeting_id}")
        
        # Initialize transcript file
        with open(output_location, 'w') as f:
            f.write(f"Meeting ID: {meeting_id}\n")
            f.write(f"Transcript started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Set up real-time audio capture (not implemented here)
        # TODO: Implement audio capture from meeting
        
        # Loop to continuously process audio chunks
        meeting_active = True
        while meeting_active:
            # TODO: Get audio chunk
            # TODO: Send to speech-to-text API
            # TODO: Process response
            
            # Placeholder for chunk processing
            # new_text = process_audio_chunk(audio_chunk)
            
            # Append new text to transcript
            # with open(output_location, 'a') as f:
            #     f.write(new_text + "\n")
            
            # Check if meeting is still active
            # meeting_active = check_if_meeting_still_active(meeting_id)
            
            # Placeholder implementation
            # Google may send audio as a webhook rather than needing to manually query it and sleep 
            time.sleep(5)
            meeting_active = False  # TODO: Check if meeting is ended
        
        logger.info(f"Real-time transcription completed for meeting {meeting_id}")
            
    except Exception as e:
        logger.error(f"Error in real-time transcription for meeting {meeting_id}: {str(e)}")

def query_ongoing_call(meeting_id, output_location):
    """
    Periodically check if a meeting is still active,
    then trigger full transcription once complete.
    
    Args:
        meeting_id: Unique identifier for the meeting
        output_location: Where to save the transcript
    """
    try:
        logger.info(f"Starting meeting monitoring for {meeting_id}")
        
        meeting_active = True
        check_interval = 20 * 60  # Check every 20 minutes
        
        # Loop to periodically check if meeting is still active
        while meeting_active:
            # TODO: Implement actual meeting status check
            # We can do this with Recall but may want to use the Google API instead
            
            logger.info(f"Checking status of meeting {meeting_id}")
            
            # Placeholder implementation
            time.sleep(check_interval)
            meeting_active = False  # This would normally check meeting status
        
        # Once meeting is complete, get full transcription
        logger.info(f"Meeting {meeting_id} has ended, starting full transcription")
        get_transcription_full(meeting_id, output_location)
        
    except Exception as e:
        logger.error(f"Error monitoring meeting {meeting_id}: {str(e)}")

def get_transcription_full(meeting_id, output_location):
    """
    Process the entire meeting recording to generate a full transcript.
    Called after a meeting has ended.
    
    Args:
        meeting_id: Unique identifier for the meeting
        output_location: Where to save the transcript
    """
    # TODO: Option to save audio file as well 
    try:
        logger.info(f"Starting full transcription for meeting {meeting_id}")
        
        # TODO: Get meeting recording
        # TODO: Send to speech-to-text API for full processing
            # We can adapt existing Gemini code here
        # TODO: Format and save transcript
        
        # Placeholder for full transcript processing
        with open(output_location, 'w') as f:
            f.write(f"Meeting ID: {meeting_id}\n")
            f.write(f"Full transcript processed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("Placeholder for full meeting transcript\n")
        
        logger.info(f"Full transcription completed for meeting {meeting_id}")
        
    except Exception as e:
        logger.error(f"Error in full transcription for meeting {meeting_id}: {str(e)}")

@app.route('/status', methods=['GET'])
def get_status():
    """
    API endpoint to check the status of the transcription service
    and any active meetings.
    
    Returns:
        JSON with service status and active meetings information
    """
    return jsonify({
        "status": "running",
        "active_meetings": len(active_meetings),
        "transcription_mode": "real-time" if REALTIME_TRANSCRIPTION else "post-meeting"
    })

if __name__ == '__main__':
    # Start the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)