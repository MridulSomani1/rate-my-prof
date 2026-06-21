# =============================================================================
# Dockerfile — builds the container image GCP Cloud Run will run.
# =============================================================================

# Start from a small, official Python image.
FROM python:3.12-slim

# Don't write .pyc files and flush logs straight to the console (better for Cloud Run logs).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# All app files live here inside the container.
WORKDIR /app

# Install dependencies first so Docker can cache this layer between builds.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Cloud Run sends traffic to the port in the $PORT env var (defaults to 8080).
ENV PORT=8080
EXPOSE 8080

# Start the app with gunicorn. "app:app" = the `app` object inside app.py.
# Shell form is used so $PORT gets expanded at runtime.
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 120 app:app
