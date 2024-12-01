# Use the official Python image as the base image
FROM python:3.12-slim

# Set environment variables to prevent Python from buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set the working directory in the container
WORKDIR /app

# Copy only requirements first (leverage Docker caching)
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN apt-get update && apt-get install -y python3 python3-pip && \
    pip3 install --no-cache-dir --upgrade pip && pip3 install --no-cache-dir -r requirements.txt

# Copy application code to the container
COPY . /app

# Expose the port Flask runs on
EXPOSE 5000

# Command to run the app with Gunicorn
CMD ["python", "app.py"]