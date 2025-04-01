import os
import ffmpeg

def convert_mp4_to_mp3(input_file, output_file):
    # Check if input file exists
    if not os.path.isfile(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        return False

    try:
        # Open the input file
        stream = ffmpeg.input(input_file)

        # Extract audio and convert to MP3
        audio = stream.audio
        output = ffmpeg.output(audio, output_file, acodec='libmp3lame', audio_bitrate='192k')

        # Run the conversion
        ffmpeg.run(output, overwrite_output=True)

        print(f"Successfully converted '{input_file}' to '{output_file}'")
        return True
    except ffmpeg.Error as e:
        print(f"Error during conversion: {e.stderr.decode()}")
        return False