FROM python:3.6

RUN apt-get update && \
    apt-get install -y wget ca-certificates

RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir spacy && \
    python3 -m spacy download en_core_web_lg

COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

RUN mkdir -p /app/common/text_files
RUN wget -P /app/common/text_files https://redcrossstorage.blob.core.windows.net/textfiles/famous_people.txt.gz
RUN wget -P /app/common/text_files https://redcrossstorage.blob.core.windows.net/textfiles/country_demonyms.txt

COPY src /app/get_famous_people_list/src
WORKDIR /app/get_famous_people_list/src

CMD ["python3", "get_famous_people_list.py"]
