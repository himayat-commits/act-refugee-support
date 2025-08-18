FROM python:3.10-slim

WORKDIR /app

# Use lightweight requirements for deployment
COPY requirements-light.txt .
RUN pip install --no-cache-dir -r requirements-light.txt

COPY . .

# Set environment variables
ENV USE_LIGHTWEIGHT=true
# OpenAI API key must be provided at runtime via .env or environment variable

# Start the API server
CMD ["python", "run_api.py"]
