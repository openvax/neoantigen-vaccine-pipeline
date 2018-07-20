# Copyright (c) 2018. Mount Sinai School of Medicine
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function, division, absolute_import
from argparse import ArgumentParser
import datetime

from os import access, R_OK, W_OK
from os.path import isfile, join, basename, splitext
import sys

import psutil
import snakemake
import yaml


def total_memory_gb():
    n_bytes = psutil.virtual_memory().total
    return n_bytes / (1024 * 1024 * 1024)

parser = ArgumentParser()

parser.add_argument(
    "--configfile",
    default="",
    help="Docker-relative Snakemake YAML config file path")

parser.add_argument(
    "--target",
    action="append",
    help="Snakemake target(s). For multiple targets, can specify --target t1 --target t2 ...")

parser.add_argument(
    "--somatic-variant-calling-only",
    help=(
        "If this argument is present, will only call somatic variants - "
        "no RNA processing or final vaccine peptide computation"),
    action="store_true")

parser.add_argument(
    "--snakefile",
    default="snakemake/Snakefile",
    help="Docker-relative path to Snakefile")

parser.add_argument(
    "--cores",
    default=max(1, psutil.cpu_count() - 1),
    type=int,
    help="Number of CPU cores to use in this pipeline run (default %(default)s)")

parser.add_argument(
    "--memory",
    default=max(1.0, total_memory_gb() - 1),
    type=float,
    help="Total memory (in GB) allowed for use by the Snakemake scheduler (default %(default)s)")

parser.add_argument(
    "--dry-run",
    help="If this argument is present, Snakemake will do a dry run of the pipeline",
    action="store_true")


def get_output_dir(config):
    return join(config["workdir"], config["input"]["id"])


def default_vaxrank_targets(config):
    mhc_predictor = config["mhc_predictor"]
    vcfs = "-".join(config["variant_callers"])
    path_without_ext = join(
        get_output_dir(config),
        "vaccine-peptide-report_%s_%s" % (mhc_predictor, vcfs))
    return ['%s.%s' % (path_without_ext, ext) for ext in ('txt', 'json', 'pdf', 'xlsx')]


def somatic_vcf_targets(config):
    return [
        join(get_output_dir(config), "%s.vcf" % vcf_type)
        for vcf_type in config["variant_callers"]
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
                        raise ValueError("File %s does not exist or is unreadable" % r)
            elif fragment["type"] == "single-end":
                r = fragment["r"]
                if not (isfile(r) and access(r, R_OK)):
                    raise ValueError("File %s does not exist or is unreadable" % r)
            else:
                raise ValueError("Unsupported fragment type: %s" % fragment["type"])

    # check reference genome files
    for key in config["reference"]:
        ref_file = config["reference"][key]
        if not (isfile(ref_file) and access(ref_file, R_OK)):
            raise ValueError("Reference genome file %s does not exist or is unreadable" % ref_file)

    # check that the workdir exists and is writable
    workdir = config["workdir"]
    if not access(workdir, W_OK):
        raise ValueError("Workdir %s does not exist or is not writable" % workdir)


# Contains validation specific to pipeline config details
def check_target_against_config(target, config):
    if not target.startswith(get_output_dir(config)):
        raise ValueError("Invalid target, must start with output directory: %s" % target)
    if "vaccine-peptide-report" in target and target not in default_vaxrank_targets(config):
        raise ValueError(
            "Invalid target, vaccine peptide output must match config file specs: %s" % target)
    # if the target is a VCF file, make sure it's in the config
    root, ext = splitext(basename(target))
    if ext == ".vcf" and "germline" not in root and root not in config["variant_callers"]:
        raise ValueError(
            "Invalid target, must be part of config file variant_callers: %s" % root)


# Contains validation specific to runtime args: memory/CPU resources, etc.
def check_target_against_args(target, args):
    if args.memory < 6.5:
        raise ValueError("Must provide at least 6.5GB RAM")
    # if any of the targets are RNA or vaxrank report outputs, needs >=32GB RAM
    # TODO: don't just match the target on starting with 'rna' since we might
    # be doing something like seq2hla that doesn't require as much memory
    if "vaccine-peptide-report" in target or basename(target).startswith("rna"):
        if args.memory < 32:
            raise ValueError(
                "Must provide at least 32GB RAM for RNA processing or full peptide computation")
        if args.somatic_variant_calling_only:
            raise ValueError(
                "Cannot request --somatic-variant-calling-only in combination with any RNA "
                "processing or vaccine peptide targets")


def main(args_list=None):
    if args_list is None:
        args_list = sys.argv[1:]
    args = parser.parse_args(args_list)
    print(args)

    with open(args.configfile) as configfile:
        config = yaml.load(configfile)
    output_dir = get_output_dir(config)

    targets = args.target
    if targets is None:
        if args.somatic_variant_calling_only:
            targets = somatic_vcf_targets(config)
        else:
            targets = default_vaxrank_targets(config)

    # input validation
    check_inputs(config)
    if len(targets) == 0:
        raise ValueError("Must specify at least one target")
    for target in targets:
        check_target_against_config(target, config)
        check_target_against_args(target, args)

    start_time = datetime.datetime.now()
    if not snakemake.snakemake(
        args.snakefile,
        cores=args.cores,
        resources={'mem_mb': int(1024 * args.memory)},
        configfile=args.configfile,
        config={'num_threads': args.cores, 'mem_gb': args.memory},
        printshellcmds=True,
        dryrun=args.dry_run,
        targets=targets,
        stats=join(output_dir, "stats.json"),
    ):
        raise ValueError("Pipeline failed, see Snakemake error message for details")

    end_time = datetime.datetime.now()
    print("--- Pipeline running time: %s ---" % (str(end_time - start_time)))


if __name__ == "__main__":
    main()
