# Use a lightweight Python base
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies (useful for debugging and future-proofing)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# (Ensure your requirements.txt has: openenv-core pydantic openai pytest)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Hugging Face Spaces require exposing port 7860
EXPOSE 7860

# Start the OpenEnv server using our manifest
CMD ["openenv", "serve", "openenv.yaml", "--host", "0.0.0.0", "--port", "7860"]
