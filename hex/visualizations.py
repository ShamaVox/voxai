import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json

# -----------------------------------------------------------------------------
# VISUALIZATION CONFIGURATION CLASS
# -----------------------------------------------------------------------------

class VisualizationConfig:
    def __init__(self,
                 speaker_fig_size=(10, 6),
                 sentiment_fig_size=(15, 6),
                 engagement_fig_size=(15, 6),
                 topic_fig_size=(15, 6),
                 skills_fig_size=(15, 6),
                 timeline_fig_size=(15, 6),
                 timeline_dot_size=15,    
                 bar_color_speaker='skyblue',
                 bar_color_sentiment='lightcoral',
                 bar_color_engagement='lightgreen',
                 bar_color_skills='lightcoral',
                 top_n_topics=5):
        self.speaker_fig_size = speaker_fig_size
        self.sentiment_fig_size = sentiment_fig_size
        self.engagement_fig_size = engagement_fig_size
        self.topic_fig_size = topic_fig_size
        self.skills_fig_size = skills_fig_size
        self.timeline_fig_size = timeline_fig_size
        self.timeline_dot_size = timeline_dot_size
        self.bar_color_speaker = bar_color_speaker
        self.bar_color_sentiment = bar_color_sentiment
        self.bar_color_engagement = bar_color_engagement
        self.bar_color_skills = bar_color_skills
        self.top_n_topics = top_n_topics


# -----------------------------------------------------------------------------
# DATA LOADING FUNCTIONS
# -----------------------------------------------------------------------------

def load_transcript_json(filepath):
    """Load and convert JSON transcript into pandas DataFrame."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    return df

def load_skills_json(filepath):
    """Load and convert JSON skills analysis into pandas DataFrame."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Flatten the nested JSON structure
    rows = []
    for speaker, skills in data.items():
        for skill_name, skill_data in skills.items():
            rows.append({
                'speaker': speaker,
                'skill': skill_name,
                'rationale': skill_data['rationale'] if skill_data and 'rationale' in skill_data else '',
                'score': skill_data['score']
            })
    return pd.DataFrame(rows)

# -----------------------------------------------------------------------------
# PLOTTING FUNCTIONS
# -----------------------------------------------------------------------------

def plot_speaker_distribution(df, config: VisualizationConfig = None):
    """Plot distribution of speaker turns."""
    config = config or VisualizationConfig()
    speaker_counts = df['speaker'].value_counts()
    plt.figure(figsize=config.speaker_fig_size)
    speaker_counts.plot(kind='bar', color=config.bar_color_speaker)
    plt.title('Distribution of Speaker Turns')
    plt.xlabel('Speaker')
    plt.ylabel('Number of Turns')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
    print("\nSpeaker Statistics:")
    print(f"Total turns: {len(df)}")
    print("\nTurns per speaker:")
    print(speaker_counts)

def plot_sentiment_analysis(df, config: VisualizationConfig = None):
    """Plot sentiment analysis visualizations."""
    config = config or VisualizationConfig()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=config.sentiment_fig_size)
    
    # Convert sentiment scores to categories
    df['sentiment_category'] = pd.cut(df['sentiment'], 
                                      bins=[-np.inf, 3, 7, np.inf],
                                      labels=['Negative', 'Neutral', 'Positive'])
    
    # Overall sentiment distribution
    sentiment_counts = df['sentiment_category'].value_counts()
    sentiment_counts.plot(kind='bar', ax=ax1, color=config.bar_color_sentiment)
    ax1.set_title('Overall Sentiment Distribution')
    ax1.set_xlabel('Sentiment')
    ax1.set_ylabel('Count')
    ax1.tick_params(axis='x', rotation=45)
    
    # Average sentiment by speaker
    avg_sentiment = df.groupby('speaker')['sentiment'].mean().sort_values(ascending=False)
    avg_sentiment.plot(kind='bar', ax=ax2, color=config.bar_color_sentiment)
    ax2.set_title('Average Sentiment Score by Speaker')
    ax2.set_xlabel('Speaker')
    ax2.set_ylabel('Average Sentiment (0-10)')
    ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.show()
    
    print("\nSentiment Statistics:")
    print("\nSentiment distribution:")
    print(sentiment_counts)
    print("\nAverage sentiment by speaker:")
    print(avg_sentiment)

