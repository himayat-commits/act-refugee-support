FROM python:3.10-slim

WORKDIR /app

# Use lightweight requirements for deployment
COPY requirements-light.txt .
RUN pip install --no-cache-dir -r requirements-light.txt

COPY . .

# Set environment variables
ENV USE_LIGHTWEIGHT=true
ENV USE_LOCAL_EMBEDDINGS=false

# Start the API server
CMD ["python", "api_server.py"]
