#!/bin/bash

# This script will build the public Docker image, tagging it as latest.

set -ex

# docker hub username
USERNAME=openvax
# image name
IMAGE=neoantigen-vaccine-pipeline

# Build image
docker build -t $USERNAME/$IMAGE:latest -f docker/Dockerfile .
