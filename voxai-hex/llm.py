import json
from json.decoder import JSONDecodeError
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import MessagesPlaceholder
import time

# -----------------------------------------------------------------------------
# CONFIGURATION CLASS
# -----------------------------------------------------------------------------

class LLMConfig:
    def __init__(self,
                 # Transcription config
                 SPLIT_LINES_AT_SENTENCES=True,
                 TRANSCRIBE_AUDIO=True,
                 TRANSCRIBE_SENTIMENT=True,
                 TRANSCRIBE_ENGAGEMENT=True,
                 TRANSCRIBE_EMOTIONS=False,
                 EMOTION_TYPES=None,
                 TRANSCRIBE_TOPICS=True,
                 # Skill analysis config
                 RUN_SKILL_ANALYSES=True,
                 SKILL_TYPES=None,
                 SKILLS_FROM_TRANSCRIPT=True,
                 SKILLS_FROM_AUDIO=False,
                 # Insights config
                 RUN_SENTIMENT_INSIGHTS=True,
                 RUN_ENGAGEMENT_INSIGHTS=True, 
                 # LLM config
                 TRANSCRIPTION_MODEL_NAME="gemini-2.0-flash-exp",
                 ANALYSIS_MODEL_NAME="gemini-2.0-flash-exp",
                 TEMPERATURE=None,  # If None, default to 0.7 in our function.
                 MAX_ITERATIONS=8,
                 USE_AUDIO_FOR_ANALYSIS=False,
                 TRACK_RATE_LIMIT=True,
                 RATE_LIMIT_MESSAGES=9,
                 RATE_LIMIT_SECONDS=70):
        # Transcription settings
        self.SPLIT_LINES_AT_SENTENCES = SPLIT_LINES_AT_SENTENCES
        self.TRANSCRIBE_AUDIO = TRANSCRIBE_AUDIO
        self.TRANSCRIBE_SENTIMENT = TRANSCRIBE_SENTIMENT
        self.TRANSCRIBE_ENGAGEMENT = TRANSCRIBE_ENGAGEMENT
        self.TRANSCRIBE_EMOTIONS = TRANSCRIBE_EMOTIONS
        self.EMOTION_TYPES = EMOTION_TYPES or [
            "Happiness", "Sadness", "Surprise", "Anger", "Frustration",
            "Excitement", "Calmness", "Confusion"
        ]
        self.TRANSCRIBE_TOPICS = TRANSCRIBE_TOPICS
        # For backwards compatibility if needed
        self.TRANSCRIBE_ATTRIBUTES = (self.TRANSCRIBE_SENTIMENT or 
                                      self.TRANSCRIBE_ENGAGEMENT or 
                                      self.TRANSCRIBE_EMOTIONS or 
                                      self.TRANSCRIBE_TOPICS)
        # Skill analysis settings
        self.RUN_SKILL_ANALYSES = RUN_SKILL_ANALYSES
        self.SKILL_TYPES = SKILL_TYPES or [
            "Communication & Clarity",
            "Growth Mindset",
            "Adapability"
        ]
        self.SKILLS_FROM_TRANSCRIPT = SKILLS_FROM_TRANSCRIPT
        self.SKILLS_FROM_AUDIO = SKILLS_FROM_AUDIO
        self.RUN_SENTIMENT_INSIGHTS = RUN_SENTIMENT_INSIGHTS
        self.RUN_ENGAGEMENT_INSIGHTS = RUN_ENGAGEMENT_INSIGHTS
        # LLM settings
        self.TRANSCRIPTION_MODEL_NAME = TRANSCRIPTION_MODEL_NAME
        self.ANALYSIS_MODEL_NAME = ANALYSIS_MODEL_NAME
        self.TEMPERATURE = TEMPERATURE if TEMPERATURE is not None else 0.7
        self.MAX_ITERATIONS = MAX_ITERATIONS
        self.USE_AUDIO_FOR_ANALYSIS = USE_AUDIO_FOR_ANALYSIS
        self.TRACK_RATE_LIMIT = TRACK_RATE_LIMIT
        self.RATE_LIMIT_MESSAGES = RATE_LIMIT_MESSAGES
        self.RATE_LIMIT_SECONDS = RATE_LIMIT_SECONDS


# -----------------------------------------------------------------------------
# PREVENT RATE LIMITING
# -----------------------------------------------------------------------------

# Global variables to track LLM call count and timestamp.
LLM_CALL_TIMESTAMPS = []

