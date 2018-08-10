FROM python:3.6

COPY ./get_famous_people_photos/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt && \
    apt-get update && apt-get install -y ca-certificates

COPY /src /app/get_famous_people_photos/src
COPY ../common/text_files /app/common/text_files
COPY ../common/models /app/common/models
WORKDIR /app/get_famous_people_photos/src

CMD ["python", "get_famous_people_photos.py"]
