import os
import pytest
import subprocess # Import subprocess
from unittest.mock import patch, MagicMock
# Removed Path import
import media_processing
# Get paths as strings from fixture patching config
from config import TEMP_FOLDER, FFMPEG_BITRATE, FFMPEG_SAMPLE_RATE, FFMPEG_CHANNELS, S3_BUCKET

# Use fixtures from conftest.py: temp_folders, mock_boto3_s3, mock_subprocess

# --- Test convert_to_mp3 ---

def test_convert_to_mp3_ffmpeg_not_found(temp_folders, mock_subprocess):
    """Test handling when ffmpeg command is not found."""
    mock_popen, mock_proc = mock_subprocess
    # Simulate FileNotFoundError when calling Popen
    mock_popen.side_effect = FileNotFoundError("ffmpeg not found")

    video_file = os.path.join(TEMP_FOLDER, "nofmpeg_video.mp4")
    with open(video_file, 'w') as f: f.write('video')

    result_path = media_processing.convert_to_mp3(video_file)

    assert result_path is None
    mock_popen.assert_called_once() # Popen was called, but raised error
    mock_proc.communicate.assert_not_called()

def test_convert_to_mp3_input_file_not_found(temp_folders):
    """Test when the input video file doesn't exist."""
    # No need to mock subprocess as it shouldn't be called
    result_path = media_processing.convert_to_mp3(os.path.join(TEMP_FOLDER, "nonexistent.mp4"))
    assert result_path is None

def test_convert_to_mp3_already_exists(temp_folders, mock_subprocess):
    """Test skipping conversion if MP3 file already exists."""
    mock_popen, mock_proc = mock_subprocess

    video_file = os.path.join(TEMP_FOLDER, "existing.mp4")
    mp3_file = os.path.join(TEMP_FOLDER, "existing.mp3")
    with open(video_file, 'w') as f: f.write('video')
    with open(mp3_file, 'w') as f: f.write('audio') # Create dummy mp3 file

    result_path = media_processing.convert_to_mp3(video_file)

    assert result_path == mp3_file
    mock_popen.assert_not_called() # Should not call ffmpeg

# --- Test upload_to_s3 ---

def test_upload_to_s3_success(temp_folders, mock_boto3_s3):
    """Test successful upload to S3."""
    local_file = os.path.join(TEMP_FOLDER, "upload_me.mp3")
    with open(local_file, 'w') as f: f.write("audio data")
    s3_key = "user/meeting/recording.mp3"
    content_type = 'audio/mpeg'

    s3_url = media_processing.upload_to_s3(local_file, s3_key, content_type)

    expected_s3_url = f"s3://{S3_BUCKET}/{s3_key}"
    assert s3_url == expected_s3_url
    # Check that the S3 client's upload_file method was called correctly
    mock_boto3_s3.upload_file.assert_called_once_with(
        local_file,
        S3_BUCKET,
        s3_key,
        ExtraArgs={'ContentType': content_type}
    )

def test_upload_to_s3_no_bucket(temp_folders, monkeypatch):
    """Test upload failure when S3_BUCKET is not set."""
    monkeypatch.setattr(media_processing, 'S3_BUCKET', None)
    local_file = os.path.join(TEMP_FOLDER, "upload_me.mp3")
    with open(local_file, 'w') as f: f.write('audio')
    s3_url = media_processing.upload_to_s3(local_file, "key", 'audio/mpeg')
    assert s3_url is None

def test_upload_to_s3_file_not_found(temp_folders, mock_boto3_s3):
    """Test upload failure when local file doesn't exist."""
    s3_url = media_processing.upload_to_s3(os.path.join(TEMP_FOLDER, "not_here.mp3"), "key", 'audio/mpeg')
    assert s3_url is None
    mock_boto3_s3.upload_file.assert_not_called()

