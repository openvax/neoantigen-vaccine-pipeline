#!/bin/bash

SNAKEFILE=/pipeline/Snakefile
CONFIGFILE=/inputs/config.json
TARGETS=$@

snakemake \
-s $SNAKEFILE \
--cores=2 \
--resources mem_mb=100000 \
--configfile $CONFIGFILE \
--config workdir=/outputs \
-np \
$TARGETS
