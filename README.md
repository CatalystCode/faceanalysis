# Demo Instructions
1. Create an Azure VM (preferably Ubuntu 16.04)
2. Install Docker and Docker Compose
3. Clone this repo
4. Replace default environment variables in docker-compose.yml
5. From the directory containing docker-compose.yml run the command 'docker-compose build'
6. Run the command 'docker-compose up'
7. Once output stops printing, navigate to http://YOUR_VM_IP_ADDRESS
8. Click on one of the original images to see cropped images
9. Click on one of the cropped images to see all the matches
10. Click on one of the matches to see the original image it came from
11. When finished, press ctrl-d to stop the docker containers and optionally execute the script cleanup.sh to properly remove persisted data

# Gotchas
- Uploaded images must have the following file name: img_id.jpg. Do not choose any img_id between 0 and 10. For instance, 11.jpg works fine.
- After clicking upload, wait and the image will appear in the grid of original images (it takes a few seconds to be analyzed)
- The cleanup.sh script does not remove images you upload yourself
    - To get rid of them, run 'rm -f persisted_data/images/input/img_id.jpg' ('git status' will let you know if you need to manually remove them)
- If there are duplicate images:
    - The queue may not have been clear when you ran 'docker-compose up'
    - Someone may be using the same queue as you
    - You forgot to delete persistant data after your previous run. Run cleanup.sh and 'git status' to ensure your repo is clean.

# Architecture
![Alt text](/architecture_diagram/architecture_diagram.jpeg?raw=true "Architecture Diagram")
