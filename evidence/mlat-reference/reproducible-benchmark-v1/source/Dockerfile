FROM python:3.12.11-slim@sha256:47ae396f09c1303b8653019811a8498470603d7ffefc29cb07c88f1f8cb3d19f

WORKDIR /app

# Copy locked requirements first for deterministic dependency caching
COPY requirements.lock .
COPY pyproject.toml .

# Install only distributions whose hashes are recorded in the lockfile
RUN pip install --no-cache-dir --require-hashes -r requirements.lock

# Copy application code
COPY src/ ./src/
COPY .env.example ./

# Build isolation would resolve build dependencies outside the lockfile.
RUN pip install --no-cache-dir --no-deps --no-build-isolation .

RUN mkdir -p /app/data /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose API port
EXPOSE 5000

CMD ["mlat-processor"]