def track_llm_call(config):
    """
    Tracks LLM calls using a sliding window.
    If the number of calls in the past config.RATE_LIMIT_SECONDS is greater than or equal to
    config.RATE_LIMIT_MESSAGES, it waits until the oldest call is outside the window.
    """
    global LLM_CALL_TIMESTAMPS
    now = time.time()
    
    # Remove any timestamps older than RATE_LIMIT_SECONDS ago.
    LLM_CALL_TIMESTAMPS = [t for t in LLM_CALL_TIMESTAMPS if now - t < config.RATE_LIMIT_SECONDS]
    print("LLM call made. Timestamps: ", LLM_CALL_TIMESTAMPS)
    print("Number of calls in list: ", len(LLM_CALL_TIMESTAMPS))
    
    if len(LLM_CALL_TIMESTAMPS) >= config.RATE_LIMIT_MESSAGES:
        # Calculate how much time to wait until the oldest call is older than RATE_LIMIT_SECONDS.
        oldest = LLM_CALL_TIMESTAMPS[0]
        wait_time = config.RATE_LIMIT_SECONDS - (now - oldest)
        if wait_time > 0:
            print(f"Rate limit reached: waiting for {wait_time:.1f} seconds")
            time.sleep(wait_time)
            now = time.time()
            # Clean up the timestamps again after waiting.
            LLM_CALL_TIMESTAMPS = [t for t in LLM_CALL_TIMESTAMPS if now - t < config.RATE_LIMIT_SECONDS]
    
    # Record the current call's timestamp.
    LLM_CALL_TIMESTAMPS.append(time.time())

# -----------------------------------------------------------------------------
# LLM HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def get_llm(config: LLMConfig, mode: str = "transcription", stop_sequences=None):
    """
    Returns an LLM instance configured based on the provided configuration.
    :param mode: "transcription" or "analysis" to select the appropriate model.
    """
    model = config.TRANSCRIPTION_MODEL_NAME if mode == "transcription" else config.ANALYSIS_MODEL_NAME
    params = {
        "model": model,
        "temperature": config.TEMPERATURE,
        "maxOutputTokens": 8192,  # For example, Gemini Flash max tokens
    }
    if stop_sequences:
        return ChatGoogleGenerativeAI(**params, stop_sequences=stop_sequences)
    return ChatGoogleGenerativeAI(**params)

def fix_json(llm, invalid_json: str, error_message: str) -> str:
    """Attempts to fix invalid JSON using another LLM call."""
    fix_json_template = """
    You are a helpful AI that only responds in valid JSON. 
    The following JSON string you generated previously is invalid:

    ```json
    {invalid_json}
    ```

    The error message is:

    ```
    {error_message}
    ```

    Please provide the corrected JSON. Do not output anything besides valid JSON.
    """
    fix_json_prompt = PromptTemplate(
        input_variables=["invalid_json", "error_message"], template=fix_json_template
    )
    fix_json_chain = LLMChain(llm=llm, prompt=fix_json_prompt)
    corrected_json = fix_json_chain.run(
        invalid_json=invalid_json, error_message=error_message
    )
    return corrected_json

def clean_json_markdown(json_with_markdown):
    json_with_markdown = json_with_markdown.strip()
    if json_with_markdown.startswith("```json"):
        json_with_markdown = json_with_markdown[7:]
    if json_with_markdown.endswith("```"):
        json_with_markdown = json_with_markdown[:-3]
    json_with_markdown = json_with_markdown.replace("```json", "").strip()
    return json_with_markdown

def parse_json_with_fixing(llm, response):
    """Parses JSON; if invalid, attempts to fix it using the LLM."""
    if not isinstance(response, str):
        return response  # Already parsed.
    try:
        return json.loads(response)
    except JSONDecodeError as e:
        print(f"Invalid JSON encountered: {e}")
        print("Attempting to fix...")
        try:
            fixed_json = fix_json(llm, response, str(e))
            fixed_json = clean_json_markdown(fixed_json)
            return json.loads(fixed_json)
        except JSONDecodeError as e2:
            print(f"Failed to fix JSON: {e2}")
            return None

def parse_speaker_mapping(response: str) -> dict:
    """
    Parse the LLM response to extract the JSON mapping from speaker labels
    to names. It finds the separator line (---), then extracts all text that
    follows (up to the stop token [DONE]). If parsing fails, it returns an empty dict.
    """
    # Split the response into lines
    lines = response.splitlines()
    separator_index = None

    # Find the line that contains only '---'
    for idx, line in enumerate(lines):
        if line.strip() == '---':
            separator_index = idx
            break

    if separator_index is None:
        print("Separator '---' not found in response.")
        return {}

    # Join everything after the separator as candidate JSON text.
    json_lines = lines[separator_index + 1:]
    json_text = "\n".join(json_lines)

    # Remove the stop sequence [DONE] if present.
    if "[DONE]" in json_text:
        json_text = json_text.split("[DONE]")[0].strip()

    try:
        mapping = json.loads(json_text)
        return mapping
    except json.JSONDecodeError as e:
        print("Invalid JSON encountered:", e)
        # Optionally: implement a JSON-fixing procedure here.
        # For now, we return an empty dict.
        return {}

