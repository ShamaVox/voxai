import json
import pandas as pd
from IPython.display import HTML, display

# -----------------------------------------------------------------------------
# TRANSCRIPT VISUALIZATION CONFIGURATION CLASS
# -----------------------------------------------------------------------------

class TranscriptVizConfig:
    def __init__(self,
                 # Colors: base values for low and high sentiment; these are used to compute a red-green gradient.
                 low_sentiment_color=(200, 0, 0),  # Base for low sentiment (red-ish)
                 high_sentiment_color=(0, 200, 0),   # Base for high sentiment (green-ish)
                 sentiment_max_score=10,             # Maximum sentiment score (assumed 0 to 10 scale)
                 sentiment_mid_score=5,              # Middle score used for scaling
                 # Font weight settings for engagement
                 engagement_min_weight=100,
                 engagement_max_weight=500,
                 # Additional style parameters for transcript display
                 line_padding="5px",
                 topic_marker_style="font-weight: bold; font-size: 1.2em; margin-top: 10px;"
                ):
        self.low_sentiment_color = low_sentiment_color
        self.high_sentiment_color = high_sentiment_color
        self.sentiment_max_score = sentiment_max_score
        self.sentiment_mid_score = sentiment_mid_score
        self.engagement_min_weight = engagement_min_weight
        self.engagement_max_weight = engagement_max_weight
        self.line_padding = line_padding
        self.topic_marker_style = topic_marker_style

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def get_color(sentiment, config: TranscriptVizConfig = None):
    """
    Convert a sentiment score (0-10) to an RGB color (as a hex string) on a red-green gradient.
    When sentiment is low, the color is closer to red; when high, closer to green.
    """
    # Use default config if not provided.
    config = config or TranscriptVizConfig()
    
    # Normalize sentiment to a 0-1 scale.
    norm = sentiment / config.sentiment_max_score
    # Interpolate between low and high color.
    red = int(config.low_sentiment_color[0] * (1 - norm) + config.high_sentiment_color[0] * norm)
    green = int(config.low_sentiment_color[1] * (1 - norm) + config.high_sentiment_color[1] * norm)
    blue = 0  # Fixed blue channel.
    return f'#{red:02x}{green:02x}{blue:02x}'

def get_font_weight(engagement, config: TranscriptVizConfig = None):
    """
    Convert an engagement score (0-10) to a font weight between engagement_min_weight and engagement_max_weight.
    """
    config = config or TranscriptVizConfig()
    # Scale the engagement from 0-10 to the configured weight range.
    weight = config.engagement_min_weight + (engagement / 10) * (config.engagement_max_weight - config.engagement_min_weight)
    return int(weight)

# Helper style function for pandas.
def color_score(val):
    try:
        val = float(val)
        if pd.isna(val):
            return ''
        elif val >= 8:
            return 'background-color: #a8e6cf'  # Light green
        elif val >= 6:
            return 'background-color: #dcedc1'  # Light yellow-green
        elif val >= 4:
            return 'background-color: #ffd3b6'  # Light orange
        else:
            return 'background-color: #ffaaa5'  # Light red
    except:
        return ''

# -----------------------------------------------------------------------------
# TRANSCRIPT DISPLAY FUNCTIONS
# -----------------------------------------------------------------------------

def print_transcript(file_path, config: TranscriptVizConfig = None):
    """
    Load a JSON transcript and display it as HTML.
    Each transcript line is styled based on sentiment and engagement.
    A topic marker is inserted whenever the topic changes.
    """
    config = config or TranscriptVizConfig()
    try:
        with open(file_path, 'r') as file:
            transcript = json.load(file)
    except FileNotFoundError:
        print(f"Error: Could not find file {file_path}")
        return
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in file")
        return

    html_output = []
    current_topic = None
    
    for entry in transcript:
        # Insert a topic marker if the topic changes.
        if entry.get('topic') != current_topic:
            current_topic = entry.get('topic')
            html_output.append(f'<div style="{config.topic_marker_style}">(Topic: {current_topic})</div>')
        
        # Determine color based on sentiment and font weight based on engagement.
        color = get_color(entry.get('sentiment', config.sentiment_mid_score), config)
        weight = get_font_weight(entry.get('engagement', 5), config)
        line = (
            f'<div style="color: {color}; font-weight: {weight}; padding: {config.line_padding};">'
            f'{entry.get("speaker", "Unknown")}: {entry.get("text", "")}'
            '</div>'
        )
        html_output.append(line)
    
    display(HTML('\n'.join(html_output)))

