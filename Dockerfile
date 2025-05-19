# Use the official Python 3.12 image as a base
FROM python:3.12-slim

# Set environment variables for Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-dev \
    libpq-dev \
    postgresql \
    curl \
    authbind \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 5432

COPY . /app
RUN mkdir /app/voxai/node_modules && mkdir /app/voxai/client/node_modules && chown -R postgres:postgres /app && chmod -R 755 /app/

# Configure authbind for port 80
RUN touch /etc/authbind/byport/80 && \
    chmod 500 /etc/authbind/byport/80 && \
    chown root /etc/authbind/byport/80

USER postgres

ENV PATH="/var/lib/postgresql/.local/bin:$PATH"

RUN service postgresql restart && \
    psql -c "CREATE USER linux WITH SUPERUSER ENCRYPTED PASSWORD 'password';" && \
    psql -c "CREATE USER root WITH SUPERUSER;" && \
    psql -c "CREATE DATABASE voxai_db WITH OWNER linux;"

# Install and set up nvm and node
ENV NVM_DIR=/var/lib/postgresql/.nvm
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash && \
    . "$NVM_DIR/nvm.sh" && \
    nvm install node

RUN echo 'export NVM_DIR="$HOME/.nvm"' >> ~/.bashrc && \
    echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm' >> ~/.bashrc && \
    echo 'nvm install node' >> ~/.bashrc && \
    echo 'service postgresql restart' >> ~/.bashrc \
    echo "RUN sed -i \'s/venv\\/bin\\/flask/flask/g\' /app/voxai/package.json" >> ~/.bashrc

# Copy the entire project
WORKDIR /app

# Install Python dependencies
COPY voxai/server/requirements.txt .
RUN pip install --upgrade wheel setuptools && \
    pip install -r requirements.txt

# Install Node.js dependencies
RUN . $NVM_DIR/nvm.sh && npm install --prefix voxai/client

RUN . $NVM_DIR/nvm.sh && npm install --prefix voxai

COPY voxai/credentials.json /root/.aws/credentials.json
RUN mkdir /var/lib/postgresql/.aws
COPY voxai/credentials.json /var/lib/postgresql/.aws/credentials.json
RUN sed -i 's/venv\/bin\/flask/flask/g' voxai/package.json

# Expose ports
EXPOSE 80
EXPOSE 5000

# Update working directory for bash 
WORKDIR /app/voxai

# Initialize database

RUN rm -rf server/src/migrations
RUN service postgresql restart && . $NVM_DIR/nvm.sh && echo "Initialize database\n\n" | npm run migrate || true

# Set the entrypoint to authbind
ENTRYPOINT ["authbind"]
