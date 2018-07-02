# neoantigen-vaccine-pipeline

This repository is the public version of the bioinformatics pipeline for selecting patient-specific cancer neoantigen vaccines developed by the [openvax](https://www.openvax.org/) group at [Mount Sinai](http://icahn.mssm.edu/). This pipeline is currently the basis for two phase I clinical trials using synthetic long peptides, [NCT02721043](https://clinicaltrials.gov/ct2/show/NCT02721043) and [NCT03223103](https://clinicaltrials.gov/ct2/show/NCT03223103).

The pipeline used for these trials differs slightly from the version given here due to licensing restrictions on the [NetMHC](http://www.cbs.dtu.dk/services/NetMHC/) suite of tools, which prevent their inclusion in the provided Docker image. To circumvent this issue, the open source pipeline performs MHC binding prediction using the IEDB web interface to these tools. This may be slower but should give the same results. If you have a license to the NetMHC tools (free for non-commerical use) and wish to run these tools locally in the pipeline, please contact us or file an issue.

The pipeline is implemented using the [Snakemake](https://snakemake.readthedocs.io/en/stable/) workflow management system. We recommend running it using our provided [Docker image](https://hub.docker.com/r/julia326/neoantigen-vaccine-pipeline/), which includes all needed dependencies.

# Overview

This pipeline assumes you have the following datasets.

* Tumor and normal whole exome sequencing. In our trials, we target 300X tumor coverage, 150X normal.
* Tumor RNA sequencing. We target 100M reads for fresh samples (using poly-A capture) and 300M reads for FFPE samples (using Ribo-Zero).
* List of MHC class I alleles for the individual.
* Reference genome and associated files (COSMIC, dbSNP, known transcripts). As a convenience, we provide these files for GRCh37. 

The steps performed by the workflow are as follows.

* Tumor and normal whole exome sequencing FASTQ files are aligned to GRCh37+decoy (b37decoy) using [bwa mem](http://bio-bwa.sourceforge.net/). RNA-seq of the tumor sample is aligned by [STAR](https://academic.oup.com/bioinformatics/article/29/1/15/272537) to the same reference genome.
* Aligned tumor and normal exome reads pass through several steps using GATK 3.7: MarkDuplicates, IndelRealigner, BQSR.
* Aligned RNA-seq reads are grouped into two sets: those spanning introns and those aligning entirely within an exon (determined based on the CIGAR string). The latter group is passed through IndelRealigner, and the two groups of reads are merged.
* Somatic variant calling is performed by running Mutect 1.1.7, Mutect 2, and/or Strelka version 1. The user is expected to specify which of those 3 variant callers the pipeline should run.
* [Vaxrank](https://github.com/openvax/vaxrank) is run, using the combined VCFs from all variant callers and the aligned RNA reads.

## Running using Docker

For best results, you will need a machine with at least 16 cores and 1TB free disk space, and Docker [installed](https://docs.docker.com/install/).

The pipeline is run by invoking a Docker entrypoint in the image while providing three directories as mounted Docker [volumes](https://docs.docker.com/storage/volumes/): `/inputs` (FASTQ files and a configuration YAML), `/outputs` (directory to write results to), and `/reference-genome` (data shared across patients, such as the genome reference).

Note that all three directories and their contents must be world writable. This is necessary because the Docker pipeline runs as an unprivileged user and not as you. Data is modified in the `outputs` directory as well as in the `reference-genome` directory, since indexing the reference genome for use by aligners and other tools requires writing results to this directory.

First we will download the reference data for b37decoy.

```sh
mkdir -p reference-genome/b37decoy
cd reference-genome/b37decoy
wget https://github.com/openvax/neoantigen-vaccine-pipeline/releases/download/pre-public/b37decoy.fasta.gz
wget https://github.com/openvax/neoantigen-vaccine-pipeline/releases/download/pre-public/cosmic.vcf
wget https://github.com/openvax/neoantigen-vaccine-pipeline/releases/download/pre-public/dbsnp.vcf.gz
wget https://github.com/openvax/neoantigen-vaccine-pipeline/releases/download/pre-public/transcripts.gtf.gz
cd ../..
chmod -R a+w reference-genome
```

Now we will download a test sequencing dataset, consisting of a YAML config file and two small FASTQ files of reads overlapping a single somatic mutation. For this simple test, we will re-use the tumor DNA sequencing as our RNA reads.

```sh
mkdir inputs
cd inputs
wget https://github.com/openvax/neoantigen-vaccine-pipeline/blob/master/test/idh1_config.yaml?raw=true
wget https://github.com/openvax/neoantigen-vaccine-pipeline/blob/master/datagen/idh1_r132h_normal.fastq.gz?raw=true
wget https://github.com/openvax/neoantigen-vaccine-pipeline/blob/master/datagen/idh1_r132h_tumor.fastq.gz?raw=true
cd ..
chmod -R a+w inputs
```

And we’ll make an empty output directory:

```sh
mkdir outputs
chmod -R a+w outputs
```

Now we may run the pipeline. Note that the Docker volume option (`-v`) requires absolute paths. We use `$(realpath <dirname>)` to get the absolute path to the directories created above on the host machine. You can also just replace those with absolute paths.

```
docker run \
-v $(realpath inputs):/inputs \
-v $(realpath outputs):/outputs \
-v $(realpath reference-genome):/reference-genome \
julia326/neoantigen-vaccine-pipeline:latest \
--configfile=/inputs/idh1_r132h_config.yaml
```

This should create the final results as well as many intermediate files in the output directory.

If you want to poke around in the image to execute tools manually or inspect versions:
```
docker run \
-v $(realpath inputs):/inputs \
-v $(realpath outputs):/outputs \
-v $(realpath reference-genome):/reference-genome \
--entrypoint /bin/bash -it \
julia326/neoantigen-vaccine-pipeline:latest
```

### Running the dockerized pipeline with your own data

Use the [test IDH config file](https://github.com/openvax/neoantigen-vaccine-pipeline/blob/master/test/idh1_config.yaml) as a template for your own config file you can pass to the pipeline. Assuming you've successfully run the pipeline on the test data, you should only need to customize the `input` section.

Please note:
- The input FASTQ files must live in the same directory as your config YAML file. You should only need to modify the basename of the sample file paths, leaving the `/inputs` part of the filename unchanged.
- If your data is paired-end FASTQ files, you must specify the two files as `r1` and `r2` entries instead of the singular `r` entry in the config template. You must also change the `type` to say `paired-end`.

### Intermediate files

As a result of the full pipeline run, many intermediate files are generated in the output directory. In case you want to reuse these for a different pipeline run (e.g. if you have one normal sample and several tumor samples, each of which you want to run against the normal), any intermediate file you copy to the new location will tell Snakemake to not repeat that step (or its substeps, unless they're needed for some other workflow node). For that reason, it's helpful to know the intermediate file paths. You can also run parts of the pipeline used to generate any of the intermediate files, specifying one or more as a target to the Docker run invocation. Example, if you use [the test IDH config](https://github.com/openvax/neoantigen-vaccine-pipeline/blob/master/test/idh1_config.yaml):
```
docker run \
-v <your inputs dir>:/inputs \
-v <your outputs dir>:/outputs \
-v <your reference genome dir>:/reference-genome \
julia326/neoantigen-vaccine-pipeline:latest \
--configfile=/inputs/idh1_config.yaml \
--target=/outputs/idh1-test-sample/tumor_aligned_coordinate_sorted_dups_indelreal_bqsr.bam \
--target=/outputs/idh1-test-sample/normal_merged_aligned_coordinate_sorted.bam
```
This (somewhat arbitrary) example will run alignment on normal DNA, and alignment + full GATK process on the tumor DNA.

Here are some of the intermediate file names you might use as targets, in a sample's output directory:
- `{normal,tumor,rna}_merged_aligned_coordinate_sorted.bam`: after BWA alignment, merging of lanes if necessary
- `{normal,tumor,rna}_aligned_coordinate_sorted_dups.bam`: after GATK MarkDups
- `{normal,tumor}_aligned_coordinate_sorted_dups_indelreal.bam`: after GATK IndelRealigner
- `{normal,tumor}_aligned_coordinate_sorted_dups_indelreal_bqsr.bam`: after GATK BQSR. These are inputs to variant callers.
- `rna_aligned_coordinate_sorted_dups_cigar_N_filtered.bam`: after GATK MarkDups, filtered to all tumor RNA reads with Ns in the CIGAR string (will not run IndelRealigner on these)
- `rna_aligned_coordinate_sorted_dups_cigar_0-9MIDSHPX_filtered.bam`: after GATK MarkDups, all tumor RNA reads without Ns
- `rna_cigar_0-9MIDSHPX_filtered_sorted_indelreal.bam`: tumor RNA after GATK IndelRealigner
- `rna_final_sorted.bam`. This is RNA after all processing; used as input to `vaxrank`.
- `{mutect,mutect2,strelka}.vcf`: merged (all-contig) VCF from corresponding variant caller. Use e.g. `mutect_10.vcf` to only call Mutect variants in chromosome 10.

## Running without Docker

To get started with pipeline development and rule definition, install the Python dependencies:
```
pip install -r requirements.txt
```
## Testing

You can run a small local unit test which simulates a pipeline dependency graph and does not require Docker. Once you clone this repo and install the Python requirements, run:
```
nosetests
```
