# Build with: docker build -f docker/Dockerfile .

FROM --platform=linux/amd64 ubuntu:22.04

MAINTAINER Julia Kodysh <julia326@gmail.com>

RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections && \
    apt-get clean && \
    apt-get update && \
    apt-get install --no-install-recommends --no-upgrade -y \
        ca-certificates \
        curl \
        gawk \
        git \
        graphviz \
        g++ \
        libfreetype6-dev \
        libx11-dev \
        libbz2-dev \
        libcurl4-openssl-dev \
        libgnutls28-dev \
        libssl-dev \
        make \
        perl \
        pkg-config \
        python-tk \
        python2.7-dev \
        rsync \
        sudo \
        tar \
        tcsh \
        unzip \
        wget \
        xvfb \
        zlib1g-dev && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --home-dir /home/user --shell /bin/bash -G sudo user && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER user
ENV HOME=/home/user
ENV SHELL=/bin/bash
ENV USER=user
WORKDIR /home/user

# Install the Perl vcftools
# Original address for vcftools: https://kent.dl.sourceforge.net/project/vcftools/vcftools_0.1.13.tar.gz
RUN cd /tmp && wget https://github.com/openvax/neoantigen-vaccine-pipeline/releases/download/0.3.0/vcftools_0.1.13.tar.gz && \
    tar xvfz vcftools_0.1.13.tar.gz && cd vcftools_0.1.13/ && make && \
    sudo cp -r /tmp/vcftools_0.1.13/bin/* /usr/local/bin && \
    sudo cp -r /tmp/vcftools_0.1.13/lib/perl5/site_perl/* /usr/local/lib && \
    rm -rf /tmp/*

ENV PERL5LIB /usr/local/lib

# Install Miniconda
RUN wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh && \
    bash miniconda.sh -b -p $HOME/miniconda
ENV PATH $HOME/miniconda/bin:$PATH

ENV PGV_BIN /home/user/miniconda/envs/pgv/bin
ENV JAVA7_BIN /home/user/miniconda/envs/java7/bin

# Switch to a faster solver for conda
RUN conda update -n base conda && conda install -n base conda-libmamba-solver && \
    conda config --set solver libmamba

# install a bunch of bfx tools; gatk needs to be this version, latest doesn't work
# graphviz needed for DAG visualization
# ucsc-liftover for converting coverage bed files between various alignments
# java version specific to MuTect
RUN conda config --add channels r && \
    conda config --add channels defaults && \
    conda config --add channels conda-forge && \
    conda config --add channels bioconda && \
    conda create -n pgv \
    setuptools \
    python=3.6 \
    bedtools \
    bwa==0.7.17 \
    cython \
    fastqc \
    gatk==3.7 \
    java-jdk==8.0.112 \
    picard==2.18.5 \
    pip \
    sambamba \
    samtools \
    star==2.6.0c \
    vcftools==0.1.15 \
    && conda clean --all -y

# We also setup a newer environment with mhcflurry.
RUN conda config --add channels r && \
    conda config --add channels defaults && \
    conda config --add channels conda-forge && \
    conda config --add channels bioconda && \
    conda create -n mhcflurry \
    python=3.7 \
    setuptools \
    cython \
    pip \
    && conda clean --all -y

# And an older one with Python 2.7 so that Strelka can run.
RUN conda config --add channels r && \
    conda config --add channels defaults && \
    conda config --add channels conda-forge && \
    conda config --add channels bioconda && \
    conda create -n strelka \
    python=2.7 \
    strelka==2.9.10 \
    && conda clean --all -y

# MuTect needs Java 1.7, while GATK and other things need Java 1.8.
# Dealing with this by setting up a separate Conda environment, specifically for Java 7
RUN conda create -n java7 \
    java-jdk==7.0.91 \
    && conda clean --all -y

# Set up MuTect 1.1.7
RUN wget -O $HOME/mutect-1.1.7.jar http://storage.googleapis.com/common-files/tools/mutect-1.1.7.jar
ENV MUTECT $HOME/mutect-1.1.7.jar

# Set up GATK 3.7; need to link with gatk-register
RUN wget -O $HOME/GenomeAnalysisTK.jar http://storage.googleapis.com/common-files/tools/GenomeAnalysisTK.jar
RUN $PGV_BIN/gatk-register $HOME/GenomeAnalysisTK.jar

# Copy and install Vaxrank and other python dependencies; they won't change very often,
# so we want to do this before any further COPY commands in this Dockerfile.
# See https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#add-or-copy
COPY requirements.txt $HOME
ENV MHCFLURRY_BIN /home/user/miniconda/envs/mhcflurry/bin
RUN $MHCFLURRY_BIN/pip install --ignore-installed -r $HOME/requirements.txt
RUN $MHCFLURRY_BIN/mhcflurry-downloads fetch

# Test MHCflurry
RUN $MHCFLURRY_BIN/mhcflurry-predict --alleles HLA-A0201 --peptides SIINFEKL

# most of the tools we're using are in the pgv environment; adding to PATH for convenience
ENV PATH $MHCFLURRY_BIN:$PGV_BIN:$PATH

# Vaxrank-required env variables and setup
ENV KERAS_BACKEND tensorflow
ENV PYENSEMBL_CACHE_DIR /reference-genome/pyensembl-cache
ENV VAXRANK_REF_PEPTIDES_DIR /reference-genome/reference-peptides
# this is needed for Vaxrank reports to be reasonably formatted, otherwise kerning is off
RUN curl https://pastebin.com/raw/AmfYN3er > $HOME/.fonts.conf

# Copy the current directory contents into the container
COPY . $HOME

# Strelka setup
ENV STRELKA_CONFIG $HOME/pipeline/strelka_config.txt
ENV STRELKA_BIN $HOME/miniconda/envs/strelka/bin

# Python scripts setup, for things that are too small/simple to be their own modules
ENV SCRIPTS $HOME/pipeline/scripts

# snakemake logs get written here (hidden dir)
RUN mkdir -p $HOME/.snakemake && sudo chown -R $USER $HOME/.snakemake

# Hack to patch broken vaxrank after WUSTL server change.
RUN sed -i '/^\s*except requests\.exceptions\.ConnectionError as e:/s/except requests\.exceptions\.ConnectionError as e:/except:/g' /home/user/miniconda/envs/mhcflurry/lib/python3.7/site-packages/vaxrank/report.py


ENTRYPOINT ["python", "run_snakemake.py"]
