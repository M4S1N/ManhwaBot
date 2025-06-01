# Use an official Node.js runtime as a parent image
FROM n8nio/n8n:latest

# Use environment variables to set up the N8N configuration
ENV N8N_BASIC_AUTH_ACTIVE=true
ENV N8N_BASIC_AUTH_USER=admin
ENV N8N_BASIC_AUTH_PASSWORD=admin
ENV N8N_HOST=manhwa-bot-n8n
ENV N8N_PORT=${PORT:-5678}
ENV N8N_SECURE_COOKIE=false
ENV N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true
ENV N8N_RUNNERS_ENABLED=true
ENV N8N_LOG_LEVEL=debug
ENV N8N_ENCRYPTION_KEY=CpEMNDGDE9cRi8KP1mM0rkDLBIyAUPH3
ENV WEBHOOK_URL=https://manhwabot-agent.onrender.com

# ENV DB_TYPE=postgresdb
# ENV DB_POSTGRESDB_HOST=manhwabot-postgres.onrender.com
# ENV DB_POSTGRESDB_PORT=5432
# ENV DB_POSTGRESDB_USER=n8n_user
# ENV DB_POSTGRESDB_PASSWORD=n8n_password
# ENV DB_POSTGRESDB_DATABASE=n8n_db

# Copy the credentials file to the container
COPY ./n8n_credentials.json /workflows/n8n_credentials.json
COPY ./n8n_workflow.json /workflows/n8n_workflow.json

# Excecute import and then start the service
ENTRYPOINT [ "sh", "-c", "n8n import:workflow --input /workflows/n8n_workflow.json && n8n import:credentials --input /workflows/n8n_credentials.json && n8n update:workflow --id eca1GMRSKykhf4P1 --active=true && n8n start" ]
