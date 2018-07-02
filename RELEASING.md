# Releasing neoantigen-vaccine-pipeline

This document explains what do once your [Pull Request](https://www.atlassian.com/git/tutorials/making-a-pull-request/) has been reviewed and all final changes applied. Now you're ready merge your branch into master and release it to the world:

1. Make sure that your last PR included a version increment, in the [Version](https://github.com/openvax/neoantigen-vaccine-pipeline/blob/master/docker/VERSION) file. If it didn't, open another PR to increment the version. Use [semantic versioning](http://semver.org/).
2. Run `./build.sh` to build a new Docker image.
3. Run `./release-docker.sh` to release the Docker image tagged with the most recent version, as well as updating the image under the `latest` tag.
4. Run `./release-github.sh` to do a GitHub repo release with that same version.
