# neoantigen-vaccine-pipeline

Snakemake implementation of the PGV vaccine pipeline, powering the PGV001 and GBM vaccine trials.

## Setup

To get started with pipeline development and rule definition, you only need the Python dependencies:
```
pip install -r requirements.txt
```

### Dockerized pipeline

Note that this relies on a private Docker image which contains the necessary tool dependencies. This is not ready for external users.

Prerequisites for us:
- Installed Docker (for how to do this on Debian, see https://docs.docker.com/install/linux/docker-ce/debian/#set-up-the-repository)
- A JSON file containing the private key describing the bhardwaj-lab service account.
- A machine with at least 16 cores and 1TB free disk space.

#### 1. Set up service account access to bhardwaj-lab buckets:

```
gcloud auth activate-service-account --key-file <bhardwaj-lab JSON key file path>
```

#### 2. Download this data for getting started with the pipeline:

- `gs://pgv-test-data`: this contains an example Snakemake config and small test tumor/normal FASTQ files
- `gs://reference-genomes`: reference genomes data

Download this and put in a world-writeable directory (the pipeline will preprocess the reference as needed, and write the results to that same directory)

#### 3. Create a pipeline outputs directory; this will contain sample-specific pipeline output.

#### 4. Note that your outputs and reference genomes directory must be recursively world writable:
```
chmod -R a+w <reference genomes dir>
chmod -R a+w <outputs dir>
```
This is necessary because the Docker pipeline runs as an internal Docker user and not as you, so it needs write privileges. Data is modified in the outputs directory as well as in the reference genomes: preparing the reference genome for use by BWA/GATK/etc. will save the results to the genome directory.

#### 5. Log into Docker Hub to pull the private Docker image.
```
docker login
```
You may see an error like "Cannot connect to the Docker daemon at unix:///var/run/docker.sock"; this means your user is not a member of the docker group. Add the user to the group:
```
sudo usermod -a -G docker <your username>
```

#### 6. Pull the Docker image.
```
docker pull julia326/neoantigen-vaccine-pipeline:wip
```

This is an example pipeline command which uses the test Snakemake config you downloaded, and runs the full pipeline including Vaxrank:
```
docker run \
-v <your inputs dir>:/inputs \
-v <your outputs dir>:/outputs \
-v <your reference genomes dir>:/reference-genome \
julia326/neoantigen-vaccine-pipeline:wip \
--configfile=/inputs/idh1_config.json
```

If you want to poke around in the image to execute tools manually, look at tool versions etc.:
```
docker run \
-v <your inputs dir>:/inputs \
-v <your outputs dir>:/outputs \
-v <your reference genomes dir>:/reference-genome \
--entrypoint /bin/bash -it julia326/neoantigen-vaccine-pipeline:wip
```

#### Intermediate files

As a result of the full pipeline run, many intermediate files are generated in the output directory. In case you want to reuse these for a different pipeline run (e.g. if you have one normal sample and several tumor samples, each of which you want to run against the normal), any intermediate file you copy to the new location will tell Snakemake to not repeat that step (or its substeps, unless they're needed for some other workflow node). For that reason, it's helpful to know the intermediate file paths. You can also run parts of the pipeline used to generate any of the intermediate files, specifying one or more as a target to the Docker run invocation. Example, if you use [the test IDH config](https://github.com/openvax/neoantigen-vaccine-pipeline/blob/master/test/idh1_config.json):
```
docker run \
-v <your inputs dir>:/inputs \
-v <your outputs dir>:/outputs \
-v <your reference genomes dir>:/reference-genome \
julia326/neoantigen-vaccine-pipeline:wip \
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



## Requirements for running the pipeline without Docker

These instructions assumes you're running on the PGV compute node,
which already has a GATK jar. On a different machine you will have to first
installing GATK.

### Set up a Conda environment:

```sh
# snakemake needs python3
conda create -n pgv
source activate pgv
```

### Set up Bioconda

Install channels in this order

```sh
conda config --add channels r
conda config --add channels defaults
conda config --add channels conda-forge
conda config --add channels bioconda
```

### Install bioinformatics tools

```sh
# install a bunch of bio tools; gatk needs to be this version, latest doesn't work
# graphviz needed for DAG visualization
# ucsc-liftover for converting coverage bed files between various alignments
# java version specific to MuTect
conda install bwa samtools sambamba snakemake picard gatk==3.7 graphviz bedtools ucsc-liftover java-jdk==8.0.92 vcftools star
```

### Link GATK:
```sh
# need to link GATK
# unfortunately, then also need to edit the gatk binary (see "which gatk") to have the right
# value for jar_file.
gatk-register /data/biokepi-work-dir/workdir/toolkit/gatk.NOVERSION/GenomeAnalysisTK_37.jar
```

### Install MuTect

First download Mutect from `https://software.broadinstitute.org/gatk/download/mutect` to the path:
`/biokepi/workdir/toolkit/mutect-1.1.7.jar`

### Install Java 1.7


MuTect needs Java 1.7, while GATK and other things need Java 1.8.
Dealing with this by setting up a separate Conda environment, specifically for Java 7

```sh
conda create -n java17
source activate java17
conda install java-jdk==7.0.91
```
This results in java 7 being installed to `/home/julia/miniconda3/envs/java17/bin/java`,
which should be run only for MuTect.


### Install Perl vcftools

```sh
cd ~/bin
wget -O vcftools_0.1.13.tar.gz https://kent.dl.sourceforge.net/project/vcftools/vcftools_0.1.13.tar.gz
tar xvfz vcftools_0.1.13.tar.gz
cd vcftools_0.1.13/
```

Possibly unnecessary step?

```sh
export PERL5LIB=~/bin/vcftools-vcftools-ea875e2/src/perl
```


This will build both the C++ and Perl, we're only using Perl, but that's fine:

```sh
make
# copy stuff over to $HOME/bin, already on the path
# run `which vcftools` to make sure it's the conda-installed version, rather than this one
# (depends on PATH setup)
cp bin/* $HOME/bin
cp lib/perl5/site_perl/* $HOME/bin
export PERL5LIB=$HOME/bin/
```
To make sure things work run `vcf-concat -h`

### Install Strelka

Note that Strelka needs Python 2.7, so that's probably what the system Python needs to be?

```sh
wget -O strelka_workflow-1.0.14.tar.gz ftp://strelka:%27%27@ftp.illumina.com/v1-branch/v1.0.14/strelka_workflow-1.0.14.tar.gz
tar xvfz strelka_workflow-1.0.14.tar.gz
cd strelka_workflow-1.0.14
./configure prefix=$HOME/bin
make
chmod -R a+rx ./*
make install
export STRELKA_BIN=$HOME/bin/bin
```

### Add vaxrank to the Conda env
```sh
pip install vaxrank
```

For vaxrank to generate PDF reports, need to do this on a Linux box:
```sh
sudo apt-get install xvfb
```

Get wkhtmltopdf for making vaxrank reports
```sh
wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
tar xvfJ wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
cd wkhtmltox/bin
sudo chown root:root wkhtmltopdf
sudo cp wkhtmltopdf /usr/local/bin/wkhtmltopdf
curl https://pastebin.com/raw/AmfYN3er > ~/.fonts.conf   # for the kerning to not be awful
```

### Install MHC binding predictor:


For our purposes, to set up netMHCcons/pan, follow instructions at: https://github.com/openvax/netmhc-bundle

### Reference genome data

Right now, the pipeline relies on having generated a bunch of reference genome content.
Current contents of a reference genome directory, I believe all of these are needed for correct DNA processing (these are specific to b37decoy, obviously different for other references):

* b37decoy.dict
* b37decoy.fasta
* b37decoy.fasta.amb
* b37decoy.fasta.ann
* b37decoy.fasta.bwt
* b37decoy.fasta.fai
* b37decoy.fasta.pac
* b37decoy.fasta.sa
* cosmic.vcf
* cosmic.vcf.idx
* dbsnp.vcf
* dbsnp.vcf.idx
* transcripts.gtf

### Configure Strelka

Create a Strelka config file with the following contents, and use it in the Strelka invocation:

```
[user]
isSkipDepthFilters = 1
maxInputDepth = 10000
depthFilterMultiple = 3.0
snvMaxFilteredBasecallFrac = 0.4
snvMaxSpanningDeletionFrac = 0.75
indelMaxRefRepeat = 8
indelMaxWindowFilteredBasecallFrac = 0.3
indelMaxIntHpolLength = 14
ssnvPrior = 0.000001
sindelPrior = 0.000001
ssnvNoise = 0.0000005
sindelNoise = 0.0000001
ssnvNoiseStrandBiasFrac = 0.5
minTier1Mapq = 40
minTier2Mapq = 5
ssnvQuality_LowerBound = 15
sindelQuality_LowerBound = 30
isWriteRealignedBam = 0
binSize = 25000000
extraStrelkaArguments = --eland-compatibility
```

### Environment variables

A pipeline user outside Docker needs to go through the above setup and also have the following environment variables set:

* `STRELKA_BIN`: directory of Strelka installation, must contain configureStrelkaWorkflow.pl
* `STRELKA_CONFIG`: path to Strelka config file
* `MUTECT`: path to MuTect (v1) jar file
* `JAVA7_BIN`: path to directory containing the Java 7 executable

You must also set `PYENSEMBL_CACHE_DIR`, and have it be writeable (see "pyensembl" rule in special_sauce.rules)
Same for `VAXRANK_REF_PEPTIDES_DIR`.



