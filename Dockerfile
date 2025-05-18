FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5165

# Add health check
HEALTHCHECK --interval=1m --timeout=10s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:5165/token_info.json || exit 1

CMD ["python", "smartthings_token_server.py"]
