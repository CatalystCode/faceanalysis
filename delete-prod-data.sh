#!/usr/bin/env bash
sudo rm -rf persisted_data/prod
sudo mkdir persisted_data/prod

sudo mkdir persisted_data/prod/database
sudo mkdir persisted_data/prod/images

sudo touch persisted_data/prod/database/.gitkeep
sudo touch persisted_data/prod/images/.gitkeep
