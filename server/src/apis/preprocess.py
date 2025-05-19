from flask import jsonify, request

from ..app import app
from ..utils import api_error_response, download_and_reupload_file

def preprocess(interview, audio=False, video=False):
    """
    Mocks a call to the preprocessing API, which cleans up audio or video data.
    Args:
        interview: A row in the Interview table, which contains the URLs to the audio and/or video to preprocess.
        audio: Whether or not to preprocess audio data. 
        video: Whether or not to preprocess video data.
    Returns:
        The URLs of the preprocessed audio and video files.
    """
    if not audio and not video:
        # No need to preprocess
        return 

    # Construct data to send to API
    data = {}
    if audio:
        data['audio_url'] = interview.audio_url
    if video:
        data['video_url'] = interview.video_url

    # Make a request to the preprocess API
    # TODO: Replace test implementation with real API call
    with app.test_client() as client:
        response = client.post('/test/preprocess', json=data)

    # Handle response and update Interview object
    if response.status_code == 200:
        interview.audio_url_preprocessed = response.json['audio_url_preprocessed']
        interview.video_url_preprocessed = response.json['video_url_preprocessed']
    else:
        # Handle API error
        print(f"Preprocessing API error: {response.status_code}")

# Temporary implementations of APIs
@app.route('/test/preprocess', methods=['POST'])
def preprocess_media():
    """A mock route to mimic preprocessing.

    Returns:
        A response with preprocessed URLs set in the JSON data
    """
    audio_url = request.json.get('audio_url')
    video_url = request.json.get('video_url')
    
    if not audio_url and not video_url:
        return api_error_response("No URL provided", 400)
    if (audio_url and "s3://" not in audio_url) or (video_url and "s3://" not in video_url):
        return api_error_response("Invalid URL provided", 400)
    
    data = {}
    
    if audio_url:
        audio_output_key = 'file_example_MP3_700KB.mp3'
        data['audio_url_preprocessed'] = download_and_reupload_file(audio_url, audio_output_key)
    
    if video_url:
        video_output_key = 'file_example_MP4_480_1_5MG.mp4'
        data['video_url_preprocessed'] = download_and_reupload_file(video_url, video_output_key)

    if (audio_url and data['audio_url_preprocessed'] is None) or (video_url and data['video_url_preprocessed'] is None):
        return api_error_response("Invalid S3 file", 500)
    
    return jsonify(data), 200