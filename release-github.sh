#!/bin/bash
#
# This script will push a release to GitHub with a tag matching the version.
#
# Note that if a GitHub release already exists with this version tag, this script will error.
# Also, this script MUST be run from this repository!

set -ex

# Get latest version
version=`cat docker/VERSION`
echo "version: $version"

git tag -a "$version" -m "version $version"
git push
git push --tags