def test_upload_to_s3_boto_error(temp_folders, mock_boto3_s3):
    """Test handling of Boto3 client errors during upload."""
    from botocore.exceptions import ClientError
    mock_boto3_s3.upload_file.side_effect = ClientError({'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}}, 'UploadFile')

    local_file = os.path.join(TEMP_FOLDER, "upload_fail.mp3")
    with open(local_file, 'w') as f: f.write('audio')
    s3_url = media_processing.upload_to_s3(local_file, "key", 'audio/mpeg')

    assert s3_url is None
    mock_boto3_s3.upload_file.assert_called_once()

# --- Test file_exists_in_s3 ---

def test_file_exists_in_s3_true(mock_boto3_s3):
    """Test checking when file exists."""
    s3_key = "user/meeting/exists.mp3"
    # Configure mock to return content for the specific key
    mock_boto3_s3.list_objects_v2.return_value = {
        'Contents': [{'Key': s3_key, 'Size': 100}],
        'ResponseMetadata': {'HTTPStatusCode': 200}
    }

    exists = media_processing.file_exists_in_s3(s3_key)

    assert exists is True
    mock_boto3_s3.list_objects_v2.assert_called_once_with(
        Bucket=S3_BUCKET, Prefix=s3_key, MaxKeys=1
    )

def test_file_exists_in_s3_false(mock_boto3_s3):
    """Test checking when file does not exist."""
    s3_key = "user/meeting/not_exists.mp3"
    # Configure mock to return empty contents
    mock_boto3_s3.list_objects_v2.return_value = {
         'ResponseMetadata': {'HTTPStatusCode': 200} # No 'Contents' key
    }

    exists = media_processing.file_exists_in_s3(s3_key)
    assert exists is False
    mock_boto3_s3.list_objects_v2.assert_called_once_with(
        Bucket=S3_BUCKET, Prefix=s3_key, MaxKeys=1
    )

def test_file_exists_in_s3_prefix_mismatch(mock_boto3_s3):
    """Test checking when list_objects returns a different key with the same prefix."""
    s3_key = "user/meeting/data.json"
    prefix_match_key = "user/meeting/data.json.backup"
    mock_boto3_s3.list_objects_v2.return_value = {
        'Contents': [{'Key': prefix_match_key, 'Size': 100}], # Key doesn't match exactly
        'ResponseMetadata': {'HTTPStatusCode': 200}
    }

    exists = media_processing.file_exists_in_s3(s3_key)
    assert exists is False # Should be false because the exact key was not found
    mock_boto3_s3.list_objects_v2.assert_called_once_with(
        Bucket=S3_BUCKET, Prefix=s3_key, MaxKeys=1
    )


def test_file_exists_in_s3_no_bucket(monkeypatch):
    """Test checking when S3_BUCKET is not set."""
    monkeypatch.setattr(media_processing, 'S3_BUCKET', None)
    exists = media_processing.file_exists_in_s3("key")
    assert exists is False

def test_file_exists_in_s3_boto_error(mock_boto3_s3):
    """Test handling Boto3 errors during check."""
    from botocore.exceptions import ClientError
    mock_boto3_s3.list_objects_v2.side_effect = ClientError({'Error': {'Code': 'InternalError', 'Message': 'Error'}}, 'ListObjectsV2')
    exists = media_processing.file_exists_in_s3("key")
    assert exists is False # Assume not found on error
    mock_boto3_s3.list_objects_v2.assert_called_once()

# --- Test cleanup_temp_files ---

def test_cleanup_temp_files(temp_folders):
    """Test deleting temporary files."""
    file1 = os.path.join(TEMP_FOLDER, "file1.txt")
    file2 = os.path.join(TEMP_FOLDER, "file2.mp4")
    subdir = os.path.join(TEMP_FOLDER, "subdir")
    file3 = os.path.join(subdir, "file3.json")

    with open(file1, 'w') as f: f.write('1')
    with open(file2, 'w') as f: f.write('2')
    os.makedirs(subdir, exist_ok=True)
    with open(file3, 'w') as f: f.write('3')


    assert os.path.exists(file1)
    assert os.path.exists(file2)
    assert os.path.exists(file3)

    media_processing.cleanup_temp_files(file1, file2, file3, None, "nonexistent_file")

    assert not os.path.exists(file1)
    assert not os.path.exists(file2)
    assert not os.path.exists(file3)

def test_cleanup_temp_files_error(temp_folders, mocker):
    """Test that cleanup continues even if one file removal fails."""
    file1 = os.path.join(TEMP_FOLDER, "file_a.txt")
    file2 = os.path.join(TEMP_FOLDER, "file_b.txt") # This one will fail
    file3 = os.path.join(TEMP_FOLDER, "file_c.txt")

    with open(file1, 'w') as f: f.write('a')
    with open(file2, 'w') as f: f.write('b')
    with open(file3, 'w') as f: f.write('c')

    # Mock os.remove to raise error only for file2
    original_remove = os.remove
    def mock_remove(path):
        if path == file2:
            raise OSError("Permission denied")
        else:
            # Ensure path exists before calling original remove
            if os.path.exists(path):
                 original_remove(path)
    mocker.patch('os.remove', side_effect=mock_remove)

    media_processing.cleanup_temp_files(file1, file2, file3)

    assert not os.path.exists(file1) # Should be removed
    assert os.path.exists(file2)     # Should still exist due to error
    assert not os.path.exists(file3) # Should be removed