def run_with_iterations(llm, base_messages, config):
    """
    Runs the LLM with iterations until a stop sequence is encountered.
    Accumulates JSON output from successive calls.
    """
    STOP_SEQUENCE = "[DONE]"
    accumulated_json = ""
    
    for iteration in range(config.MAX_ITERATIONS):
        # Create a new messages list for each iteration
        current_messages = base_messages.copy()
        
        # If there is accumulated JSON, add it as additional context
        if accumulated_json:
            current_messages.append(AIMessage(content=accumulated_json))
            
        template = ChatPromptTemplate.from_messages(current_messages)
        formatted_messages = template.format_messages(chat_history=[])
        
        track_llm_call(config)
        response = llm.invoke(formatted_messages)
        # Handle different response object types
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Check for the stop sequence
        if STOP_SEQUENCE in response_text:
            response_text = response_text.replace(STOP_SEQUENCE, "").strip()
            if response_text:
                accumulated_json += response_text
            break
        else:
            accumulated_json += response_text
    
    # Clean up any markdown code block formatting
    accumulated_json = clean_json_markdown(accumulated_json)
    
    return accumulated_json

# -----------------------------------------------------------------------------
# TRANSCRIPTION & ANALYSIS FUNCTIONS
# -----------------------------------------------------------------------------

def run_transcription(llm, audio_filename: str, config: LLMConfig = None, meeting_participants: list = None):
    """
    Runs the transcription chain with audio input and JSON fixing.
    If meeting_participants is provided, adds that information to the prompt.
    """
    STOP_SEQUENCE = "[DONE]"
    
    # Build additional instructions regarding meeting participants.
    participants_text = ""
    if meeting_participants:
        participants_text = (
            f"\nMeeting Participants: {', '.join(meeting_participants)}. "
            "Note that not every participant necessarily speaks and some may be bots. However, this may be helpful to identify the number of speakers."
        )
    
    attributes_list = []
    if config.SPLIT_LINES_AT_SENTENCES: 
        attributes_list.append("- Include a separate JSON entry for each sentence.")
    if config.TRANSCRIBE_SENTIMENT:
        attributes_list.append("- Include a 'sentiment' field with a numerical score (0-10).")
    if config.TRANSCRIBE_ENGAGEMENT:
        attributes_list.append("- Include an 'engagement' field with a numerical score (0-10).")
    if config.TRANSCRIBE_EMOTIONS:
        attributes_list.append(f"- Include numerical scores for each emotion in {config.EMOTION_TYPES}.")
    if config.TRANSCRIBE_TOPICS:
        attributes_list.append("- Include a 'topic' field with the high-level topic. Keep the topics very high-level such that you limit the number of topics to 5-10.")
    attributes_str = "\n".join(attributes_list)
    
    # Read and upload the audio file
    with open(audio_filename, "rb") as audio_file:
        uploaded_blob = genai.upload_file(path=audio_file, mime_type="audio/mp3")
        gcs_uri = uploaded_blob.uri

    messages = [
        ("system", "You are a helpful assistant that transcribes audio files. In your transcription, refer to speakers as 'Speaker A', 'Speaker B', etc."),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessage(content=[
            {
                "type": "text",
                "text": f"""Please transcribe this audio file and follow these instructions:
- Output the transcription as valid JSON and nothing else.
- Each turn should be an object with 'text' and 'speaker' fields.
- Use speaker labels in the format "Speaker A", "Speaker B", etc.
- When you finish the transcription, close the JSON and on a new line add {STOP_SEQUENCE} by itself.
{attributes_str}
{participants_text}
                """
            },
            {
                "type": "media",
                "mime_type": "audio/mp3",
                "file_uri": gcs_uri
            }
        ])
    ]
      
    return run_with_iterations(llm, messages, config)

def get_significant_speakers(llm, transcript: dict, config: LLMConfig):
    """
    Runs an LLM call to identify the significant speaker labels present in the transcript.
    Expected output is a JSON list such as ["Speaker A", "Speaker B"].
    """
    messages = [
        ("system", "You are a helpful assistant that identifies significant speaker labels in transcripts."),
        HumanMessage(content=f"""
The following is a transcript with speaker labels.
Please output a JSON list of all significant speaker labels. Only include speakers with significant dialogue.
End your response with the stop sequence [DONE].
Transcript:
{transcript}
        """)
    ]
    return run_with_iterations(llm, messages, config)