def generate_transcript_html(transcript_data):
    """
    Given a list of transcript entries (dictionaries with keys such as 
    'speaker', 'text', 'sentiment', 'engagement', and 'topic'),
    returns an HTML string that displays the transcript with tooltips.
    
    The tooltip shows the sentiment, engagement, and topic. The sentiment and
    engagement numbers are color coded (red if < 5, green if >= 5) and bold.
    A topic header is inserted whenever the topic changes.
    """
    html = """
<div style="font-family: Arial, sans-serif; position: relative;">
  <style>
      .tooltip {
          display: none;
          position: absolute;
          background: #f9f9f9;
          border: 1px solid #ddd;
          padding: 5px;
          border-radius: 3px;
          box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
          z-index: 10;
      }
  </style>
  <script>
      function showTooltip(e, elem) {
          var tooltip = elem.querySelector('.tooltip');
          tooltip.style.display = 'block';
          moveTooltip(e, elem);
      }
      function hideTooltip(elem) {
          var tooltip = elem.querySelector('.tooltip');
          tooltip.style.display = 'none';
      }
      function moveTooltip(e, elem) {
          var tooltip = elem.querySelector('.tooltip');
          tooltip.style.left = (e.pageX + 10) + 'px';
          tooltip.style.top = (e.pageY + 10) + 'px';
      }
  </script>
"""
    current_topic = None
    # Loop through each transcript entry.
    for entry in transcript_data:
        topic = entry.get('topic', '')
        # When topic changes, output a topic header.
        if topic != current_topic:
            current_topic = topic
            html += f'<div style="font-weight: bold; margin-top: 10px;">(Topic: {current_topic})</div>\n'
        speaker = entry.get('speaker', 'Unknown')
        text = entry.get('text', '')
        sentiment = entry.get('sentiment', 5)
        engagement = entry.get('engagement', 5)
        # Determine color: red if value < 5, green otherwise.
        sentiment_color = 'green' if sentiment >= 5 else 'red'
        engagement_color = 'green' if engagement >= 5 else 'red'
        tooltip_info = (
            f"Sentiment: <span style='color: {sentiment_color}; font-weight: bold;'>{sentiment}</span>, "
            f"Engagement: <span style='color: {engagement_color}; font-weight: bold;'>{engagement}</span>, "
            f"Topic: {topic}"
        )
        # Each line is in a span with a nested span.tooltip.
        html += f"""
  <span style="cursor: help;" 
        onmouseover="showTooltip(event, this)" 
        onmouseout="hideTooltip(this)" 
        onmousemove="moveTooltip(event, this)">
      {speaker}: {text}
      <span class="tooltip">{tooltip_info}</span>
  </span><br><br>
"""
    html += "</div>"
    return html


# -----------------------------------------------------------------------------
# SKILLS DISPLAY FUNCTIONS
# -----------------------------------------------------------------------------

