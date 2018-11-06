FROM python:3.6

RUN apt-get update && \
    apt-get install -y wget ca-certificates

COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r /app/requirements.txt

RUN mkdir -p /app/common/{text_files,models,images}
RUN wget -P /app/common/text_files https://redcrossstorage.blob.core.windows.net/textfiles/famous_people.txt.gz
RUN wget -P /app/common/text_files https://redcrossstorage.blob.core.windows.net/textfiles/image_urls.data
RUN wget -P /app/common/models https://redcrossstorage.blob.core.windows.net/models/facenet_model.pb

COPY src /app/get_famous_people_photos/src
WORKDIR /app/get_famous_people_photos/src

CMD ["python3", "get_famous_people_photos.py"]
