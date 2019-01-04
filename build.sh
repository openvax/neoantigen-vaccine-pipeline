#!/bin/bash

# This script will build the public Docker image, tagging it as latest.

set -ex

# docker hub username
USERNAME=openvax
# image name
IMAGE=neoantigen-vaccine-pipeline
# directory of this script
BASEDIR=$(dirname "$0")

# Build image
docker build -t $USERNAME/$IMAGE:latest -f $BASEDIR/docker/Dockerfile .