def plot_engagement_analysis(df, config: VisualizationConfig = None):
    """Plot engagement analysis visualizations."""
    config = config or VisualizationConfig()
    if 'engagement' not in df.columns:
        print("No engagement data found in transcript")
        return
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=config.engagement_fig_size)
    
    # Overall engagement distribution
    df['engagement_category'] = pd.cut(df['engagement'], 
                                       bins=[-np.inf, 3, 7, np.inf],
                                       labels=['Low', 'Medium', 'High'])
    engagement_counts = df['engagement_category'].value_counts()
    engagement_counts.plot(kind='bar', ax=ax1, color=config.bar_color_engagement)
    ax1.set_title('Overall Engagement Distribution')
    ax1.set_xlabel('Engagement Level')
    ax1.set_ylabel('Count')
    ax1.tick_params(axis='x', rotation=45)
    
    # Average engagement by speaker
    avg_engagement = df.groupby('speaker')['engagement'].mean().sort_values(ascending=False)
    avg_engagement.plot(kind='bar', ax=ax2, color=config.bar_color_engagement)
    ax2.set_title('Average Engagement Score by Speaker')
    ax2.set_xlabel('Speaker')
    ax2.set_ylabel('Average Engagement (0-10)')
    ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.show()

def plot_topic_analysis(df, config: VisualizationConfig = None):
    """Plot topic analysis visualizations."""
    config = config or VisualizationConfig()
    if 'topic' not in df.columns:
        print("No topic data found in transcript")
        return
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=config.topic_fig_size)
    
    # Topic distribution
    topic_counts = df['topic'].value_counts()
    topic_counts.plot(kind='bar', ax=ax1, color=config.bar_color_sentiment)
    ax1.set_title('Distribution of Topics')
    ax1.set_xlabel('Topic')
    ax1.set_ylabel('Frequency')
    ax1.tick_params(axis='x', rotation=45)
    
    # Topics per speaker
    topics_by_speaker = pd.crosstab(df['speaker'], df['topic'])
    topics_by_speaker.plot(kind='bar', stacked=True, ax=ax2)
    ax2.set_title('Topics by Speaker')
    ax2.set_xlabel('Speaker')
    ax2.set_ylabel('Number of Turns')
    ax2.legend(title='Topic', bbox_to_anchor=(1.05, 1))
    ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.show()

def plot_skills_analysis(skills_df, config: VisualizationConfig = None):
    """Plot skills analysis visualizations."""
    config = config or VisualizationConfig()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=config.skills_fig_size)
    
    # Overall skills distribution
    avg_scores = skills_df.groupby('skill')['score'].mean().sort_values(ascending=False)
    avg_scores.plot(kind='bar', ax=ax1, color=config.bar_color_skills)
    ax1.set_title('Average Score by Skill')
    ax1.set_xlabel('Skill')
    ax1.set_ylabel('Average Score (0-10)')
    ax1.tick_params(axis='x', rotation=45)
    
    # Skills by speaker
    pivot_scores = skills_df.pivot_table(index='speaker', 
                                         columns='skill', 
                                         values='score',
                                         aggfunc='mean')
    pivot_scores.plot(kind='bar', ax=ax2)
    ax2.set_title('Skills Scores by Speaker')
    ax2.set_xlabel('Speaker')
    ax2.set_ylabel('Score (0-10)')
    ax2.legend(title='Skill', bbox_to_anchor=(1.05, 1))
    ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.show()
    
    print("\nSkills Statistics:")
    print("\nAverage scores by skill:")
    print(avg_scores)
    print("\nScores by speaker:")
    print(pivot_scores)

