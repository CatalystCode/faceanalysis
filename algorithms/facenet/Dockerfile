FROM python:3.6

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY vectorize.py .
RUN wget "https://redcrossstorage.blob.core.windows.net/images/facenet_model.pb"

ENTRYPOINT ["python3", "vectorize.py"]
