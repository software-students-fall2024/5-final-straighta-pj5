# Dockerfile for Flask App

# Base Image from Docker Hub
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libssl-dev libffi-dev python3-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt to the container
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV SECRET_KEY=your_default_secret_key
ENV MONGO_URI=mongodb://mongo:27017/

# Expose the port that the Flask app runs on
EXPOSE 3000

# Run the application
CMD ["flask", "run", "--host=0.0.0.0", "--port=3000"]
