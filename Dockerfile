# Use Python 3.11+ base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY ontology/ ./ontology/
COPY validation/ ./validation/
COPY data/ ./data/

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh

# Create output directory
RUN mkdir -p /app/output

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose API port
EXPOSE 8000

# Set Python path to include src directory
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Set entrypoint to run startup initialization and then start API service
ENTRYPOINT ["/app/entrypoint.sh"]
