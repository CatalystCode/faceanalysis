# This is a sample Dockerfile you can modify to deploy your own app based on face_recognition

FROM python:3.4-slim

RUN apt-get -y update \
    && apt-get install -y --fix-missing \
        build-essential \
        cmake \
        gfortran \
        git \
        wget \
        curl \
        graphicsmagick \
        libgraphicsmagick1-dev \
        libatlas-dev \
        libavcodec-dev \
        libavformat-dev \
        libboost-all-dev \
        libgtk2.0-dev \
        libjpeg-dev \
        liblapack-dev \
        libswscale-dev \
        pkg-config \
        python3-dev \
        python3-numpy \
        software-properties-common \
        zip \
        mysql-client \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/* \
    && cd ~ \
    && mkdir -p dlib \
    && git clone -b 'v19.7' --single-branch https://github.com/davisking/dlib.git dlib/ \
    && cd  dlib/ \
    && python3 setup.py install --yes USE_AVX_INSTRUCTIONS

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
#RUN pip install mysql-connector-python \
#    sqlalchemy \
#    Pillow \
#    imageio \
#    azure-storage-queue \
#    numpy \
#    scipy \
#    face_recognition \
#    passlib \
#    Flask-HTTPAuth \
#    requests
EXPOSE 5000
ENTRYPOINT ["/bin/bash", "/app/run.sh"]
