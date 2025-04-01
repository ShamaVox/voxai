from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import matplotlib
matplotlib.use('Agg')  # Set backend to prevent display
import matplotlib.pyplot as plt
import pandas as pd
import io
import os
import json
from .visualizations import load_transcript_json, plot_speaker_distribution, plot_sentiment_analysis, plot_engagement_analysis, plot_topic_analysis

class ReportConfig:
    def __init__(self,
                 # Page settings
                 page_size=landscape(letter),
                 margins=36,  # in points
                 # Table settings
                 col_widths=[1.5*inch, 0.8*inch, 2.0*inch, 4.0*inch],
                 table_colors={
                     'header_bg': colors.grey,
                     'header_text': colors.whitesmoke,
                     'alt_row_bg': colors.lightgrey
                 },
                 # Font settings
                 header_font_size=24,
                 section_font_size=16,
                 table_font_size=10,
                 # Visualization settings
                 viz_width=7*inch,
                 viz_height=4*inch,
                 viz_dpi=300):
        self.page_size = page_size
        self.margins = margins
        self.col_widths = col_widths
        self.table_colors = table_colors
        self.header_font_size = header_font_size
        self.section_font_size = section_font_size
        self.table_font_size = table_font_size
        self.viz_width = viz_width
        self.viz_height = viz_height
        self.viz_dpi = viz_dpi
        
        # Initialize styles
        self.styles = self._create_styles()
        self.table_style = self._create_table_style()
    
    def _create_styles(self):
        """Create and return dictionary of paragraph styles."""
        base_styles = getSampleStyleSheet()
        return {
            'header': ParagraphStyle(
                'CustomHeader',
                parent=base_styles['Heading1'],
                fontSize=self.header_font_size,
                spaceAfter=30,
                spaceBefore=20
            ),
            'section': ParagraphStyle(
                'SectionHeader',
                parent=base_styles['Heading2'],
                fontSize=self.section_font_size,
                spaceBefore=20,
                spaceAfter=12
            ),
            'normal': ParagraphStyle(
                'Normal',
                parent=base_styles['Normal'],
                fontSize=self.table_font_size,
                leading=self.table_font_size + 2
            ),
            'bold': ParagraphStyle(
                'Bold',
                parent=base_styles['Normal'],
                fontSize=self.table_font_size,
                leading=self.table_font_size + 2,
                fontName='Helvetica-Bold'
            )
        }
    
    def _create_table_style(self):
        """Create and return table style configuration."""
        return TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), self.table_colors['header_bg']),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.table_colors['header_text']),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            # Padding and borders
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),
            # Content alignment
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (3, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.table_colors['alt_row_bg']])
        ])

class ReportGenerator:
    def __init__(self, config=None):
        self.config = config or ReportConfig()
    
    def create_visualization(self, plot_func, data):
        """Create visualization as ReportLab Image object."""
        # Check if data is empty
        if data.empty:
            return None
            
        try:
            buf = io.BytesIO()
            plot_func(data)
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=self.config.viz_dpi)
            plt.close()
            buf.seek(0)
            return Image(buf, width=self.config.viz_width, height=self.config.viz_height)
        except Exception as e:
            print(f"Warning: Failed to create visualization: {str(e)}")
            return None
    
    def create_skills_table(self, skills_data, speaker):
        """Create formatted skills table for a speaker."""
        if speaker not in skills_data:
            return None
            
        table_data = [['Skill', 'Score', 'Summary', 'Rationale']]
        
        for skill, data in skills_data[speaker].items():
            if data is not None:
                row = [
                    Paragraph(skill, self.config.styles['bold']),
                    str(data.get('score', 'N/A')),
                    Paragraph(data.get('summary', 'No summary provided'), self.config.styles['normal']),
                    Paragraph(data.get('rationale', 'No rationale provided'), self.config.styles['normal'])
                ]
                table_data.append(row)
        
        table = Table(table_data, colWidths=self.config.col_widths)
        table.setStyle(self.config.table_style)
        return table
    
    def generate_individual_report(self, transcript_df, skills_data, speaker):
        """Generate individual PDF report for a speaker."""
        output_path = f"{speaker.replace(' ', '_')}_report.pdf"
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.config.page_size,
            rightMargin=self.config.margins,
            leftMargin=self.config.margins,
            topMargin=self.config.margins,
            bottomMargin=self.config.margins
        )
        
        content = []
        content.append(Paragraph(f"Analysis Report for {speaker}", self.config.styles['header']))
        
        # Add skills analysis
        content.append(Paragraph("Skills Analysis", self.config.styles['section']))
        skills_table = self.create_skills_table(skills_data, speaker)
        if skills_table:
            content.append(skills_table)
        else:
            content.append(Paragraph("No skills data available", self.config.styles['normal']))
        
        content.append(Spacer(1, 20))
        
        # Add visualizations
        speaker_data = transcript_df[transcript_df['speaker'] == speaker]
        self._add_visualizations(content, speaker_data)
        
        doc.build(content)
        print(f"Generated report for {speaker}: {output_path}")
    
    def generate_summary_report(self, transcript_df, skills_data):
        """Generate summary PDF report."""
        doc = SimpleDocTemplate(
            "summary_report.pdf",
            pagesize=self.config.page_size,
            rightMargin=self.config.margins,
            leftMargin=self.config.margins,
            topMargin=self.config.margins,
            bottomMargin=self.config.margins
        )
        
        content = []
        content.append(Paragraph("Conversation Analysis Summary Report", self.config.styles['header']))
        content.append(Spacer(1, 20))
        
        self._add_visualizations(content, transcript_df, is_summary=True)
        
        doc.build(content)
        print("Generated summary report: summary_report.pdf")
    
    def _add_visualizations(self, content, data, is_summary=False):
        """Helper method to add visualizations to report content."""
        if is_summary:
            content.append(Paragraph("Speaker Distribution", self.config.styles['section']))
            viz = self.create_visualization(plot_speaker_distribution, data)
            if viz:
                content.append(viz)
            content.append(Spacer(1, 20))
        
        for col, title, plot_func in [
            ('sentiment', 'Sentiment Analysis', plot_sentiment_analysis),
            ('engagement', 'Engagement Analysis', plot_engagement_analysis),
            ('topic', 'Topic Analysis', plot_topic_analysis)
        ]:
            if col in data.columns:
                content.append(Paragraph(f"{'Overall ' if is_summary else ''}{title}", 
                                      self.config.styles['section']))
                content.append(Spacer(1, 10))
                viz = self.create_visualization(plot_func, data)
                if viz:
                    content.append(viz)
                content.append(Spacer(1, 20))
    
    def generate_all_reports(self, transcript_path, skills_path):
        """Generate all PDF reports."""
        try:
            # Load transcript data
            with open(transcript_path, 'r') as f:
                transcript_data = json.load(f)
            transcript_df = pd.DataFrame(transcript_data)
            
            # Load skills data
            with open(skills_path, 'r') as f:
                skills_data = json.load(f)
            
            self.generate_summary_report(transcript_df, skills_data)
            
            for speaker in skills_data.keys():
                self.generate_individual_report(transcript_df, skills_data, speaker)
            
            print("All reports generated successfully in current directory")
            
        except FileNotFoundError as e:
            print(f"Error: Could not find file - {e}")
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format - {e}")
        except Exception as e:
            print(f"Error generating reports: {str(e)}")
