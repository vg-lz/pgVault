FROM python:3.12-slim

# Keep container output readable and avoid writing bytecode files into layers.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install PgVault runtime and test dependencies from the shared requirements.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application package, legacy modules, docs, and tests.
COPY . .

# Default behavior for Compose is to run the catalog scan and print JSON.
CMD ["python", "-m", "pgvault", "scan"]