def display_candidate_skills(skills_data, candidates=None, config: TranscriptVizConfig = None):
    """
    Display skills data for candidates in a nicely formatted table.
    
    Parameters:
      - skills_data (dict): Dictionary containing skills data.
      - candidates (list, optional): List of specific candidates to display. If None, displays all.
      - config (TranscriptVizConfig, optional): Configuration object (currently not used for styling, but available for extension).
    """

    # Process candidates.
    if candidates is None:
        candidates = list(skills_data.keys())
    
    for candidate in candidates:
        if candidate not in skills_data:
            print(f"No data found for {candidate}")
            continue
            
        print(f"\n## Skills Analysis for {candidate}")
        
        rows = []
        for skill, data in skills_data[candidate].items():
            if data is not None:
                score = data.get('score', 'N/A')
                rationale = data.get('rationale', 'No rationale provided')
                rows.append({
                    'Skill': skill,
                    'Score': score,
                    'Rationale': rationale
                })
        
        if not rows:
            print("No skills data available")
            continue
            
        df = pd.DataFrame(rows)
        styled_df = (df.style
                       .apply(lambda x: ['text-align: center' if x.name == 'Score' else 'text-align: left' for _ in x], axis=0)
                       .apply(lambda x: ['font-weight: bold' if x.name == 'Skill' else '' for _ in x], axis=0)
                       .applymap(color_score, subset=['Score'])
                       .set_properties(**{'padding': '10px', 'border': '1px solid #ddd', 'white-space': 'pre-wrap'})
                       .set_table_styles([
                           {'selector': 'th',
                            'props': [('background-color', '#4a4a4a'),
                                      ('color', 'white'),
                                      ('font-weight', 'bold'),
                                      ('text-align', 'center'),
                                      ('padding', '10px')]},
                           {'selector': 'table',
                            'props': [('border-collapse', 'collapse'),
                                      ('width', '100%'),
                                      ('margin', '10px 0')]},
                           {'selector': 'caption',
                            'props': [('caption-side', 'bottom'),
                                      ('text-align', 'left'),
                                      ('font-style', 'italic'),
                                      ('padding', '10px')]}
                       ]))
        
        display(HTML(styled_df.to_html()))
        print("\n" + "-"*80)

def display_skills_summary(skills_data, config: TranscriptVizConfig = None):
    """
    Display a summary table of all candidates' skills scores.
    
    Parameters:
      - skills_data (dict): Dictionary containing skills data.
      - config (TranscriptVizConfig, optional): Configuration object (currently not used for styling, but available for extension).
    """
    summary_data = {}
    all_skills = set()
    
    for candidate, skills in skills_data.items():
        summary_data[candidate] = {}
        for skill, data in skills.items():
            if data is not None:
                summary_data[candidate][skill] = data.get('score', 'N/A')
                all_skills.add(skill)
    
    df = pd.DataFrame.from_dict(summary_data, orient='index')
    for skill in all_skills:
        if skill not in df.columns:
            df[skill] = 'N/A'
    df = df.sort_index(axis=1)
    
    avg_scores = []
    for col in df.columns:
        numeric_vals = pd.to_numeric(df[col], errors='coerce')
        avg = numeric_vals.mean()
        avg_scores.append(round(avg, 2) if not pd.isna(avg) else 'N/A')
    df.loc['Average'] = avg_scores
    
    styled_df = (df.style
                   .apply(lambda x: ['text-align: center' for _ in x], axis=0)
                   .applymap(lambda val: color_score(val))
                   .set_properties(**{'padding': '10px', 'border': '1px solid #ddd'})
                   .set_table_styles([
                       {'selector': 'th',
                        'props': [('background-color', '#4a4a4a'),
                                  ('color', 'white'),
                                  ('font-weight', 'bold'),
                                  ('text-align', 'center'),
                                  ('padding', '10px')]},
                       {'selector': 'table',
                        'props': [('border-collapse', 'collapse'),
                                  ('width', '100%'),
                                  ('margin', '10px 0')]},
                       {'selector': 'caption',
                        'props': [('caption-side', 'bottom'),
                                  ('text-align', 'left'),
                                  ('font-style', 'italic'),
                                  ('padding', '10px')]}
                   ]))
    
    print("\n# Skills Summary for All Candidates")
    display(HTML(styled_df.to_html()))

def get_skill_cell_color(score):
    """
    Returns a background color based on a 0-10 score:
      - Score >= 8: light green (#a8e6cf)
      - Score >= 6: light yellow-green (#dcedc1)
      - Score >= 4: light orange (#ffd3b6)
      - Otherwise: light red (#ffaaa5)
    """
    try:
        score = float(score)
    except:
        return ''
    if score >= 8:
        return '#a8e6cf'
    elif score >= 6:
        return '#dcedc1'
    elif score >= 4:
        return '#ffd3b6'
    else:
        return '#ffaaa5'

