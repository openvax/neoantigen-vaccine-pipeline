# neoantigen-vaccine-pipeline

Snakemake implementation of the PGV vaccine pipeline, powering the PGV001 and GBM vaccine trials.

## Setup

This repo includes the [pip requirements file](https://github.com/openvax/neoantigen-vaccine-pipeline/blob/master/requirements.txt) as well as a [Conda environment spec](https://github.com/openvax/neoantigen-vaccine-pipeline/blob/master/conda-spec-file.txt). Note that to get started with pipeline development and rule definition, you just need the Python dependencies:
```
pip install -r requirements.txt
```
### Full setup

If you want to run the pipeline with all its tools, you'll need access to a machine that already has a full pipeline setup. This can be one of:
- demeter-csmaz11-19 (most frequently used PGV node)
- demeter-csmaz11-18
- demeter-csmaz11-16

(Alternatively, follow [these instructions](https://github.com/openvax/neoantigen-vaccine-pipeline/blob/master/snakemake/notes.txt) to set up a new Linux machine that will be able to run the full pipeline, but proceed at your own risk - those instructions may be incomplete and assume some tool/data dependencies that aren't fully documented yet. See list below.)

Once you SSH into a pipeline-enabled machine, make a new environment from which to run everything:
```
# this will create a Conda env with bfx dependencies and Python 3.5.4
conda create --name <env> --file conda-spec-file.txt
source activate <env>
pip install -r requirements.txt
```

An extra step is needed to set up GATK in this new environment. Find the path of the `gatk` binary using `which gatk`, then edit that file  and set the value of `jar_file` to 'GenomeAnalysisTK_37.jar'). After that, run:
```
gatk-register /data/biokepi-work-dir/workdir/toolkit/gatk.NOVERSION/GenomeAnalysisTK_37.jar
```
## Testing

### Unit test

You can run a small local unit test which simulates a pipeline dependency graph and does not require bioinformatics tool setup. Once you clone this repo and install the Python requirements, run `nosetests`.

### Data test

If you're on a pipeline-enabled machine and you've gone through the environment setup, dry-run the full pipeline on test data:
```
cd snakemake
snakemake \
--configfile idh1_config.json \
--resources mem_mb=160000 \
--cores 24 \
-np \
/data/pipeline/workdir/idh1-test-sample/vaccine-peptide-report.txt
```
This will print all the commands and list the rules that would be triggered to make the vaccine peptide report. If you want to really run the pipeline, run with `-p` instead of `-np`. This will take up to half an hour on a Demeter machine, start to finish (FASTQ inputs to Vaxrank report).

To run a subset of the pipeline, change the target to an upstream file. For example, to run just BWA alignment and mark dups on normal DNA inputs, run the above command with `/data/pipeline/workdir/idh1-test-sample/normal_aligned_coordinate_sorted_dups.bam` instead of the vaccine peptide report path.


## Tool and data dependencies

Partial list:
- MuTect (v1)
- Strelka
- MHC prediction tools, unless you're using MHCflurry
- Reference genome data

See [setup notes](https://github.com/openvax/neoantigen-vaccine-pipeline/blob/master/snakemake/notes.txt) for instructions on how to set up a Linux box with dependencies not covered by the Conda and pip specs.



