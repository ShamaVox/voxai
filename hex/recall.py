import argparse
import json
import os
import requests
import sys
import time
from typing import Dict, Any, Optional, Tuple

class RecallAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self.get_recall_api_key()
        if not self.api_key:
            raise ValueError("API key is required either via argument or credentials file")
        self.base_url = "https://us-west-2.recall.ai/api"
        
    @staticmethod
    def get_recall_api_key() -> Optional[str]:
        """Gets the recall.ai API key from the credentials file."""
        return os.environ.get("RECALL_API_KEY")

    def get_headers(self) -> Dict[str, str]:
        """Returns headers for the recall.ai API."""
        return {
            'accept': 'application/json',
            'content-type': 'application/json',
            'Authorization': f'Token {self.api_key}'
        }

    def handle_response(self, response: requests.Response) -> Tuple[Dict[str, Any], int]:
        """Handles API response and returns formatted result."""
        if 200 <= response.status_code < 300:
            return response.json(), response.status_code
        else:
            return {"error": response.text}, response.status_code

    def join_meeting(self, meeting_url: str) -> Tuple[Dict[str, Any], int]:
        """Joins and begins recording a meeting."""
        data = {
            'meeting_url': meeting_url,
            'bot_name': 'VoxAI Bot',
            'automatic_leave': {
                'everyone_left_timeout': 150
            },
            'recording_mode': 'speaker_view'
        }
        
        response = requests.post(
            f'{self.base_url}/v1/bot/',
            headers=self.get_headers(),
            json=data
        )
        return self.handle_response(response)

    def get_bot_details(self, bot_id: str) -> Tuple[Optional[dict], int]:
        """
        Retrieves details for a given bot ID, including the video URL and meeting participants.
        If the "meeting_participants" key exists, extract each participant's name and store them
        in the key "meeting_participants_names".
        """
        url = f"{self.base_url}/v1/bot/{bot_id}/"
        response = requests.get(url, headers=self.get_headers())
        if response.status_code == 200:
            try:
                data = response.json()
                # Extract meeting participant names (using the "name" field)
                if "meeting_participants" in data:
                    names = [participant.get("name", "").strip()
                             for participant in data["meeting_participants"]
                             if participant.get("name")]
                    data["meeting_participants_names"] = names
                return data, response.status_code
            except json.JSONDecodeError:
                print(f"Error parsing JSON response: {response.text}", file=sys.stderr)
                return None, response.status_code
        else:
            print(f"Error getting bot details (Status {response.status_code}): {response.text}", file=sys.stderr)
            return None, response.status_code

    def generate_transcript(self, bot_id: str) -> Tuple[Dict[str, Any], int]:
        """Generates a transcript from a recorded meeting."""
        data = {
            'assemblyai_async_transcription': {
                'language_code': 'en_us',
                'speaker_labels': True,
                'disfluencies': True,
                'sentiment_analysis': True,
                'summarization': True,
                'entity_detection': True,
                'iab_categories': True,
            }
        }

        response = requests.post(
            f'{self.base_url}/v2beta/bot/{bot_id}/analyze',
            headers=self.get_headers(),
            json=data
        )
        return response.json(), response.status_code

    def analyze_interview(self, bot_id: str) -> Tuple[Dict[str, Any], int]:
        """Analyzes an interview recording."""
        transcript_response = requests.get(
            f'{self.base_url}/v1/bot/{bot_id}/transcript',
            headers=self.get_headers()
        )
        intelligence_response = requests.get(
            f'{self.base_url}/v1/bot/{bot_id}/intelligence',
            headers=self.get_headers()
        )

        if transcript_response.status_code != 200 or intelligence_response.status_code != 200:
            return {"error": "Failed to retrieve data"}, 500

        intelligence_data = intelligence_response.json()
        summary = intelligence_data.get("assembly_ai.summary", "")
        topics = intelligence_data.get("assembly_ai.iab_categories_result", {}).get("summary", {})
        top_5_topics = dict(sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5])
        
        return {
            "summary": summary,
            "topics": top_5_topics,
            "transcript": transcript_response.json(),
            "intelligence": intelligence_data
        }, 200

    def save_recording(self, bot_id: str) -> Tuple[Dict[str, Any], int]:
        """Retrieves recording information for a specific bot."""
        response = requests.get(
            f'{self.base_url}/v1/bot/{bot_id}/',
            headers=self.get_headers()
        )
        return response.json(), response.status_code

def join_meeting(MEETING_URL: str):
    if MEETING_URL:
        try:
            # Initialize API
            api = RecallAPI()

            # Join the meeting
            response, status_code = api.join_meeting(MEETING_URL)

            if 200 <= status_code < 300:
                print(json.dumps(response, indent=2))
                print("Successfully joined the meeting!")

                # Extract bot ID from the response
                bot_id = response.get("id")
                if bot_id:
                    print(f"Bot ID: {bot_id}")
                else:
                    print("Bot ID not found in the response.", file=sys.stderr)
            else:
                print(
                    f"Error joining meeting (Status {status_code}):",
                    json.dumps(response, indent=2),
                    file=sys.stderr,
                )
        except ValueError as e:
            print(f"Configuration error: {str(e)}")
            print("Please set the environment variable 'RECALL_API_KEY' with your Recall API key.")
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {str(e)}", file=sys.stderr)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {str(e)}", file=sys.stderr)
        except Exception as e:
            print(f"Unexpected error: {str(e)}", file=sys.stderr)
    else:
        print("No meeting URL provided.", file=sys.stderr)

    return bot_id 

def download_video(bot_id: str, video_download_filename: str, refresh_time: int = None):
    """
    Downloads the video for a given bot_id and returns a tuple:
    (path to downloaded video, meeting participants list).
    """
    try:
        api = RecallAPI()
        bot_details, status_code = api.get_bot_details(bot_id)
        if bot_details and 200 <= status_code < 300:
            video_url = None 
            while video_url is None: 
                video_url = bot_details.get("video_url")
                meeting_participants = bot_details.get("meeting_participants_names", [])
                meeting_participants = [participant for participant in meeting_participants if "read.ai" not in participant and "Fireflies.ai" not in participant] # Temporary: hardcode excluding meeting bots
                if video_url:
                    print("Video URL:", video_url)
                    print("Meeting Participants:", meeting_participants)
                    # Download the video
                    print(f"Downloading video to: {video_download_filename}.mp4")
                    video_response = requests.get(video_url, stream=True)
                    video_response.raise_for_status()

                    with open(video_download_filename + ".mp4", "wb") as f:
                        for chunk in video_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"Video downloaded to: {video_download_filename}.mp4")
                    # Return both the video path and meeting participants list.
                    return video_download_filename + ".mp4", meeting_participants
                else:
                    if refresh_time is not None: 
                        print("Video not found on Recall. Waiting ", refresh_time, " seconds to try again in case recording is in progress.")
                        time.sleep(refresh_time)
                    else: 
                        print("Video URL not found in bot details.", file=sys.stderr)
                        break 
        else:
            print(f"Error getting bot details (Status {status_code}).", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {str(e)}", file=sys.stderr)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
    # In case of failure, return None for both.
    return None, []
