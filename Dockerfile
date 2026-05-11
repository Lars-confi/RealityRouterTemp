# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY reality-router/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set environment variables
# We default to the standard location, which will be mapped to a volume
ENV REALITY_ROUTER_HOME=/root/.reality_router
ENV PYTHONPATH=/app/reality-router

# Create the directory for persistent data
RUN mkdir -p /root/.reality_router

# Expose port 8000 for the FastAPI server
EXPOSE 8000

# Run uvicorn when the container launches
# Note: We run from the reality-router directory to match the local setup expectations
WORKDIR /app/reality-router
CMD ["python3", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
