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

    git clone https://github.com/ShamaVox/voxai/voxai.git
    cd voxai

If this doesn't work, try cloning via ssh:

    ssh-keygen -t ed25519 -C <your email>
    git clone git@github.com:ShamaVox/voxai.git   

After cloning, check out the dev branch:

    cd voxai    
    git checkout dev

### Backend Setup:

Install the requirements, if not installed already. 

On Ubuntu or any Linux distro supporting apt-get:

    sudo apt-get update
    sudo apt-get install python3.12
    sudo apt-get install python3.12-venv
    sudo apt-get install python3-dev libpq-dev
    sudo apt-get install postgresql

Installing nvm on Linux:

    sudo apt-get install curl
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash

On MacOS: 

    brew install python3
    brew install postgres
    brew install nvm

(On both Mac and Linux) Set up NVM and install node through NVM:

    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
    nvm install node

You may need to restart your shell after running the first two commands. 

Create a Python virtual environment and install the required Python libraries:

    cd server
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade wheel
    pip install --upgrade setuptools
    pip install -r requirements.txt

To avoid running the nvm commands every time the virtual environment is initialized, add them to the bottom of server/venv/bin/activate. 

### Database Setup:

Start the postgres server:

    psql start

Create a role:

    sudo -u postgres createuser -s YOUR_USERNAME

In a new terminal, create a database for the application:

    psql POSTGRES
    CREATE DATABASE voxai_db;

Edit the database URI in server/src/database.py to match the database credentials:

    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://localhost:5432/voxai_db"

If you set up a different postgres user than the default, the line will look something like this:

    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://username:password@localhost:5432/voxai_db"

### AWS / Recall Setup:

Download the AWS and Recall credentials to ~/.aws/credentials.json. (These will be shared in the Slack once the VoxAI AWS account is set up.)

### Database Migrations:

   npm run upgrade

### Frontend Setup
**Work in progress - instructions may be incomplete**

Navigate to Frontend Directory:

    cd client

Install Frontend Dependencies:

    npm install

### Running the Application
Run in Development mode on the AWS server:

    npm run dev

This command also runs in development mode:

    npm start

Run locally (server will be on localhost):

    npm run local 

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