def plot_timeline(df, y_axis, speaker=None, config: VisualizationConfig = None):
    """
    Plot a timeline graph with each dot representing a line.
    
    Parameters:
        df (DataFrame): Transcript DataFrame. If no 'time' column is found, a synthetic timeline is created using the index.
        y_axis (str): Column name to use for the y-axis ('sentiment', 'engagement', or 'topic').
        speaker (str, optional): If provided, only plot lines for this speaker.
        config (VisualizationConfig, optional): Visualization configuration.
    """
    config = config or VisualizationConfig()
    
    timeline_df = df.copy()
    # Create a synthetic 'time' column if not present
    if 'time' not in timeline_df.columns:
        timeline_df['time'] = timeline_df.index

    if speaker:
        timeline_df = timeline_df[timeline_df['speaker'] == speaker]
        hue = None
        title = f"Timeline for {speaker}"
    else:
        hue = 'speaker'
        title = "Timeline by Topic" if y_axis == "topic" else "Timeline by Speaker"
    
    plt.figure(figsize=config.timeline_fig_size)
    
    # Handle categorical y-axis (e.g., for topics) with jitter
    if timeline_df[y_axis].dtype.name in ['category', 'object']:
        # Map categories to numbers
        categories = timeline_df[y_axis].astype('category').cat.categories
        mapping = {cat: i for i, cat in enumerate(categories)}
        timeline_df['_y_numeric'] = timeline_df[y_axis].map(mapping)
        # Add slight random jitter to avoid overlap
        jitter = np.random.uniform(-0.1, 0.1, size=len(timeline_df))
        y_values = timeline_df['_y_numeric'] + jitter
        plt.yticks(range(len(categories)), categories)
        y_label = y_axis.capitalize()
    else:
        y_values = timeline_df[y_axis]
        y_label = y_axis.capitalize()
    
    if hue:
        for speaker in timeline_df['speaker'].unique():
            mask = timeline_df['speaker'] == speaker
            plt.scatter(timeline_df[mask]['time'], y_values[mask], label=speaker)
        plt.legend()
    else:
        plt.scatter(timeline_df['time'], y_values, color=config.bar_color_speaker)

    plt.title(title)
    plt.xlabel("Time")
    plt.ylabel(y_label)
    plt.tight_layout()
    plt.show()


def plot_speaker_pie_chart(df, config: VisualizationConfig = None):
    """
    Plot a pie chart showing the percentage of lines by each speaker.
    """
    config = config or VisualizationConfig()
    speaker_counts = df['speaker'].value_counts()
    
    plt.figure(figsize=(8, 8))
    # Use a pastel color map for an appealing look
    colors = plt.get_cmap('Pastel1').colors
    plt.pie(speaker_counts, labels=speaker_counts.index, autopct='%1.1f%%', startangle=140, colors=colors)
    plt.title("Percentage of Lines by Speaker")
    plt.axis('equal')  # Ensures the pie chart is circular.
    plt.tight_layout()
    plt.show()

def plot_topic_sentiment_engagement_by_speaker(df, config: VisualizationConfig = None):
    """
    For the top N topics, plot for each topic a bar graph showing:
      - "Overall" average sentiment and engagement (across all speakers)
      - Per-speaker average sentiment and engagement.
    
    This creates one subplot per topic.
    """
    config = config or VisualizationConfig()
    required_cols = {'topic', 'sentiment', 'engagement'}
    if not required_cols.issubset(df.columns):
        print("Required columns (topic, sentiment, engagement) not found in DataFrame.")
        return

    top_topics = df['topic'].value_counts().head(config.top_n_topics).index.tolist()
    num_topics = len(top_topics)
    
    fig, axes = plt.subplots(num_topics, 1, figsize=(10, 4 * num_topics))
    if num_topics == 1:
        axes = [axes]
    
    for ax, topic in zip(axes, top_topics):
        topic_df = df[df['topic'] == topic]
        # Calculate overall averages for the topic
        overall_sentiment = topic_df['sentiment'].mean()
        overall_engagement = topic_df['engagement'].mean()
        # Calculate per-speaker averages
        speaker_stats = topic_df.groupby('speaker').agg({'sentiment': 'mean', 'engagement': 'mean'}).reset_index()
        # Combine overall with speaker stats
        combined = pd.DataFrame({
            'speaker': ['Overall'] + speaker_stats['speaker'].tolist(),
            'sentiment': [overall_sentiment] + speaker_stats['sentiment'].tolist(),
            'engagement': [overall_engagement] + speaker_stats['engagement'].tolist()
        })
        
        x = np.arange(len(combined))
        width = 0.35
        ax.bar(x - width/2, combined['sentiment'], width, label='Sentiment', color=config.bar_color_sentiment)
        ax.bar(x + width/2, combined['engagement'], width, label='Engagement', color=config.bar_color_engagement)
        ax.set_xlabel('Speaker')
        ax.set_ylabel('Average Score')
        ax.set_title(f"Sentiment and Engagement for Topic: {topic}")
        ax.set_xticks(x)
        ax.set_xticklabels(combined['speaker'], rotation=45)
        ax.legend()
    
    plt.tight_layout()
    plt.show()

