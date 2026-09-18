FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN pip install --no-cache-dir "jsonschema>=4.21" "pytest>=8.0"
COPY . .

CMD ["python", "-m", "runner.mock_slice"]
