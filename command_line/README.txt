The recall command line tool can be used to start Recall recordings, start a Recall analysis job, without running the rest of the server. The functionality is identical to that provided by the server.

Join a meeting with a credentials file in ~/.aws/credentials.json:

    ./recall_tool.py join --url "https://zoom.us/j/123456789"

Join a meeting with a credentials file in a custom location:

    ./recall_tool.py --credentials-file /path/to/your/credentials.json join --url "https://zoom.us/j/123456789"

Join a meeting by manually specifying the API key:

    ./recall_tool.py --api-key YOUR_API_KEY join --url "https://zoom.us/j/123456789"

Start the job to analyze and transcribe a meeting recording:

    ./recall_tool.py analyze --bot-id 5a3d01eb-8729-4978-b613-346ae10f83cb

View the analysis of a meeting:

    ./recall_tool.py analyze --bot-id 5a3d01eb-8729-4978-b613-346ae10f83cb

Save the meeting recordings to AWS:

    ./recall_tool.py save --bot-id 5a3d01eb-8729-4978-b613-346ae10f83cb
