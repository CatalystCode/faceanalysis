#!/usr/bin/env bash
sudo rm -rf persisted_data/prod_database
sudo mkdir persisted_data/prod_database
sudo touch persisted_data/prod_database/.gitkeep

sudo rm -rf persisted_data/test_database
sudo mkdir persisted_data/test_database
sudo touch persisted_data/test_database/.gitkeep

sudo rm -rf persisted_data/images
sudo mkdir persisted_data/images
sudo touch persisted_data/images/.gitkeep
