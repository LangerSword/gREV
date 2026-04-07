# Use a lightweight Python base
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install uv (The new package manager Meta is using)
RUN pip install uv

# Copy the entire project into the container
COPY . .

# Hugging Face Spaces require exposing port 7860
EXPOSE 7860

# Run the OpenEnv server using the exact 'uv' command requested
CMD ["uv", "run", "--project", ".", "server", "--host", "0.0.0.0", "--port", "7860"]
