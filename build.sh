#!/bin/bash

# This script will build the public Docker image, tagging it as latest.

set -ex

# docker hub username
USERNAME=hremon331046
IMAGE_TAG=d0.4.2-mhc2-flexible-cutoff-v1.0.2
# image name
IMAGE=neoantigen-vaccine-pipeline
# directory of this script
BASEDIR=$(dirname "$0")

# Build image
docker build -t $USERNAME/$IMAGE:$IMAGE_TAG -f $BASEDIR/docker/Dockerfile .
