# neoantigen-vaccine-pipeline

Snakemake implementation of the PGV vaccine pipeline, powering the PGV001 and GBM vaccine trials.

## Setup

This repo includes the [pip requirements file](https://github.com/openvax/neoantigen-vaccine-pipeline/blob/master/requirements.txt) as well as a [Conda environment spec](https://github.com/openvax/neoantigen-vaccine-pipeline/blob/master/conda-spec-file.txt). Note that to get started with pipeline development and rule definition, you just need the Python dependencies:
```
pip install -r requirements.txt
```

### Dockerized pipeline

Note that this relies on a private Docker image which contains the necessary tool dependencies. This is not ready for external users.

Prerequisites for us:
- Installed Docker (for how to do this on Debian, see https://docs.docker.com/install/linux/docker-ce/debian/#set-up-the-repository)
- A JSON file containing the private key describing the bhardwaj-lab service account.
- A machine with at least 16 cores and 1TB free disk space.

Set up service account access to bhardwaj-lab buckets:
```
gcloud auth activate-service-account --key-file bhardwaj-lab.json
```

Data downloads:
- Test data from gs://pgv-test-data: this contains an example Snakemake config as well as a couple of FASTQs you can try running on
- Reference genome data from gs://reference-genomes. Download this and put in a world-writeable directory (the pipeline will preprocess the reference as needed, and write the results to that same directory)

Make a world-writeable outputs directory; this will contain sample-specific pipeline output.

Add the current user to the docker group, if necessary; then log into Docker Hub (`docker login`) to be able to use the private Docker image.

Example pipeline command (replace these host volume paths with yours):
```
docker run \
-v /home/julia/pipeline_inputs:/inputs \
-v /home/julia/pipeline_outputs:/outputs \
-v /home/julia/reference-genomes:/reference-genome \
julia326/neoantigen-vaccine-pipeline:wip \
--configfile=/inputs/idh1_config.json
```

## Testing

### Unit test

You can run a small local unit test which simulates a pipeline dependency graph and does not require bioinformatics tool setup. Once you clone this repo and install the Python requirements, run `nosetests`.

### Data test (deprecated, needs updating; ignore for now)

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


## Tool and data dependencies (deprecated, needs updating; ignore for now)

Partial list:
- MuTect (v1)
- Strelka
- MHC prediction tools, unless you're using MHCflurry
- Reference genome data

See [setup notes](https://github.com/openvax/neoantigen-vaccine-pipeline/blob/master/snakemake/notes.txt) for instructions on how to set up a Linux box with dependencies not covered by the Conda and pip specs.



