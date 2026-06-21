# =============================================================================
# Dockerfile — Hugging Face Spaces deployment.
# HF Spaces routes traffic to port 7860 and runs containers as a non-root user.
# =============================================================================

FROM python:3.9

# HF Spaces best practice: run as a non-root user with uid 1000.
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Create the working directory AFTER switching users so `user` owns it
# (the app writes reviews.db here on startup).
WORKDIR /app

# Install dependencies first for better build caching.
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY --chown=user . .

# HF Spaces expects the app on port 7860.
EXPOSE 7860

# Start the Flask app.
CMD ["python", "app.py"]
