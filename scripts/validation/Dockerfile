# https://getintodevops.com/blog/the-simple-way-to-run-docker-in-docker-for-ci
FROM python:3.6-slim
RUN apt-get update && \
apt-get -y install apt-transport-https \
     ca-certificates \
     curl \
     gnupg2 \
     software-properties-common && \
curl -fsSL https://download.docker.com/linux/$(. /etc/os-release; echo "$ID")\
/gpg > /tmp/dkey; apt-key add /tmp/dkey && \
add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/\
$(. /etc/os-release; echo "$ID") $(lsb_release -cs) stable" && \
apt-get update && \
apt-get -y install docker-ce
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY src /app/validation/src
WORKDIR /app/validation/src
CMD ["/bin/sh", "-c", "python validate.py --image_dir $IMAGE_DIR \
--container_name $CONTAINER_NAME --distance_metric $DISTANCE_METRIC \
--pairs_fname $PAIRS_FNAME --threshold_start $THRESHOLD_START --threshold_end \
$THRESHOLD_END --threshold_step $THRESHOLD_STEP --embedding_size \
$EMBEDDING_SIZE --threshold_metric $THRESHOLD_METRIC $PREALIGNED_FLAG \
$REMOVE_EMPTY_EMBEDDINGS_FLAG"]
