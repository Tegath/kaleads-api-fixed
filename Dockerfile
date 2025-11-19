# Dockerfile for Kaleads Atomic Agents API

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY data/ ./data/
COPY .env.example .env

# Copy city CSV files for comprehensive scraping
COPY Villes_france.csv ./
COPY Villes_belgique.csv ./

# Expose port
EXPOSE 20001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:20001/health || exit 1

# Run the application
CMD ["uvicorn", "src.api.n8n_optimized_api:app", "--host", "0.0.0.0", "--port", "20001"]
