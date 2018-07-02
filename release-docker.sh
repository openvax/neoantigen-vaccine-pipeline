#!/bin/bash
#
# This script will tag the last-built Docker image with the version currently specified in the
# VERSION file and push the new image to DockerHub, with the tag "latest" and the version tag.

set -ex

# docker hub username
USERNAME=julia326
# image name
IMAGE=neoantigen-vaccine-pipeline

# Get latest version
version=`cat docker/VERSION`
echo "version: $version"

docker tag $USERNAME/$IMAGE:latest $USERNAME/$IMAGE:$version
docker push $USERNAME/$IMAGE:latest
docker push $USERNAME/$IMAGE:$version
