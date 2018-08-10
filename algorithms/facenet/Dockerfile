FROM python:3.6-slim-stretch

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY vectorize.py .
COPY 20180402-114759.pb .

ENTRYPOINT ["python3", "vectorize.py"]
