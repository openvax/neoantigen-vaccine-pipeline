from __future__ import print_function, division, absolute_import
from argparse import ArgumentParser
import datetime
import json
from os import access, R_OK, W_OK
from os.path import isfile, join

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
parser.add_argument(
    "--dry-run",
    help="If this argument is present, Snakemake will do a dry run of the pipeline",
    action="store_true")

def get_output_dir(config):
    return join(config["workdir"], config["input"]["id"])

def compute_vaxrank_targets(config):
    return [
        # TODO(julia): add mutect2 vaxrank report to this
        join(get_output_dir(config), "vaccine-peptide-report-mutect-strelka.txt"),
    ]

def check_inputs(config):
    """
    Check that the paths specified in the config exist and are readable.
    """
    # check inputs
    for sample_type in ["tumor", "normal", "rna"]:
        if sample_type not in config["input"]:
            continue
        for fragment in config["input"][sample_type]:
            if fragment["type"] == "paired-end":
                for read_num in ["r1", "r2"]:
                    r = fragment[read_num]
                    if not (isfile(r) and access(r, R_OK)):
                        raise ValueError("File %s does not exist or is unreadable", r)
            elif fragment["type"] == "single-end":
                r = fragment["r"]
                if not (isfile(r) and access(r, R_OK)):
                    raise ValueError("File %s does not exist or is unreadable", r)
            else:
                raise ValueError("Unsupported fragment type: %s", fragment["type"])

    # check reference genome files
    for key in config["reference"]:
        ref_file = config["reference"][key]
        if not (isfile(ref_file) and access(ref_file, R_OK)):
            raise ValueError("Reference genome file %s does not exist or is unreadable", ref_file)

    # check that the workdir exists and is writable
    workdir = config["workdir"]
    if not access(workdir, W_OK):
        raise ValueError("Workdir %s does not exist or is not writable", workdir)


def run():
    args = parser.parse_args()
    print(args)

    with open(args.configfile) as configfile:
        config = json.load(configfile)
    output_dir = get_output_dir(config)

    check_inputs(config)
    # check target
    targets = args.target
    if targets is None:
        targets = compute_vaxrank_targets(config)
        targets = [
            # TODO(julia): add mutect2 vaxrank report to this
            join(output_dir, "vaccine-peptide-report-mutect-strelka.txt"),
        ]

    start_time = datetime.datetime.now()
    snakemake.snakemake(
        args.snakefile,
        cores=args.cores,
        resources={'mem_mb': 160000},
        configfile=args.configfile,
        config={'num_threads': args.cores},
        printshellcmds=True,
        dryrun=args.dry_run,
        targets=targets,
        stats=join(output_dir, "stats.json"),
    )
    end_time = datetime.datetime.now()
    print("--- Pipeline running time: %s ---" % (str(end_time - start_time)))


if __name__ == "__main__":
    run()
