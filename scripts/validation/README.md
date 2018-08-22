# Instructions
* The validation script requires python 3.7
    * If using [anaconda](https://www.anaconda.com/download/), create a virtual environment with ```conda create -n py37 python=3.7```
    * Activate the virtual environment with ```conda activate py37```
    * Install requirements with ```pip install -r requirements.txt```
* Example to run validation script: ```python validate.py --image_dir /images --container_name the_algorithm_container --distance_metric ANGULAR_DISTANCE --pairs_fname /pairs/pairs.txt --threshold_start 0 --threshold_end 4 --threshold_step 0.01 --embedding_size 128 --threshold_metric ACCURACY --prealigned_flag --remove_empty_embeddings_flag```
