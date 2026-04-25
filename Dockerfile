FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/home/app \
    DATA_CSV_PATH=/var/data/science.adu3198_data_s4.csv

RUN groupadd --system app \
    && useradd --system --gid app --create-home --home-dir /home/app app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

USER app
EXPOSE 8000

CMD [ \
    "gunicorn", \
    "-k", "uvicorn.workers.UvicornWorker", \
    "-w", "2", \
    "-b", "0.0.0.0:8000", \
    "--timeout", "120", \
    "app.main:app" \
]
