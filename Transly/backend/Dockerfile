FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# libpq-dev + gcc are required to build asyncpg/psycopg-related wheels on
# some platforms; ffmpeg provides ffprobe, used to validate uploaded
# videos (format/duration) before they are sent to Gemini. Kept minimal
# and removed from the apt cache afterwards.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
