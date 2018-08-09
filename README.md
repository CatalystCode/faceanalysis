[![Travis CI status](https://api.travis-ci.org/c-w/faceanalysis.svg?branch=master)](https://travis-ci.org/c-w/faceanalysis)

# Testing and evaluating face detection algorithms

See [here](./algorithms/README.md).

# Demo Instructions
1. Create an Azure VM (preferably Ubuntu 16.04)
2. Install Docker and Docker Compose
3. Clone this repo
4. Replace default configuration values in `.env` and `secrets.env`
5. To run tests type './run-test.sh' from within the top level directory
6. To run in production type './run-prod.sh' from within the top level directory
7. If you would like to clear the production database, run './delete-prod-data.sh'
- Each time you run in production, **you most likely do not want to delete the production database**. Therefore, when you run './run-prod.sh', the previous database will not be deleted. You have the option to manually delete it by running './delete-prod-data.sh'

# Workflow
1. Register your user by making a POST request to /api/v1/register_user with a 'username' and 'password'
2. Optionally retrieve a token by making a GET request to /api/v1/token with your username:password in the Authentication header
3. Access all other resources by passing your_token:any_value in the Authentication header (using Basic Auth) or by passing username:password for each request
4. Upload an image by making a POST request to /api/v1/upload_image
5. Process an image by making a POST request to /api/v1/process_image
6. Check the status of the image to see if it is finished processing by making a GET request to /api/v1/process_image (once the image is finished processing, it will be removed from the host file system)
7. See which other images are matches by making a GET request to api/v1/image_matches

# Notes
1. Logs and log rotation are handled by docker, and the specifics can be seen in either docker-compose file
- To make docker handle logs, the nginx base image creates a symbolic link between the console and the files (access.log and error.log) that normally store logs. Similarly, our defined Dockerfile for mysql creates a symbolic link between the console and the files (error.log) that normally store logs
- As is default, only mysql error logging is turned on
- The api service's logs are written to the console via python's logging module, so docker handles them as well
2. Before deploying into production, consider deleting the script "delete-prod-data.sh", so that no one accidentally deletes the production database
3. The unit tests in the api service provide clarity if there is any question regarding the workflow
