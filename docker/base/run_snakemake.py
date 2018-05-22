from __future__ import print_function, division, absolute_import
from argparse import ArgumentParser
import json
import os
import datetime

import snakemake

parser = ArgumentParser()
parser.add_argument(
    "--configfile",
    default="",
    help="Docker-relative Snakemake JSON config file path")
parser.add_argument(
    "--target",
    action="append",
    help="Snakemake target(s). For multiple targets, can specify --target t1 --target t2 ...")
parser.add_argument(
    "--snakefile",
    default="snakemake/Snakefile",
    help="Docker-relative path to Snakefile")
parser.add_argument(
    "--cores",
    default=22,
    type=int,
    help="Number of CPU cores to use in this pipeline run")

def compute_vaxrank_targets(config_file_path):
    """
    configfile: Docker-relative path to a JSON config file
    """
    with open(config_file_path) as configfile:
        config = json.load(configfile)
        output_dir = os.path.join(config["workdir"], config["input"]["id"])
        targets = [
            # TODO(julia): add mutect2 vaxrank report to this
            os.path.join(output_dir, "vaccine-peptide-report-mutect-strelka.txt"),
        ]
        return targets

if __name__ == "__main__":
    args = parser.parse_args()
    print(args)

    # check target
    targets = args.target
    if targets is None:
        targets = compute_vaxrank_targets(args.configfile)

    start_time = datetime.datetime.now()
    snakemake.snakemake(
        args.snakefile,
        cores=args.cores,
        resources={'mem_mb': 160000},
        configfile=args.configfile,
        config={'num_threads': args.cores},
        printshellcmds=True,
        targets=targets,
    )
    end_time = datetime.datetime.now()
    print("--- Pipeline running time: %s ---" % (str(end_time - start_time)))
