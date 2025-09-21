# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy your FastAPI application code into the container
COPY ./ /app

# Install FastAPI and Uvicorn, which is a popular ASGI server
RUN pip install  -r /app/requirements.txt
RUN pip install celery

# Avoid prompts during package installations
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary packages
RUN apt-get update && \
    apt-get install -y vim tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Reset the environment variable for any future interactive use
ENV DEBIAN_FRONTEND=

# Expose the port that Uvicorn will listen on (default is 8000)
EXPOSE 8000

ENV PYTHONPATH=/

# Copy the startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Define the command to start your FastAPI application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--timeout-keep-alive", "4000", "--reload"]                                                                                                                          
