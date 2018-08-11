FROM python:3.6

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY vectorize.py .
COPY 20180402-114759.pb .

ENTRYPOINT ["python3", "vectorize.py"]
