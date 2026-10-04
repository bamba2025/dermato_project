FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/pyproject.toml backend/pyproject.toml
COPY backend/app backend/app
RUN pip install --no-cache-dir ./backend && useradd --uid 10001 --create-home derma
COPY backend/alembic.ini backend/alembic.ini
COPY backend/migrations backend/migrations
COPY worker worker
USER derma
WORKDIR /app/backend
ENV PYTHONPATH=/app:/app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
