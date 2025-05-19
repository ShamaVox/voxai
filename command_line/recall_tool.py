#!/usr/bin/env python3

import argparse
import json
import os
import requests
import sys
from typing import Dict, Any, Optional, Tuple

RECALL_CREDENTIAL_FILEPATH = os.path.expanduser("~/.aws/credentials.json")

class RecallAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self.get_recall_api_key()
        if not self.api_key:
            raise ValueError("API key is required either via argument or credentials file")
        self.base_url = "https://us-west-2.recall.ai/api"
        
    @staticmethod
    def get_recall_api_key() -> Optional[str]:
        """Gets the recall.ai API key from the credentials file."""
        try:
            with open(RECALL_CREDENTIAL_FILEPATH) as f:
                credentials = json.load(f)
            return credentials["recall_api_key"]
        except (FileNotFoundError, KeyError):
            return None

    def get_headers(self) -> Dict[str, str]:
        """Returns headers for the recall.ai API."""
        return {
            'accept': 'application/json',
            'content-type': 'application/json',
            'Authorization': f'Token {self.api_key}'
        }

    def handle_response(self, response: requests.Response) -> Tuple[Dict[str, Any], int]:
        """Handles API response and returns formatted result."""
        if response.status_code >= 200 and response.status_code < 300:
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

    def generate_transcript(self, bot_id: str) -> Dict[str, Any]:
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

    def analyze_interview(self, bot_id: str) -> Dict[str, Any]:
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

    def save_recording(self, bot_id: str) -> Dict[str, Any]:
        """Retrieves recording information for a specific bot."""
        response = requests.get(
            f'{self.base_url}/v1/bot/{bot_id}/',
            headers=self.get_headers()
        )
        return response.json(), response.status_code

def main():
    global RECALL_CREDENTIAL_FILEPATH
    parser = argparse.ArgumentParser(description='Recall.ai API Command Line Tool')
    parser.add_argument('--api-key', help='Your Recall.ai API key (optional if using credentials file)')
    parser.add_argument('--credentials-file', help='Path to credentials file', default=RECALL_CREDENTIAL_FILEPATH)
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Join meeting command
    join_parser = subparsers.add_parser('join', help='Join a meeting')
    join_parser.add_argument('--url', required=True, help='Meeting URL to join')

    # Generate transcript command
    transcript_parser = subparsers.add_parser('transcript', help='Generate transcript')
    transcript_parser.add_argument('--bot-id', required=True, help='Bot ID for the recording')

    # Analyze interview command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze interview')
    analyze_parser.add_argument('--bot-id', required=True, help='Bot ID for the recording')

    # Save recording command
    save_parser = subparsers.add_parser('save', help='Save recording')
    save_parser.add_argument('--bot-id', required=True, help='Bot ID for the recording')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Update credentials file path if provided
    RECALL_CREDENTIAL_FILEPATH = args.credentials_file

    try:
        # Initialize API with either provided key or from credentials file
        api = RecallAPI(args.api_key)

        if args.command == 'join':
            response, status_code = api.join_meeting(args.url)
        elif args.command == 'transcript':
            response, status_code = api.generate_transcript(args.bot_id)
        elif args.command == 'analyze':
            response, status_code = api.analyze_interview(args.bot_id)
        elif args.command == 'save':
            response, status_code = api.save_recording(args.bot_id)

        if status_code >= 200 and status_code < 300:
            print(json.dumps(response, indent=2))
            sys.exit(0)
        else:
            print(f"Error (Status {status_code}):", json.dumps(response, indent=2), file=sys.stderr)
            sys.exit(1)

    except ValueError as e:
        print(f"Configuration error: {str(e)}", file=sys.stderr)
        print("\nPlease either:", file=sys.stderr)
        print("1. Provide an API key using --api-key", file=sys.stderr)
        print(f"2. Create a credentials file at {RECALL_CREDENTIAL_FILEPATH} with format:", file=sys.stderr)
        print('   {"recall_api_key": "your-api-key-here"}', file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()