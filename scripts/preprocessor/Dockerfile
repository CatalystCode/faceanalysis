FROM python:3.6

COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

COPY src /app/preprocessor/src

WORKDIR /app/preprocessor/src

ENTRYPOINT ["python3", "main.py"]
