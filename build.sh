#!/bin/bash

# This script will build the public Docker image.

set -ex

# docker hub username
USERNAME=julia326
# image name
IMAGE=neoantigen-vaccine-pipeline

# Build image
docker build -t $USERNAME/$IMAGE:public -f docker/Dockerfile .