def plot_timeline_by_speaker_sentiment(df, config: VisualizationConfig = None):
    """
    Plot a timeline graph where:
      - x-axis: Time (using the 'time' column if available, otherwise the row index)
      - y-axis: Speaker (each speaker on its own row)
      - Dot colors: Represent the sentiment value using a gradient (e.g., coolwarm colormap)
      - Colors range from 5-10: 0-5 use the same color
      
    Parameters:
        df (DataFrame): Transcript DataFrame.
        config (VisualizationConfig, optional): Visualization configuration.
    """
    config = config or VisualizationConfig()
    timeline_df = df.copy()
    
    # Use a synthetic 'time' column if none exists
    if 'time' not in timeline_df.columns:
        timeline_df['time'] = timeline_df.index

    # Map each speaker to a unique numeric value for the y-axis
    speakers = timeline_df['speaker'].unique()
    speaker_order = {speaker: idx for idx, speaker in enumerate(speakers)}
    timeline_df['speaker_numeric'] = timeline_df['speaker'].map(speaker_order)
    
    # Normalize sentiment values to 0-5 range
    timeline_df['normalized_sentiment'] = timeline_df['sentiment'].apply(lambda x: x % 5 if x > 5 else 0)
    
    # Set up the colormap for sentiment
    cmap = plt.get_cmap('coolwarm')
    
    plt.figure(figsize=config.timeline_fig_size)
    sc = plt.scatter(
        timeline_df['time'], 
        timeline_df['speaker_numeric'], 
        c=timeline_df['normalized_sentiment'], 
        cmap=cmap,
        s=config.timeline_dot_size,
        vmin=0,
        vmax=5
    )
    
    plt.xlabel("Time")
    plt.ylabel("Speaker")
    plt.title("Timeline: Speakers Colored by Sentiment")
    
    # Replace numeric y-axis ticks with speaker names
    plt.yticks(ticks=range(len(speakers)), labels=speakers)

    # Disable x-axis ticks 
    plt.xticks([])
    
    # Add a colorbar to show sentiment values
    cbar = plt.colorbar(sc)
    cbar.set_label('Sentiment')
    
    plt.tight_layout()
    plt.show()

