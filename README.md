# Demo Instructions
1. Create an Azure VM (preferably Ubuntu 16.04)
2. Install Docker and Docker Compose
3. Clone this repo
4. Replace default environment variables in environment_variables.yml
5. From the directory containing docker-compose.yml run the command 'docker-compose build'
6. Run the command 'docker-compose up'

# Workflow
1. Register your user by making a POST request to /api/register_user with a 'username' and 'password'
2. Optionally retrieve a token by making a GET request to /api/token with your username:password in the Authentication header
3. Access all other resources by passing your_token:any_value in the Authentication header (using Basic Auth) or by passing username:password for each request
4. Upload an image by making a POST request to /api/upload_image
5. Process an image by making a POST request to /api/process_image
6. Check the status of the image to see if it is finished processing by making a GET request to /api/process_image (once the image is finished processing, it will be removed from the host file system)
7. See which other images are matches by making a GET request to api/image_matches
# Architecture
![Alt text](/architecture_diagram/architecture_diagram.jpeg?raw=true "Architecture Diagram")
