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
import logging

from os import access, R_OK, W_OK
from os.path import dirname, isfile, join, basename, splitext
import psutil
import sys
import tempfile

import snakemake
import yaml

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Returns an integer value for total available memory, in GB.
def total_memory_gb():
    n_bytes = psutil.virtual_memory().total
    return int(n_bytes / (1024 * 1024 * 1024))

parser = ArgumentParser()

parser.add_argument(
    "--configfile",
    default="",
    help="Snakemake YAML config file path")

parser.add_argument(
    "--target",
    action="append",
    help="Snakemake target(s). For multiple targets, can specify --target t1 --target t2 ...")

parser.add_argument(
    "--somatic-variant-calling-only",
    help="If this argument is present, will only call somatic variants - no RNA processing "
        "or final vaccine peptide computation",
    action="store_true")

parser.add_argument(
    "--process-reference-only",
    help="If this argument is present, will only process the input reference files - no pipeline "
        "run beyond that",
    action="store_true")

parser.add_argument(
    "--cores",
    default=max(1, psutil.cpu_count() - 1),
    type=int,
    help="Number of CPU cores to use in this pipeline run (default %(default)s)")

parser.add_argument(
    "--memory",
    default=max(1, total_memory_gb() - 1),
    type=int,
    help="Total memory (in GB) allowed for use by the Snakemake scheduler (default %(default)s)")

parser.add_argument(
    "--dry-run",
    help="If this argument is present, Snakemake will do a dry run of the pipeline",
    action="store_true")

overrides_group = parser.add_argument_group("Dockerless runs: directory override options")

# TODO(julia): make sure that if any of these is specified, all the others are too
overrides_group.add_argument(
    "--inputs",
    default="",
    help="Directory that should be treated as /inputs: mimicking Docker volume mounting")

overrides_group.add_argument(
    "--outputs",
    default="",
    help="Directory that should be treated as /outputs: mimicking Docker volume mounting")

overrides_group.add_argument(
    "--reference-genome",
    default="",
    help="Directory that should be treated as /reference-genome: mimicking Docker volume mounting")


def get_output_dir(config):
    return join(config["workdir"], config["input"]["id"])


def get_reference_genome_dir(config):
    return dirname(config["reference"]["genome"])


######################################################################################
#########################          Validation        #################################
######################################################################################


def validate_config(config):
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


def validate_target(target, args, config):
    if args.memory < 6.5:
        raise ValueError("Must provide at least 6.5GB RAM")

    output_dir = get_output_dir(config)
    reference_genome_dir = get_reference_genome_dir(config)

    if target.startswith(reference_genome_dir):
        if args.memory < 32:
            raise ValueError(
                "Must provide at least 32GB RAM for reference genome processing")

    elif target.startswith(output_dir):
        if "vaccine-peptide-report" in target and target not in default_vaxrank_targets(config):
            raise ValueError(
                "Invalid target, vaccine peptide output must match config file specs: %s" % target)
        # if the target is a somatic VCF file, make sure it's in the config
        root, ext = splitext(basename(target))
        if ext == ".vcf" and not "germline" in root and not root in config["variant_callers"]:
            raise ValueError(
                "Invalid target, somatic VCF must be part of config file "
                "variant_callers: %s" % target)

        # if any of the targets are RNA or vaxrank report outputs, needs >=32GB RAM
        if "vaccine-peptide-report" in target or basename(target).startswith("rna"):
            if args.memory < 32:
                raise ValueError(
                    "Must provide at least 32GB RAM for RNA processing or full peptide computation")
            if args.somatic_variant_calling_only:
                raise ValueError(
                    "Cannot request --somatic-variant-calling-only in combination with any RNA "
                    "processing or vaccine peptide targets")

    else:
        raise ValueError(
            "Invalid target %s, must start with output (%s) or genome (%s) directory" % (
                target, output_dir, reference_genome_dir))


######################################################################################
#########################          Target processing        ##########################
######################################################################################


def default_vaxrank_targets(config):
    mhc_predictor = config["mhc_predictor"]
    vcfs = "-".join(config["variant_callers"])
    path_without_ext = join(
        get_output_dir(config),
        "vaccine-peptide-report_%s_%s" % (mhc_predictor, vcfs))
    return ['%s.%s' % (path_without_ext, ext) for ext in ('txt', 'json', 'pdf', 'xlsx')]


def somatic_vcf_targets(config):
    return [join(
        get_output_dir(config),
        "%s.vcf" % vcf_type
        ) for vcf_type in config["variant_callers"]]