def plot_timeline_by_speaker_metric_aggregated(df, metric='sentiment', colormap='Greens', aggregation_threshold=1, config: VisualizationConfig = None):
    """
    Experimental timeline graph where:
      - x-axis: Time (using the 'time' column if available, otherwise the row index)
      - y-axis: Speaker (each speaker on its own row)
      - Dot colors: Represent the chosen metric value (sentiment or engagement) using a gradient.
      - Aggregation: Consecutive dots (for the same speaker) that occur within aggregation_threshold (in time units)
                     are averaged together to reduce overlap.
    
    Parameters:
        df (DataFrame): Transcript DataFrame.
        metric (str): Which metric to plot ('sentiment' or 'engagement').
        aggregation_threshold (float): Maximum time difference for consecutive rows to be aggregated.
        config (VisualizationConfig, optional): Visualization configuration.
    """
    config = config or VisualizationConfig()
    timeline_df = df.copy()
    
    # Use synthetic 'time' if none exists
    if 'time' not in timeline_df.columns:
        timeline_df['time'] = timeline_df.index.astype(float)
    else:
        timeline_df['time'] = timeline_df['time'].astype(float)
    
    # Map each speaker to a unique numeric value for the y-axis
    speakers = timeline_df['speaker'].unique()
    speaker_order = {speaker: idx for idx, speaker in enumerate(speakers)}
    timeline_df['speaker_numeric'] = timeline_df['speaker'].map(speaker_order)
    
    # Compute the metric to be used for coloring.
    # For sentiment, use the normalization logic you provided (values >5 get mapped to [0,5]);
    # For engagement, we use the raw value (you can adjust this if needed).
    if metric == 'sentiment':
        timeline_df['normalized_metric'] = timeline_df['sentiment'].apply(lambda x: x - 5 if x > 5 else 0)
        vmin, vmax = 0, 5
    elif metric == 'engagement':
        timeline_df['normalized_metric'] = timeline_df['engagement'].apply(lambda x: x - 5 if x > 5 else 0)
        vmin, vmax = 0, 5
    else:
        print(f"Unsupported metric: {metric}")
        return
    
    # For each speaker, aggregate consecutive rows that are too close in time.
    aggregated_records = []
    for speaker, group in timeline_df.groupby('speaker'):
        group = group.sort_values('time')
        current_group = []
        for _, row in group.iterrows():
            if not current_group:
                current_group.append(row)
            else:
                # If the gap between the current row and the last row in the group is within threshold, aggregate them.
                if row['time'] - current_group[-1]['time'] <= aggregation_threshold:
                    current_group.append(row)
                else:
                    # Aggregate current_group: average time and metric value.
                    avg_time = np.mean([r['time'] for r in current_group])
                    avg_metric = np.mean([r['normalized_metric'] for r in current_group])
                    aggregated_records.append({
                        'time': avg_time,
                        'speaker': speaker,
                        'speaker_numeric': current_group[0]['speaker_numeric'],
                        'normalized_metric': avg_metric
                    })
                    current_group = [row]
        # Add the final group
        if current_group:
            avg_time = np.mean([r['time'] for r in current_group])
            avg_metric = np.mean([r['normalized_metric'] for r in current_group])
            aggregated_records.append({
                'time': avg_time,
                'speaker': speaker,
                'speaker_numeric': current_group[0]['speaker_numeric'],
                'normalized_metric': avg_metric
            })
    
    aggregated_df = pd.DataFrame(aggregated_records)
    
    # Set up the colormap
    cmap = plt.get_cmap(colormap)
    dot_size = getattr(config, 'timeline_dot_size', 100)
    
    plt.figure(figsize=config.timeline_fig_size)
    sc = plt.scatter(
        aggregated_df['time'], 
        aggregated_df['speaker_numeric'], 
        c=aggregated_df['normalized_metric'], 
        cmap=cmap,
        s=dot_size,
        vmin=vmin,
        vmax=vmax,
    )
    
    plt.xlabel("Time")
    plt.ylabel("Speaker")
    plt.title(f"Timeline: {metric.capitalize()}")
    
    # Replace numeric y-axis ticks with speaker names.
    plt.yticks(ticks=range(len(speakers)), labels=speakers)
    # Optionally disable x-axis ticks.
    plt.xticks([])
    
    cbar = plt.colorbar(sc)
    cbar.set_label(metric.capitalize())
    
    plt.tight_layout()
    plt.show()

# -----------------------------------------------------------------------------
# ANALYSIS ENTRY POINT
# -----------------------------------------------------------------------------

def analyze_conversation(transcript_path, skills_path=None, viz_config: VisualizationConfig = None):
    """Analyze conversation data and generate all visualizations."""
    # Load transcript data
    df = load_transcript_json(transcript_path)
    
    # Basic analysis: speaker distribution
    plot_speaker_distribution(df, viz_config)
    
    # Sentiment analysis (if available)
    if 'sentiment' in df.columns:
        plot_sentiment_analysis(df, viz_config)
    
    # Engagement analysis (if available)
    if 'engagement' in df.columns:
        plot_engagement_analysis(df, viz_config)
    
    # Topic analysis (if available)
    if 'topic' in df.columns:
        plot_topic_analysis(df, viz_config)
    
    # Skills analysis (if available)
    if skills_path:
        skills_df = load_skills_json(skills_path)
        plot_skills_analysis(skills_df, viz_config)