# Instructions

## Without docker
* The validation script requires python 3.7
    * If using [anaconda](https://www.anaconda.com/download/), create a virtual environment with ```conda create -n py37 python=3.7```
    * Activate the virtual environment with ```conda activate py37```
    * Install requirements with ```pip install -r requirements.txt```
* Example to run validation script: ```python validate.py --image_dir /images --container_name the_algorithm_container --distance_metric ANGULAR_DISTANCE --pairs_fname /pairs/pairs.txt --threshold_start 0 --threshold_end 4 --threshold_step 0.01 --embedding_size 128 --threshold_metric ACCURACY --prealigned_flag --remove_empty_embeddings_flag```

## With docker
* The validation script uses [docker-py](https://pypi.org/project/docker/) to call the algorithm container. Instead of running a docker container inside of another docker container, this solution uses [sibling containers](https://getintodevops.com/blog/the-simple-way-to-run-docker-in-docker-for-ci)
    * To run sibling containers, we mount the host machine's docker socket in the container. Docker commands from within the container will be handled by the host machine's daemon. 
* Build the docker image with ```docker build -t validation .``` (in the directory with the Dockerfile)
* An example of running the container:
```
docker run -it \
-v /aligned/images:/aligned/images \
-v /aligned/pairs/pairs.txt:/aligned/pairs/pairs.txt \
-v /var/run/docker.sock:/var/run/docker.sock \
-e IMAGE_DIR=/aligned/images \
-e CONTAINER_NAME=the_algorithm_container \
-e PAIRS_FNAME=/aligned/pairs/pairs.txt \
-e DISTANCE_METRIC=ANGULAR_DISTANCE \
-e THRESHOLD_START=0 \
-e THRESHOLD_END=4 \
-e THRESHOLD_STEP=0.01 \
-e EMBEDDING_SIZE=128 \
-e THRESHOLD_METRIC=ACCURACY \
-e REMOVE_EMPTY_EMBEDDINGS_FLAG=--remove_empty_embeddings_flag \
-e PREALIGNED_FLAG=--prealigned_flag \
validation
```
