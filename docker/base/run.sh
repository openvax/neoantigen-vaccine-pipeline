#!/bin/bash

# Usage:
# - config.json file describing Snakemake pipeline inputs, relative to Docker volume paths
# - set of Snakemake targets

SNAKEFILE=/pipeline/Snakefile
CONFIGFILE=$1
TARGETS="${@:2}"

snakemake \
-s $SNAKEFILE \
--cores=22 \
--resources mem_mb=100000 \
--configfile $CONFIGFILE \
--config workdir=/outputs \
-p \
$TARGETS
