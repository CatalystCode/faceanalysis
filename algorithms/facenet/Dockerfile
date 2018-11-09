FROM python:3.6

WORKDIR /app

RUN wget "https://redcrossstorage.blob.core.windows.net/models/facenet_model.pb"

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY vectorize.py .

ENTRYPOINT ["python3", "vectorize.py"]