def get_and_check_targets(args, config):
    targets = args.target
    if targets is None:
        if args.somatic_variant_calling_only:
            targets = somatic_vcf_targets(config)
        elif args.process_reference_only:
            targets = [config["reference"]["genome"] + ".done"]
        else:
            targets = default_vaxrank_targets(config)
    
    if len(targets) == 0:
        raise ValueError("Must specify at least one target")

    # in all cases, run FASTQC
    fastqc_target = join(get_output_dir(config), "fastqc.done")
    if fastqc_target not in targets:
        targets.append(fastqc_target)
    
    for target in targets:
        validate_target(target, args, config)
    return targets


######################################################################################
#########################          Execution         #################################
######################################################################################


def run_neoantigen_pipeline(args, parsed_config, configfile):
    configfile.seek(0)

    output_dir = get_output_dir(parsed_config)
    stats_file = join(output_dir, "stats.json")

    # only run targets in the output directory (exclude reference processing)
    targets = [x for x in get_and_check_targets(args, parsed_config) if x.startswith(output_dir)]
    if not targets:
        logger.info("No output targets specified")
        return

    logger.info("Running neoantigen pipeline with targets %s " % targets)

    # include all relevant contigs in the pipeline config
    with open(parsed_config["reference"]["genome"] + ".contigs") as f:
        contigs = [x.strip() for x in f.readlines()]

    # parse out targets that start with output directory (not reference)
    start_time = datetime.datetime.now()
    if not snakemake.snakemake(
            'pipeline/Snakefile',
            cores=args.cores,
            resources={'mem_mb': int(1024 * args.memory)},
            config={'num_threads': args.cores, 'mem_gb': args.memory, 'contigs': contigs},
            configfile=configfile.name,
            printshellcmds=True,
            dryrun=args.dry_run,
            targets=targets,
            stats=stats_file):
        raise ValueError("Pipeline failed, see Snakemake error message for details")

    end_time = datetime.datetime.now()
    logger.info("--- Pipeline running time: %s ---" % (str(end_time - start_time)))


def process_reference(args, parsed_config, configfile):
    configfile.seek(0)

    reference_genome_dir = get_reference_genome_dir(parsed_config)
    stats_file = join(reference_genome_dir, "stats.json")

    # only run targets in the reference directory (exclude output processing)
    targets = [
        x for x in get_and_check_targets(args, parsed_config) if x.startswith(reference_genome_dir)]
    if not targets:
        targets = [parsed_config["reference"]["genome"] + '.done']
    logger.info("Processing reference with targets: %s" % targets)

    start_time = datetime.datetime.now()
    if not snakemake.snakemake(
            'pipeline/reference_Snakefile',
            cores=args.cores,
            resources={'mem_mb': int(1024 * args.memory)},
            config={'num_threads': args.cores, 'mem_gb': args.memory},
            configfile=configfile.name,
            printshellcmds=True,
            dryrun=args.dry_run,
            targets=targets,
            stats=stats_file):
        raise ValueError("Reference processing failed, see Snakemake error message for details")
    end_time = datetime.datetime.now()
    logger.info("--- Reference processing time: %s ---" % (str(end_time - start_time)))


def main(args_list=None):
    if args_list is None:
        args_list = sys.argv[1:]
    args = parser.parse_args(args_list)
    logger.info(args)

    with open(args.configfile) as configfile:
        configfile_contents = configfile.read()

    # if necessary, replace paths in the configfile contents
    if args.inputs or args.outputs or args.reference_genome:
        if not (args.inputs and args.outputs and args.reference_genome):
            raise ValueError(
                "For a Dockerless run, must specify all overrides: --inputs, --outputs, and "
                "--reference-genome")
        # replace /outputs, /reference-genome, /inputs paths in config with user-specified dirs
        configfile_contents = configfile_contents.replace(
            '/outputs', args.outputs).replace(
            '/reference-genome', args.reference_genome).replace(
            '/inputs', args.inputs)

    parsed_config = yaml.load(configfile_contents)
    validate_config(parsed_config)

    with tempfile.NamedTemporaryFile(mode='w') as config_tmpfile:
        config_tmpfile.write(configfile_contents)
        logger.info("Processing reference...")
        process_reference(args, parsed_config, config_tmpfile)
        if args.process_reference_only:
            if args.target is not None:
                raise ValueError("If requesting --process-reference-only, cannot specify targets")
        else:
            logger.info("Running main pipeline...")
            run_neoantigen_pipeline(args, parsed_config, config_tmpfile)
    

if __name__ == "__main__":
    main()
