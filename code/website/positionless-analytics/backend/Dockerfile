FROM python:3.11-slim

WORKDIR /app

# System deps for pyarrow / catboost
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libgomp1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Model and JSON data are volume-mounted at runtime:
#   -v $(pwd)/outputs:/outputs
#   -v $(pwd)/output:/output
#   -v $(pwd)/data:/data

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]