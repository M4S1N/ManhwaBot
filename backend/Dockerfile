# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# copiar deps para cachear
COPY poetry.lock pyproject.toml /app/

RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libpq-dev curl \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir poetry \
 && poetry config virtualenvs.create false \
 && poetry install --no-interaction --without dev

# copiar el código
COPY . .

# definimos un puerto por defecto, que Railway sobreescribirá en tiempo de ejecución
ENV PORT=7013

# en producción es mejor usar Gunicorn con el worker de Uvicorn
RUN poetry add gunicorn uvicorn

EXPOSE 7013

# arrancar con Gunicorn+UvicornWorker, escuchando en la variable $PORT
ENTRYPOINT ["sh", "-c"]
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${PORT:-7013}", "--workers", "1"]
