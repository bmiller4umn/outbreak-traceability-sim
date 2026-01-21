# Build stage for frontend
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend
RUN npm run build

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy Python project files
COPY pyproject.toml ./
COPY outbreak_traceability_sim/ ./outbreak_traceability_sim/

# Install Python dependencies
RUN pip install --no-cache-dir ".[web]"

# Copy built frontend from build stage
COPY --from=frontend-build /app/frontend/dist ./static

# Expose port
EXPOSE 8000

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8000

# Run the application
CMD ["python", "-m", "uvicorn", "outbreak_traceability_sim.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
