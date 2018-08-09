FROM python:3.6

COPY ./get_famous_people_photos/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

RUN apt-get update && apt-get install -y ca-certificates

COPY ./get_famous_people_photos/src /app/src
COPY ./common/text_files /app/src
COPY ./common/models /app/models
WORKDIR /app/src

CMD ["python", "get_famous_people_photos.py"]