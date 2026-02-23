FROM apache/airflow:2.8.1-python3.11

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
  gcc \
  libpq-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Set working directory for your project
WORKDIR /opt/project


ENV PYTHONPATH="/opt/project"

# Copy and install Python dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt