# SaaS Opportunity Bot Agent - Dockerfile for ottomator Live Agent Studio
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (metadata only, Railway uses PORT env var)
EXPOSE 8001

# Run the agent via uvicorn, using Railway's PORT env var, default 8001
CMD ["sh", "-c", "uvicorn agent.saas_agent:app --host 0.0.0.0 --port ${PORT:-8001}"]
