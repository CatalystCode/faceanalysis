FROM python:3.6

WORKDIR /app
RUN apt-get update && apt-get install -y unzip
RUN wget "https://redcrossstorage.blob.core.windows.net/models/insightface.zip" && \
    unzip insightface.zip

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY vectorize.py .

ENTRYPOINT ["python3", "vectorize.py"]
