# Overview
VoxAI is a comprehensive recruitment platform that leverages cutting-edge AI technologies to streamline the hiring process and enhance decision-making. It integrates seamlessly with popular video conferencing platforms, such as Zoom, to provide valuable insights from interview recordings.

# Features
## Automated Interview Recording and Transcription: 
* Generate accurate transcripts with speaker identification from interviews conducted through platforms like Zoom, Google Meet, Microsoft Teams, and Slack. 

## Advanced Interview Analysis
Gain deeper insights into candidate performance through:
* Sentiment Analysis: Understand the emotional tone of candidates throughout the interview.
* Engagement Analysis: Assess candidate engagement levels and enthusiasm.
* Topic Extraction: Identify key topics discussed during the interview, allowing for quick review and comparison.
* Summarization: Get a concise overview of the interview, highlighting important points.
* Actionable Insights Dashboard: Track key metrics and trends, such as average interview pace, fitting job application percentage, and compensation ranges, to make data-driven decisions.

# Technology Stack
Backend: Python, Flask, SQLAlchemy
Database: PostgreSQL
Frontend: React Native (TypeScript)
AI APIs: Recall.ai (for meeting recording, transcription, and analysis)

# Installation and Setup

## Prerequisites
Git: Ensure you have Git installed for cloning the repository.
Node.js and npm: Download and install Node.js (which includes npm) from https://nodejs.org/.
Python 3 and venv: Install Python 3 and ensure the venv module is available for creating virtual environments.
PostgreSQL: Install PostgreSQL and have it running locally.
Concurrently: Install with npm install -g concurrently.

## Backend Setup

### Clone the Repository:
    git clone https://github.com/your-username/voxai.git
    cd voxai

### Backend Setup:
    cd server
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

### Database Setup:
Create a database for the application:
    createdb voxai_db

Edit the database URI in server/src/database.py to match the database credentials.

### Database Migrations:
   npm run upgrade

### Frontend Setup
Navigate to Frontend Directory:
    cd client

Install Frontend Dependencies:
    npm install

### Running the Application
Run in Development mode:
    npm run dev

### Running Backend and Frontend Separately:
Backend:
    npm run server

Frontend:
    npm run client

### Running Tests
Run the integration tests:
    npm run test

Run the integration tests, excluding intensive tests:
    npm run test:light

Run the backend test suite:
    cd server
    pytest

Run the frontend test suite:
    cd client
    npm run test