def identify_speaker_names(llm, transcript: str, config: LLMConfig = None, meeting_participants: list = None) -> dict:
    """
    Runs an LLM call that analyzes the transcript and maps speaker labels (e.g., "Speaker A")
    to likely real names. The prompt is augmented with meeting participant names if provided.
    """
    participants_text = ""
    if meeting_participants:
        participants_text = (
            f"\nMeeting Participants detected during recording: {', '.join(meeting_participants)}. "
            "Note: not every participant necessarily speaks, and some may be bots."
        )
    
    messages = [
        ("system", "You are a helpful assistant that assigns names to speaker labels."),
        HumanMessage(content=f"""
The following transcript contains speaker labels such as "Speaker A", "Speaker B", etc.
Please analyze the transcript and, for each speaker label, suggest a likely real name.
{participants_text}
First, provide your reasoning for each mapping. If you are not sure about a mapping or pair of mappings, discuss possible mappings and evidence from the transcript for each before committing to a decision.
Once done reasoning, output "---" on its own line. This is important - your response will not be parsed correctly if this is not included. 
Then, on a new line, output a JSON object mapping the speaker labels to names in the format:
{{ "Speaker A": "Name", "Speaker B": "Name", ... }}
Do not output anything besides your reasoning, the string '---', and the JSON mapping.
End your response with the stop sequence [DONE].
Transcript:
{transcript}
        """)
    ]
    response = run_with_iterations(llm, messages, config)
    mapping = parse_speaker_mapping(response)
    if mapping:
        print("Identified speaker names mapping:", mapping)
    else:
        print("No speaker names mapping identified; using default labels.")
    return mapping

def analyze_skill(llm, transcript: str, speaker: str, skill: str, gcs_uri: str = None, config: LLMConfig = None):
    """
    Analyzes a specific speaking skill for a given speaker.
    If gcs_uri is provided (and if audio analysis is enabled), the prompt includes the media reference.
    """
    message_text = f"""
{transcript}

Please evaluate whether {speaker} displayed the skill of {skill} in this audio/transcript.
The output should be in JSON format, with a 'rationale' attribute containing a detailed text analysis, a 'summary' attribute with a one-line summary, and a 'score' attribute ranging from 0 (not displayed) to 10 (maximal).
Do not output anything besides valid JSON.
End your response with the stop sequence [DONE].
    """
    messages = [
        ("system", "You are a helpful assistant that analyzes speaking skills."),
        HumanMessage(content=message_text)
    ]
    if gcs_uri:
        # Append media information if available.
        messages[-1].content += f"\nMedia file: {gcs_uri}"
    return run_with_iterations(llm, messages, config)

def analyze_attribute(llm, transcript: str, speaker: str, attribute: str, gcs_uri: str = None, config: LLMConfig = None):
    """
    Analyzes a tagged attribute (sentiment/engagement) for a given speaker.
    If gcs_uri is provided (and if audio analysis is enabled), the prompt includes the media reference.
    """
    message_text = f"""
{transcript}

Please generate insights regarding {speaker}'s {attribute} in this audio/transcript, which is numerically tagged. Possible insights include whether the speaker displays more {attribute} for given topics, or in response to other speakers, as well as overall patterns in the speaker's {attribute}. You are performing a thematic analysis, looking for patterns across the entire conversation. Avoid simply summarizing the conversation and focus on generating insights. 
The output should be in JSON format, with a 'rationale' attribute containing a detailed text analysis, and a 'summary' attribute with up to three bullet points containing the most important insights.
Do not output anything besides valid JSON. Do not output control characters such as '\\"' or output newlines as '\\n'. If you want to include quotes, use apostrophes. 
End your response with the stop sequence [DONE].
    """
    messages = [
        ("system", "You are a helpful assistant that analyzes transcripts of conversations."),
        HumanMessage(content=message_text)
    ]
    if gcs_uri:
        # Append media information if available.
        messages[-1].content += f"\nMedia file: {gcs_uri}"
    return run_with_iterations(llm, messages, config)

