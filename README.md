# neoantigen-vaccine-pipeline

Snakemake implementation of the PGV vaccine pipeline.

## Setup

To get started with pipeline development and rule definition, you only need the Python dependencies:
```
pip install -r requirements.txt
```
## Testing

You can run a small local unit test which simulates a pipeline dependency graph and does not require Docker. Once you clone this repo and install the Python requirements, run:
```
nosetests
```

## Dockerized pipeline

### Prerequisites

Make sure to have the following:
- A machine with at least 16 cores and 1TB free disk space
- Docker installed on that machine

Also please note that the Docker setup is supported for the following Debian distributions:
- Buster 10 (Docker CE 17.11 Edge only)
- Stretch 9 (stable) / Raspbian Stretch
- Jessie 8 (LTS) / Raspbian Jessie
- Wheezy 7.7 (LTS)

And the following Ubuntu distributions:
- Artful 17.10 (Docker CE 17.11 Edge and higher only)
- Xenial 16.04 (LTS)
- Trusty 14.04 (LTS)

For how to install Docker on Debian, see https://docs.docker.com/install/linux/docker-ce/debian/#set-up-the-repository.

### 1. Download this data for getting started with the pipeline:

- `gs://pgv-test-data`: this contains an example Snakemake config and small test tumor/normal FASTQ files
- `gs://reference-genomes`: reference genomes data

Download this and put in a world-writeable directory (the pipeline will preprocess the reference as needed, and write the results to that same directory)

### 2. Create a pipeline outputs directory; this will contain sample-specific pipeline output.

### 3. Note that your outputs and reference genome directory must be recursively world writable:
```
chmod -R a+w <reference genome dir>
chmod -R a+w <outputs dir>
```
This is necessary because the Docker pipeline runs as an internal Docker user and not as you, so it needs write privileges. Data is modified in the outputs directory as well as in the reference genome: preparing the reference genome for use by BWA/GATK/etc. will save the results to the genome directory.

### 4. Run the Docker pipeline.

This is an example pipeline command which uses the test Snakemake config you downloaded, and runs the full pipeline including Vaxrank:
```
docker run \
-v <your inputs dir>:/inputs \
-v <your outputs dir>:/outputs \
-v <your reference genome dir>:/reference-genome \
julia326/neoantigen-vaccine-pipeline:latest \
--configfile=/inputs/idh1_config.json
```

If you want to poke around in the image to execute tools manually, look at tool versions, etc.:
```
docker run \
-v <your inputs dir>:/inputs \
-v <your outputs dir>:/outputs \
-v <your reference genome dir>:/reference-genome \
--entrypoint /bin/bash -it \
julia326/neoantigen-vaccine-pipeline:latest
```

### Intermediate files

As a result of the full pipeline run, many intermediate files are generated in the output directory. In case you want to reuse these for a different pipeline run (e.g. if you have one normal sample and several tumor samples, each of which you want to run against the normal), any intermediate file you copy to the new location will tell Snakemake to not repeat that step (or its substeps, unless they're needed for some other workflow node). For that reason, it's helpful to know the intermediate file paths. You can also run parts of the pipeline used to generate any of the intermediate files, specifying one or more as a target to the Docker run invocation. Example, if you use [the test IDH config](https://github.com/openvax/neoantigen-vaccine-pipeline/blob/master/test/idh1_config.json):
```
docker run \
-v <your inputs dir>:/inputs \
-v <your outputs dir>:/outputs \
-v <your reference genome dir>:/reference-genome \
julia326/neoantigen-vaccine-pipeline:latest \
--configfile=/inputs/idh1_config.json \
--target=/outputs/idh1-test-sample/tumor_aligned_coordinate_sorted_dups_indelreal_bqsr.bam \
--target=/outputs/idh1-test-sample/normal_merged_aligned_coordinate_sorted.bam
```
This (somewhat arbitrary) example will run alignment on normal DNA, and alignment + full GATK process on the tumor DNA.

Here are some of the intermediate file names you might use as targets, in a sample's output directory. Listed in "chronological" order:
- `{normal,tumor,rna}_merged_aligned_coordinate_sorted.bam`: after BWA alignment, merging of lanes if necessary
- `{normal,tumor,rna}_aligned_coordinate_sorted_dups.bam`: after GATK MarkDups
- `{normal,tumor}_aligned_coordinate_sorted_dups_indelreal.bam`: after GATK IndelRealigner
- `{normal,tumor}_aligned_coordinate_sorted_dups_indelreal_bqsr.bam`: after GATK BQSR. These are inputs to variant callers.
- `rna_aligned_coordinate_sorted_dups_cigar_N_filtered.bam`: after GATK MarkDups, filtered to all tumor RNA reads with Ns in the CIGAR string (will not run IndelRealigner on these)
- `rna_aligned_coordinate_sorted_dups_cigar_0-9MIDSHPX_filtered.bam`: after GATK MarkDups, all tumor RNA reads without Ns
- `rna_cigar_0-9MIDSHPX_filtered_sorted_indelreal.bam`: tumor RNA after GATK IndelRealigner
- `rna_final_sorted.bam`. This is RNA after all processing; used as input to `vaxrank`.
- `{mutect,mutect2,strelka}.vcf`: merged (all-contig) VCF from corresponding variant caller. Use e.g. `mutect_10.vcf` to only call Mutect variants in chromosome 10.
- `vaccine-peptide-report-mutect.vcf`: run `vaxrank` with only Mutect variants. The pipeline supports running `vaxrank` with any combination of Mutect/Mutect2/Strelka. To specify this, use `mutect`, `strelka`, `mutect2` separated by a dash - e.g. to run with all 3 variant callers, use `vaccine-peptide-report-mutect-strelka-mutect2.vcf`.
