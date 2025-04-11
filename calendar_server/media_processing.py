import os
import subprocess
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
# Use TEMP_FOLDER directly from config
from config import TEMP_FOLDER, FFMPEG_BITRATE, FFMPEG_SAMPLE_RATE, FFMPEG_CHANNELS, S3_BUCKET

def convert_to_mp3(video_path: str) -> str | None:
    """Convert video file (e.g., MP4) to MP3 using ffmpeg."""
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return None

    mp3_path = os.path.splitext(video_path)[0] + '.mp3'

    # Check if MP3 already exists
    if os.path.exists(mp3_path):
        print(f"MP3 file already exists at {mp3_path}, skipping conversion.")
        return mp3_path

    print(f"Converting {video_path} to MP3...")
    command = [
        'ffmpeg',
        '-i', video_path,
        '-vn',  # Disable video recording
        '-ar', FFMPEG_SAMPLE_RATE, # Audio sample rate
        '-ac', str(FFMPEG_CHANNELS), # Audio channels (needs to be string)
        '-b:a', FFMPEG_BITRATE, # Audio bitrate
        '-f', 'mp3',  # Output format
        '-y', # Overwrite output file if it exists (safety)
        mp3_path
    ]

    try:
        # Use subprocess.PIPE directly
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f"Error converting video to MP3 (ffmpeg exit code {process.returncode}):")
            print(f"FFmpeg stderr: {stderr.decode(errors='ignore')}")
            # Clean up potentially corrupted output file only if it exists
            if os.path.exists(mp3_path):
                try:
                    os.remove(mp3_path)
                    print(f"Removed potentially corrupted output file: {mp3_path}")
                except OSError as e:
                    print(f"Warning: Failed to remove corrupted output file {mp3_path}: {e}")
            return None
        else:
            print(f"Successfully converted video to MP3: {mp3_path}")
            # Verify file exists after successful conversion before returning path
            if os.path.exists(mp3_path):
                return mp3_path
            else:
                print(f"Error: ffmpeg reported success, but output file not found: {mp3_path}")
                return None

    except FileNotFoundError:
        print("Error: 'ffmpeg' command not found. Make sure ffmpeg is installed and in your system's PATH.")
        return None
    except Exception as e:
        print(f"Unexpected error during ffmpeg conversion: {str(e)}")
        # Attempt cleanup on unexpected error too
        if os.path.exists(mp3_path):
            try:
                os.remove(mp3_path)
            except OSError: pass # Ignore cleanup error
        return None


def upload_to_s3(file_path: str, s3_key: str, content_type: str = 'application/octet-stream') -> str | None:
    """Upload a file to the configured S3 bucket."""
    if not S3_BUCKET:
        print("Error: S3_BUCKET environment variable is not set. Cannot upload.")
        return None
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}. Cannot upload to S3.")
        return None

    s3_client = boto3.client('s3')
    print(f"Uploading {file_path} to s3://{S3_BUCKET}/{s3_key}...")

    try:
        s3_client.upload_file(
            file_path,
            S3_BUCKET,
            s3_key,
            ExtraArgs={'ContentType': content_type}
        )
        s3_url = f"s3://{S3_BUCKET}/{s3_key}"
        print(f"Successfully uploaded to {s3_url}")
        return s3_url

    except (NoCredentialsError, PartialCredentialsError):
        print("Error: AWS credentials not found. Configure credentials (e.g., via environment variables, IAM role).")
        return None
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        print(f"Error uploading to S3 (Code: {error_code}): {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error during S3 upload: {str(e)}")
        return None


def file_exists_in_s3(s3_key: str) -> bool:
    """Check if a file exists in the configured S3 bucket."""
    if not S3_BUCKET:
        print("Warning: S3_BUCKET not set, cannot check for file existence.")
        return False

    s3_client = boto3.client('s3')
    try:
        # Use list_objects_v2 for efficiency, checking only for the specific key
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=s3_key,
            MaxKeys=1
        )
        # Check if 'Contents' exists and is not empty, AND if the key matches exactly
        # (Prefix match isn't enough if s3_key is like a directory prefix)
        if 'Contents' in response and len(response['Contents']) > 0:
             # Ensure the found key is exactly the one we're looking for
             return response['Contents'][0].get('Key') == s3_key
        return False
    except (NoCredentialsError, PartialCredentialsError):
        print("Warning: AWS credentials not found. Cannot check S3.")
        return False # Assume file doesn't exist if we can't check
    except ClientError as e:
        # Handle common errors like NoSuchBucket gracefully
        if e.response['Error']['Code'] == 'NoSuchBucket':
            print(f"Error: S3 bucket '{S3_BUCKET}' does not exist.")
        else:
            print(f"Error checking S3 for file {s3_key}: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error checking S3 for file {s3_key}: {str(e)}")
        return False

def cleanup_temp_files(*file_paths: str):
    """Remove files from the temporary directory."""
    for file_path in file_paths:
        # Check if path is not None and exists before attempting removal
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Cleaned up temporary file: {file_path}")
            except OSError as e:
                print(f"Error removing temporary file {file_path}: {e}")
        # Optionally log if file_path was None or didn't exist?
        # else:
        #     if file_path:
        #         print(f"Cleanup skipped: File not found at {file_path}")
