FROM python:3.6

COPY ./get_famous_people_list/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN python -m spacy download en_core_web_lg

COPY ../common/text_files/  /app/common/text_files
COPY ./get_famous_people_list/src /app/get_famous_people_list/src
WORKDIR /app/get_famous_people_list/src


CMD ["python", "get_famous_people_list.py"]