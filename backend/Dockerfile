# Backend image: FastAPI served by uvicorn on port 8000.
FROM python:3.12-slim

WORKDIR /backend

# Install dependencies first so Docker can cache this layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code and the saved January 2026 data.
COPY app ./app
COPY data ./data

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
