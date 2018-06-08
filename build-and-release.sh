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

./build.sh

# Get latest version
version=`cat docker/VERSION`
echo "version: $version"

git tag -a "$version" -m "version $version"
git push
git push --tags

docker tag $USERNAME/$IMAGE:public $USERNAME/$IMAGE:$version
docker push $USERNAME/$IMAGE:public
docker push $USERNAME/$IMAGE:$version
