FROM python:3.6-slim

RUN apt-get -y update \
    && apt-get install -y \
        mysql-client \
        python3-numpy \
        curl \
        jq \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ARG DEVTOOLS=false
COPY requirements-dev.txt .
RUN if [ "$DEVTOOLS" = "true" ]; then pip install --no-cache-dir -r requirements-dev.txt; fi

COPY . /app

EXPOSE 5000
ENTRYPOINT ["./wait-for-dependencies.sh"]
CMD ["./run-app.sh"]
