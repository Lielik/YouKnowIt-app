# Build stage - installs dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

# Copy requirements first - so dependencies aren't reinstalled on every code change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --target=/app/packages

# Final stage — lean image
FROM python:3.12-slim

WORKDIR /app

# Copy installed dependencies from build stage into a shared location
COPY --from=builder /app/packages /app/packages

# Copy application code
COPY app/ ./app/

# Add packages to Python path so they can be imported
ENV PYTHONPATH=/app/packages
ENV PATH=/app/packages/bin:$PATH

# Don't run as root — security best practice
RUN useradd --create-home appuser && \
    chown -R appuser:appuser /app
USER appuser

# Port the app listens on
EXPOSE 8000

# Start the app with uvicorn
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]