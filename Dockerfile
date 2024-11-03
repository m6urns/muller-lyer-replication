# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for numpy/matplotlib
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir \
    apscheduler \
    pandas \
    numpy \
    matplotlib \
    seaborn

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variables
ENV FLASK_APP=app.py
ENV DATA_DIR=/app/data

# Create necessary directories
RUN mkdir -p /app/data \
    && mkdir -p /app/static/images/stats \
    && chmod -R 777 /app/static/images/stats

# Create a script to run both the stats updater and Gunicorn
RUN echo '#!/bin/bash\n\
python3 -c "from stats_updater import StatsUpdater; updater = StatsUpdater(); updater.start()" & \n\
gunicorn --bind 0.0.0.0:5000 app:app\n\
' > /app/start.sh \
    && chmod +x /app/start.sh

# Run the start script when the container launches
CMD ["/app/start.sh"]