def generate_detailed_skills_html(skills_data):
    """
    Given a dictionary mapping speaker names to dictionaries of skills (where each skill is itself a JSON
    object with at least 'score' and 'summary' keys), returns an HTML string rendering a detailed table.
    
    The table has the following columns:
      Speaker | Skill | Score | Summary
    
    The "Score" cell is color-coded based on the score.
    """
    html = '<table style="border-collapse: collapse; width: 100%;">\n'
    # Header row
    html += (
        '  <tr style="background-color: #4a4a4a; color: white; text-align: center;">\n'
        '    <th style="padding: 8px; border: 1px solid #ddd;">Speaker</th>\n'
        '    <th style="padding: 8px; border: 1px solid #ddd;">Skill</th>\n'
        '    <th style="padding: 8px; border: 1px solid #ddd;">Score</th>\n'
        '    <th style="padding: 8px; border: 1px solid #ddd;">Summary</th>\n'
        '  </tr>\n'
    )
    # Data rows
    for speaker, skills in skills_data.items():
        for skill, data in skills.items():
            if data is not None:
                score = data.get('score', 'N/A')
                summary = data.get('summary', 'No summary provided')
            else:
                score = 'N/A'
                summary = 'N/A'
            cell_color = get_skill_cell_color(score) if score != 'N/A' else ''
            html += '  <tr>\n'
            html += f'    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{speaker}</td>\n'
            html += f'    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{skill}</td>\n'
            html += f'    <td style="padding: 8px; border: 1px solid #ddd; text-align: center; background-color: {cell_color};">{score}</td>\n'
            html += f'    <td style="padding: 8px; border: 1px solid #ddd; text-align: left;">{summary}</td>\n'
            html += '  </tr>\n'
    html += '</table>'
    return html

# -----------------------------------------------------------------------------
# SENTIMENT AND ENGAGEMENT DISPLAY 
# -----------------------------------------------------------------------------

def generate_average_sentiment_engagement_html(transcript_data):
    """
    Given a list of transcript entries (each a dict with keys like 'speaker', 
    'sentiment', and 'engagement'), compute the average sentiment and average engagement
    for each speaker and return an HTML table string.

    The table has three columns:
      - Speaker
      - Average Sentiment
      - Average Engagement

    Each numeric cell's background color is determined using get_skill_cell_color.
    """
    # Group sentiment and engagement values by speaker.
    speaker_stats = {}
    for entry in transcript_data:
        speaker = entry.get('speaker', 'Unknown')
        try:
            sentiment = float(entry.get('sentiment', 0))
            engagement = float(entry.get('engagement', 0))
        except (ValueError, TypeError):
            continue  # skip entries with invalid numbers
        if speaker not in speaker_stats:
            speaker_stats[speaker] = {'sentiments': [], 'engagements': []}
        speaker_stats[speaker]['sentiments'].append(sentiment)
        speaker_stats[speaker]['engagements'].append(engagement)
    
    # Compute averages for each speaker.
    averages = {}
    for speaker, values in speaker_stats.items():
        if values['sentiments']:
            avg_sentiment = sum(values['sentiments']) / len(values['sentiments'])
        else:
            avg_sentiment = None
        if values['engagements']:
            avg_engagement = sum(values['engagements']) / len(values['engagements'])
        else:
            avg_engagement = None
        averages[speaker] = {
            'avg_sentiment': round(avg_sentiment, 2) if avg_sentiment is not None else 'N/A',
            'avg_engagement': round(avg_engagement, 2) if avg_engagement is not None else 'N/A'
        }
    
    # Build the HTML table.
    html = '<table style="border-collapse: collapse; width: 100%;">\n'
    # Header row.
    html += (
        '  <tr style="background-color: #4a4a4a; color: white; text-align: center;">\n'
        '    <th style="padding: 8px; border: 1px solid #ddd;">Speaker</th>\n'
        '    <th style="padding: 8px; border: 1px solid #ddd;">Average Sentiment</th>\n'
        '    <th style="padding: 8px; border: 1px solid #ddd;">Average Engagement</th>\n'
        '  </tr>\n'
    )
    # Data rows.
    for speaker, stats in averages.items():
        avg_sent = stats['avg_sentiment']
        avg_eng = stats['avg_engagement']
        # Color-code using get_skill_cell_color if a numeric value is available.
        sentiment_color = get_skill_cell_color(avg_sent) if avg_sent != 'N/A' else ''
        engagement_color = get_skill_cell_color(avg_eng) if avg_eng != 'N/A' else ''
        html += '  <tr>\n'
        html += f'    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{speaker}</td>\n'
        html += (f'    <td style="padding: 8px; border: 1px solid #ddd; text-align: center; background-color: {sentiment_color};">'
                 f'{avg_sent}</td>\n')
        html += (f'    <td style="padding: 8px; border: 1px solid #ddd; text-align: center; background-color: {engagement_color};">'
                 f'{avg_eng}</td>\n')
        html += '  </tr>\n'
    html += '</table>'
    return html

def generate_attribute_insights_html(insights_data, attribute):
    """
    Given a dictionary mapping speaker names to analysis results for a given attribute
    (e.g., 'sentiment' or 'engagement'), returns an HTML table (as a string) where each row
    displays the speaker's name and a bullet list of insights extracted from the 'summary'
    attribute of the analysis result.
    
    Parameters:
      insights_data (dict): Keys are speaker names and values are JSON objects with at least a 
                            'summary' key.
      attribute (str): The attribute being analyzed (e.g., 'sentiment' or 'engagement') used for labeling.
    """
    html = f'<h2>{attribute.capitalize()} Insights Summary</h2>\n'
    html += '<table style="border-collapse: collapse; width: 100%;">\n'
    # Header row
    html += (
        '  <tr style="background-color: #4a4a4a; color: white; text-align: center;">\n'
        '    <th style="padding: 8px; border: 1px solid #ddd;">Speaker</th>\n'
        f'    <th style="padding: 8px; border: 1px solid #ddd;">{attribute.capitalize()} Insights</th>\n'
        '  </tr>\n'
    )
    # Data rows for each speaker.
    for speaker, analysis in insights_data.items():
        analysis = analysis[attribute]
        summary = analysis.get("summary", "")
        # If the summary is a list, build bullet points; if it's a string, try splitting on newlines.
        if isinstance(summary, list):
            bullet_list = "<ul>" + "".join(f"<li>{point}</li>" for point in summary) + "</ul>"
        else:
            lines = [line.strip() for line in summary.split('\n') if line.strip()] if summary else []
            if lines:
                bullet_list = "<ul>" + "".join(f"<li>{line}</li>" for line in lines) + "</ul>"
            else:
                bullet_list = summary
        html += '  <tr>\n'
        html += f'    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{speaker}</td>\n'
        html += f'    <td style="padding: 8px; border: 1px solid #ddd; text-align: left;">{bullet_list}</td>\n'
        html += '  </tr>\n'
    html += '</table>'
    return html

# -----------------------------------------------------------------------------
# ENTRY POINT FUNCTION
# -----------------------------------------------------------------------------

def visualize_transcript(transcript_file, skills_file=None, config: TranscriptVizConfig = None):
    """
    Unified entry point to visualize the transcript and skills data.
    
    Parameters:
      - transcript_file: Path to the JSON transcript file.
      - skills_file: Optional path to the JSON skills file.
      - config: An optional TranscriptVizConfig instance.
    """
    config = config or TranscriptVizConfig()
    
    print("Displaying Transcript:")
    print_transcript(transcript_file, config)
    
    if skills_file:
        try:
            with open(skills_file, 'r') as f:
                skills_data = json.load(f)
            print("\nDisplaying Skills Summary:")
            display_skills_summary(skills_data, config)
            print("\nDisplaying Detailed Candidate Skills:")
            display_candidate_skills(skills_data, config=config)
        except FileNotFoundError:
            print(f"Error: Could not find skills file {skills_file}")
        except json.JSONDecodeError:
            print("Error: Invalid JSON format in skills file")
        except Exception as e:
            print(f"An error occurred while loading skills data: {str(e)}")
