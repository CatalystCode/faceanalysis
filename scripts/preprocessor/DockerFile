FROM python:3.6

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY main.py .
COPY processor.py .

ENTRYPOINT ["python3", "main.py"]