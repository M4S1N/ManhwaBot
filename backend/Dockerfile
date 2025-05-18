# syntax=docker/dockerfile:1
############################################
# 1) Builder: instala deps via Poetry
############################################
FROM python:3.11-slim AS builder

# Variables de entorno para Poetry y pycache limpio
ENV PYTHONUNBUFFERED=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

# Instalamos compiladores necesarios, curl para Poetry y limpiamos caches de apt
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl \
 && rm -rf /var/lib/apt/lists/*

# Instalamos Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Ponemos Poetry en el PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Copiamos los manifests de deps y los instalamos (sin dev)
COPY pyproject.toml poetry.lock /app/
RUN poetry install --no-interaction --without dev

############################################
# 2) Runtime: imagen liviana con solo lo necesario
############################################
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PORT=7013

WORKDIR /app

# Solo certs y limpieza de apt
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Copiamos el entorno de Python desde builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiamos el código de la aplicación
COPY . /app

# Exponemos el puerto que Railway inyecta en $PORT
EXPOSE ${PORT}

# Comando de arranque: Uvicorn puro, 1 worker, loop uvloop y http httptools
CMD ["gunicorn", "app.main:app", \
     "--bind", "0.0.0.0:7013", \
     "--workers", "1", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--timeout", "180", \
     "--log-level", "warning"]
