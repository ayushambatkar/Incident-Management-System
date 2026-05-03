FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
COPY README.md /app/README.md
COPY .env.example /app/.env.example

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
