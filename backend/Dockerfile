# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 1) Copiamos solo las deps para cachear
COPY poetry.lock pyproject.toml /app/

RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libpq-dev curl \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir poetry \
 # instalamos uvicorn en el entorno de Poetry
 && poetry add uvicorn gunicorn \
 && poetry config virtualenvs.create false \
 && poetry install --no-interaction --without dev

# 2) Copiamos el resto del código
COPY . .

# Exponemos el puerto
EXPOSE $PORT

# 3) ENTRYPOINT + CMD en exec‐form para Poetry + Uvicorn
ENTRYPOINT ["sh","-c"]
CMD ["poetry run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7013}"]