def process_audio(input_file: str, config: LLMConfig, skills_to_analyze: list = None, meeting_participants=None):
    """
    Processes an audio file by:
      1. Running transcription (with the transcription LLM).
      2. Saving the raw transcript.
      3. Running two separate LLM calls:
         a. One to get speaker name mappings.
         b. One to extract significant speaker labels.
      4. Replacing the speaker labels in the transcript with the identified names.
      5. Optionally running skill analysis.
    """
    # Reset rate limit tracking on new call to process_audio
    global LLM_CALL_TIMESTAMPS
    LLM_CALL_TIMESTAMPS = []
    llm_transcription = get_llm(config, mode="transcription", stop_sequences=["[DONE]"])
    llm_analysis = get_llm(config, mode="analysis", stop_sequences=["[DONE]"])
    transcript_json = None 
    if config.TRANSCRIBE_AUDIO: 
        # --- Transcription ---
        raw_output = run_transcription(llm_transcription, input_file, config, meeting_participants=meeting_participants)
        transcript_json = parse_json_with_fixing(llm_transcription, raw_output)
        
        # Save the raw transcription output
        output_file = input_file.replace(".mp3", ".json")
        with open(output_file, "w") as f:
            json.dump(transcript_json, f, indent=2)
    
        # --- Speaker Diarization & Naming ---
        
        # First, get the mapping from speaker labels to names.
        names_mapping_response = identify_speaker_names(llm_analysis, raw_output, config, meeting_participants=meeting_participants)
        names_mapping = names_mapping_response if isinstance(names_mapping_response, dict) else {}
        if names_mapping:
            print("Identified speaker names mapping:", names_mapping)
        else:
            print("No speaker names mapping identified; continuing with default labels.")
        
        # Replace speaker labels with real names in the transcript.
        for entry in transcript_json:
            if "speaker" in entry and entry["speaker"] in names_mapping:
                entry["speaker"] = names_mapping[entry["speaker"]]

        with open(output_file, "w") as f:
            json.dump(transcript_json, f, indent=2)
    
    # --- Skill Analysis (Optional) ---
    if config.RUN_SKILL_ANALYSES and skills_to_analyze or config.RUN_ENGAGEMENT_INSIGHTS or config.RUN_SENTIMENT_INSIGHTS:
        if transcript_json is None: 
            transcript_json = json.load(open(input_file.replace(".mp3", ".json")))
        speakers_response = get_significant_speakers(llm_analysis, transcript_json, config)
        speakers = parse_json_with_fixing(llm_analysis, speakers_response)
        print("Identified significant speakers:", speakers)
        if config.USE_AUDIO_FOR_ANALYSIS:
            # Upload the audio file again to get a media URI for analysis.
            with open(input_file, "rb") as audio_file:
                uploaded_blob = genai.upload_file(path=audio_file, mime_type="audio/mp3")
                gcs_uri = uploaded_blob.uri
            source_for_analysis = None
        else:
            # Use a joined transcript text (combining speaker and text fields).
            source_for_analysis = "\n".join(
                [f"{entry.get('speaker', '')}: {entry.get('text', '')}" for entry in transcript_json]
            )
            gcs_uri = None
        
        skill_analysis = {}
        insights_analysis = {}
        for speaker in speakers:
            if config.RUN_SKILL_ANALYSES:
                skill_analysis[speaker] = {}
                for skill in skills_to_analyze:
                    skill_json = analyze_skill(llm_analysis, source_for_analysis, speaker, skill, gcs_uri, config)
                    skill_analysis[speaker][skill] = parse_json_with_fixing(llm_analysis, skill_json)
            if config.RUN_SENTIMENT_INSIGHTS or config.RUN_ENGAGEMENT_INSIGHTS:
                insights_analysis[speaker] = {}
                if config.RUN_SENTIMENT_INSIGHTS:
                    insights_json = analyze_attribute(llm_analysis, source_for_analysis, speaker, 'sentiment', gcs_uri, config)
                    insights_analysis[speaker]['sentiment'] = parse_json_with_fixing(llm_analysis, insights_json)
                if config.RUN_ENGAGEMENT_INSIGHTS:
                    insights_json = analyze_attribute(llm_analysis, source_for_analysis, speaker, 'engagement', gcs_uri, config)
                    insights_analysis[speaker]['engagement'] = parse_json_with_fixing(llm_analysis, insights_json)
        # Save the skill analysis results.
        if config.RUN_SKILL_ANALYSES: 
            skill_output_file = input_file.replace(".mp3", "_skills.json")
            with open(skill_output_file, "w") as f:
                json.dump(skill_analysis, f, indent=2)
        if insights_analysis: 
            insights_output_file = input_file.replace(".mp3", "_insights.json")
            with open(insights_output_file, "w") as f: 
                json.dump(insights_analysis, f, indent=2)
        return transcript_json, skill_analysis, insights_analysis
    
    return None, None, None 
