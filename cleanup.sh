#!/usr/bin/env bash
sudo rm -rf persisted_data/database/data
sudo mkdir persisted_data/database/data
sudo touch persisted_data/database/data/.gitkeep

sudo rm -rf persisted_data/images/output
sudo mkdir persisted_data/images/output
sudo touch persisted_data/images/output/.gitkeep