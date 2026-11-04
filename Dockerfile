FROM python:3.12-slim-bookworm
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HOST=0.0.0.0 PORT=3000 ASSINAJA_DATA_DIR=/data/assinaja ASSINAJA_SECURE_COOKIES=1
COPY server.py /app/server.py
COPY public /app/public
COPY deploy/railway_start.py /app/deploy/railway_start.py
RUN chmod -R a+rX /app
# O entrypoint prepara somente a pasta de dados da aplicação e abandona root.
CMD ["python3", "/app/deploy/railway_start.py"]
