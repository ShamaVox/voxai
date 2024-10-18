# Overview

VoxAI is a comprehensive recruitment platform that leverages cutting-edge AI technologies to streamline the hiring process and enhance decision-making. It integrates seamlessly with popular video conferencing platforms, such as Zoom, to provide valuable insights from interview recordings.

# Features

## Automated Interview Recording and Transcription:

- Generate accurate transcripts with speaker identification from interviews conducted through platforms like Zoom, Google Meet, Microsoft Teams, and Slack.

## Advanced Interview Analysis

Gain deeper insights into candidate performance through:

- Sentiment Analysis: Understand the emotional tone of candidates throughout the interview.
- Engagement Analysis: Assess candidate engagement levels and enthusiasm.
- Topic Extraction: Identify key topics discussed during the interview, allowing for quick review and comparison.
- Summarization: Get a concise overview of the interview, highlighting important points.
- Actionable Insights Dashboard: Track key metrics and trends, such as average interview pace, fitting job application percentage, and compensation ranges, to make data-driven decisions.

# Technology Stack

Backend: Python, Flask, SQLAlchemy
Database: PostgreSQL
Frontend: React Native (TypeScript)
AI APIs: Recall.ai (for meeting recording, transcription, and analysis)

# Installation and Setup (Docker)

## Prerequisites

Install Docker Desktop. You can find instructions here:

    https://docs.docker.com/desktop/install/

## Clone the Repository:

git clone https://github.com/ShamaVox/voxai/voxai.git
cd voxai

If this doesn't work, try cloning via ssh:

    ssh-keygen -t ed25519 -C <your email>
    git clone git@github.com:ShamaVox/voxai.git

After cloning, check out the dev branch:

    cd voxai
    git checkout dev

## Build docker image

The credentials.json file containing AWS and Recall AI credentials is not included with the repository but is required for the image to function. Obtain this file and copy it to the voxai directory before creating the docker image.

Then, copy the Dockerfile to the directory containing the repository and run docker build:

    cp Dockerfile ../
    cd ../
    docker build -t voxai .

If you're running the repository or any other locally, Docker's postgres service may conflict with the external one. In this case, you'll need to disable the postgres service on the host machine before building the image:

    service postgresql stop

## Run docker image

You can run the docker image with the following command:

    docker run -it --network host --entrypoint /bin/bash voxai

From within docker, start the postgresql service:

    service postgresql restart

This is currently required at each login for postgres to function correctly within the instance (this is a bug).

## Make changes within Docker

The copy of the repository inside the docker image does not automatically sync with your changes outside of it. The VSCode Dev Containers extension can be used to edit files within the container once it is running and sync it with Git, avoiding rebuilding every time a change is made.

More information here: https://code.visualstudio.com/docs/devcontainers/attach-container

## Running the Application

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

### Database Migrations

Generate a new migration (runs the migration by default after asking for confirmation, can be prevented with Ctrl-C):

    npm run migrate

Run the existing migrations:

    npm run upgrade

# Installation and Setup (Manual)

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

On Linux, authbind also needs to be set up:

    sudo touch /etc/authbind/byport/80
    sudo chmod 500 /etc/authbind/port/80
    sudo chown <your username> /etc/authbind/byport/80

### Database Setup:

Start the postgres server:

    psql start

Create a role:

    sudo -u postgres createuser -s YOUR_USERNAME

In a new terminal, create a database for the application:

    psql postgres
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

Install dependencies for running server and client at the same time:

    npm install

Install frontend dependencies:

    cd client
    npm install

### Configuring server URL

To run the server locally:

    cd client
    npm run config:local

To run the server on AWS:

    cd client
    npm run config:aws
