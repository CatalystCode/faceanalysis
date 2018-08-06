FROM python:3.4-slim

RUN apt-get -y update \
    && apt-get install -y mysql-client \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

#RUN pip install mysql-connector-python \
#    flask \
#    sqlalchemy \
#    flask-restful \
#    gunicorn \
#    azure-storage-queue
#    passlib \
#    Flask-HTTPAuth
EXPOSE 5000
ENTRYPOINT ["./wait-for-dependencies.sh"]
CMD ["gunicorn", "--bind=0.0.0.0:5000", "wsgi"]
