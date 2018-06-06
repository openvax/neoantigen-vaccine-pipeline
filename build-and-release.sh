#!/bin/bash

# This script will build the Docker image, tag it with the version currently specified in the
# VERSION file and push the new image to DockerHub. It will also push a release to GitHub with a tag
# matching the version.
#
# Usage:
# ./release.sh <mhcbundle GitHub password>

set -ex

# docker hub username
USERNAME=julia326
# image name
IMAGE=neoantigen-vaccine-pipeline

# Get latest version
version=`cat docker/base/VERSION`
echo "version: $version"
# Build image
docker build --build-arg MHCBUNDLE_PASS=$1 -t $USERNAME/$IMAGE:latest -f docker/base/Dockerfile .

git tag -a "$version" -m "version $version"
git push
git push --tags

docker tag $USERNAME/$IMAGE:latest $USERNAME/$IMAGE:$version
docker push $USERNAME/$IMAGE:latest
docker push $USERNAME/$IMAGE:$version
