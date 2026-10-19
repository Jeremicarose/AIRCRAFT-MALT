FROM python:3.12.11-slim@sha256:47ae396f09c1303b8653019811a8498470603d7ffefc29cb07c88f1f8cb3d19f

WORKDIR /app

# Copy locked requirements first for deterministic dependency caching
COPY requirements.lock .
COPY pyproject.toml .
COPY README.md LICENSE ./

# Install only distributions whose hashes are recorded in the lockfile
RUN pip install --no-cache-dir --require-hashes -r requirements.lock

# Copy application code
COPY src/ ./src/
COPY tools/ ./tools/
COPY reference/mlat/benchmarks/ ./reference/mlat/benchmarks/
COPY evidence/mlat-reference/compact-public-solver-v2/ ./evidence/mlat-reference/compact-public-solver-v2/
COPY evidence/registry-v2-testnet-2026-09-11-data1-final/ ./evidence/registry-v2-testnet-2026-09-11-data1-final/
COPY .env.example ./

# Build isolation would resolve build dependencies outside the lockfile.
RUN pip install --no-cache-dir --no-deps --no-build-isolation .

RUN groupadd --gid 10001 mlat && useradd --uid 10001 --gid mlat --create-home mlat \
    && chmod 700 /home/mlat \
    && mkdir -p /app/data /app/logs && chown -R mlat:mlat /app/data /app/logs
USER mlat

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose API port
EXPOSE 5000

CMD ["mlat-processor"]
