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
* Ensure that the_algorithm_container is built
* An example of running the container:
```docker run -v /aligned/images:/aligned/images -v /aligned/pairs/pairs.txt:/aligned/pairs/pairs.txt -v /var/run/docker.sock:/var/run/docker.sock --image_dir /aligned/images --container_name the_algorithm_container --distance_metric ANGULAR_DISTANCE --pairs_fname /aligned/pairs/pairs.txt --threshold_start 0 --threshold_end 4 --threshold_step 0.01 --embedding_size 128 --threshold_metric ACCURACY --prealigned_flag --remove_empty_embeddings_flag```
* Note: when mapping volumes, the volumes in the host and container **must have the same path**

## With docker-compose
* Replace values in .env
* Run docker-compose up
