# Use a slim version of Python 3.11
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app 

# Copy the dependency files to the container at /app
COPY poetry.lock pyproject.toml /app/

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir poetry

# Install the application dependencies
RUN poetry install --no-interaction --without dev

# Copy the rest of the application code to the container at /app
COPY . .

# Railway injects the $PORT variable, so
# we set it to 7013 (your local port) by default
ARG PORT=7013
ENV PORT=${PORT}

# Expose the port the app runs on
EXPOSE ${PORT}

# This command starts the FastAPI application using Uvicorn, binding to all interfaces on port 7013 and enabling auto-reload for development.
CMD ["poetry", "run", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
