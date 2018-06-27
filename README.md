# neoantigen-vaccine-pipeline

This repository is the public version of the bioinformatics pipeline for selecting patient-specific cancer neoantigen vaccines developed by the [openvax](https://www.openvax.org/) group at [Mount Sinai](http://icahn.mssm.edu/). This pipeline is currently the basis for two phase I clinical trials using synthetic long peptides, PGV001 ([NCT02721043](https://clinicaltrials.gov/ct2/show/NCT02721043)) and MTA ([NCT03223103](https://clinicaltrials.gov/ct2/show/NCT03223103)).

The pipeline used for these trials differs slightly from the version given here due to licensing restrictions on the [NetMHC](http://www.cbs.dtu.dk/services/NetMHC/) suite of tools, which prevent their inclusion in the provided docker image. To circumvent this issue, the open source pipeline performs MHC binding prediction using the IEDB web interface to these tools. This may be slower but should give the same results. If you have a license to the NetMHC tools (free for non-commerical use) and wish to run these tools locally in the pipeline, please contact us or file an issue.

The pipeline is implemented using the [Snakemake](https://snakemake.readthedocs.io/en/stable/) workflow management system. We recommend running it using our provided [docker image](https://hub.docker.com/r/julia326/neoantigen-vaccine-pipeline/), which includes all needed dependencies.

# Overview

This pipeline assumes you have the following datasets.

* Tumor and normal whole exome sequencing. In our trials, we target 300X tumor coverage, 150X normal.
* Tumor RNA sequencing. We target 100M reads for fresh samples (using poly-A capture) and 300M reads for FFPE samples (using Ribo-Zero).
* List of MHC class I alleles for the individual
* Reference genome and associated files (COSMIC and dbSNP). As a convenience, we provide these files for grch37. 

The steps performed by the workflow are as follows.

* Tumor and normal whole exome sequencing fastq files are aligned to [grch37](https://www.ncbi.nlm.nih.gov/assembly/GCF_000001405.13/) using [bwa mem](http://bio-bwa.sourceforge.net/). RNA-seq of the tumor sample is aligned by [STAR](https://academic.oup.com/bioinformatics/article/29/1/15/272537) to grch37.
* Aligned tumor and normal exome reads pass through several steps using GATK 3.7: MarkDuplicates, IndelRealignment, BQSR.
* Aligned RNA-seq reads are grouped into two sets: those spanning introns and those aligning entirely within an exon (determined based on the CIGAR string). The latter group is passed through IndelAligner, and the two groups of reads are merged.
* Variant calling is performed using Mutect 1.1.7 and Strelka version 1. The pipeline supports running Mutect 2 but by default it is disabled.
* [Vaxrank](https://github.com/openvax/vaxrank) is run, using the combined VCFs from all variant callers and the aligned RNA reads.

## Running using docker

You will need a machine with at least 16 cores and 1TB free disk space, and docker [installed](https://docs.docker.com/install/).

The pipeline is run by invoking a docker entrypoint in the image while providing three directories as mounted docker [volumes](https://docs.docker.com/storage/volumes/): `/inputs` (fastq files and a configuration JSON), `/outputs` (directory to write results to), and `/reference-genome` (data shared across patients, such as the genome reference).

Note that all three directories and their contents must be world writable. This is necessary because the Docker pipeline runs as an unprivileged user and not as you. Data is modified in the `outputs` directory as well as in the `reference-genome` directory, since indexing the reference genome for use by aligners and other tools requires writing results to this directory.

First we will download the reference data for grch37 (b37).

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

Now we will download a test sequencing dataset, consisting of a JSON config file and two small fastq files of reads overlapping a single somatic mutation. For this simple test, we will re-use the tumor DNA sequencing as our RNA reads.

```sh
mkdir inputs
cd inputs
wget https://github.com/openvax/neoantigen-vaccine-pipeline/blob/master/test/idh1_config.json?raw=true
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

Now we may run the pipeline. Note that the docker volume option (`-v`) requires absolute paths. We use `$(realpath <dirname>)` to get the absolute path to the directories created above on the host machine. You can also just replace those with absolute paths.

```
docker run \
-v $(realpath inputs):/inputs \
-v $(realpath outputs):/outputs \
-v $(realpath reference-genome):/reference-genome \
julia326/neoantigen-vaccine-pipeline:latest \
--configfile=/inputs/idh1_r132h_config.json
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


## Running without docker

To get started with pipeline development and rule definition, install the Python dependencies:
```
pip install -r requirements.txt
```
## Testing

You can run a small local unit test which simulates a pipeline dependency graph and does not require Docker. Once you clone this repo and install the Python requirements, run:
```
nosetests
```
