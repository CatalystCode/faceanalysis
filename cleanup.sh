#!/usr/bin/env bash
sudo rm -rf persisted_data/database
sudo mkdir persisted_data/database
sudo touch persisted_data/database/.gitkeep

sudo rm -rf persisted_data/images/output
sudo mkdir persisted_data/images/output
sudo touch persisted_data/images/output/.gitkeep

sudo rm -rf persisted_data/logs
sudo mkdir persisted_data/logs
sudo touch persisted_data/logs/.gitkeep
