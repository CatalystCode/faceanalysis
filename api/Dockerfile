FROM python:3.4-slim

WORKDIR /app
COPY . /app

RUN apt-get -y update \
    && apt-get install -y mysql-client \
    && apt-get clean && rm -rf /tmp/* /var/tmp/* \ 
    && pip install -r requirements.txt

#RUN pip install mysql-connector-python \
#    flask \
#    sqlalchemy \
#    flask-restful \
#    gunicorn \
#    azure-storage-queue
#    passlib \
#    Flask-HTTPAuth
EXPOSE 5000
ENTRYPOINT ["/bin/bash", "/app/run.sh"]
