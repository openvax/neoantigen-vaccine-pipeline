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

# WeasyPrint, used to render the vaccine peptide PDF report.
#
# We deliberately do NOT use vaxrank's own PDF output: vaxrank 1.4.0 renders PDFs
# via pdfkit -> wkhtmltopdf, and wkhtmltopdf was archived upstream in 2023. Instead
# vaxrank emits the HTML report and the vaccine_peptide_report_pdf rule converts it
# (see pipeline/special_sauce.rules).
#
# WeasyPrint is installed against the system Python 3.10 rather than vaxrank's
# Python 3.7 conda env, and is invoked as a CLI, so vaxrank's Python version does
# not constrain it. Needs Pango >= 1.44; jammy ships 1.50.
#
# Version pin, do not bump without also bumping the base image: WeasyPrint 63.0+
# subsets fonts with HarfBuzz and needs libharfbuzz-subset.so.0 (HarfBuzz >= 4.1).
# Ubuntu 22.04 ships HarfBuzz 2.7.4 and provides that library in no package at all
# -- there is no libharfbuzz-subset0 on jammy. 62.3 is the last release that
# subsets via fontTools instead, so it is the newest version that builds here.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3-pip \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libharfbuzz0b \
        libfontconfig1 && \
    pip3 install --no-cache-dir weasyprint==62.3 && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/* && \
    weasyprint --version

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

# Install Miniforge (not Miniconda).
#
# Miniforge defaults to conda-forge and never configures Anaconda's repo.anaconda.com
# channels. This matters for two reasons:
#  1. Anaconda now requires explicit Terms of Service acceptance for pkgs/main and
#     pkgs/r, which fails any non-interactive build that touches those channels.
#  2. Those terms require a paid license for organizations over 200 employees, so
#     accepting them is a licensing decision, not a build fix.
# Every package we install lives on conda-forge or bioconda, so we avoid both.
#
# Installed to $HOME/miniconda (not $HOME/miniforge) so the PGV_BIN / MHCFLURRY_BIN
# paths below and the sed patch further down keep working unchanged.
RUN wget -q https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O miniforge.sh && \
    bash miniforge.sh -b -p $HOME/miniconda && \
    rm miniforge.sh
ENV PATH $HOME/miniconda/bin:$PATH

ENV PGV_BIN /home/user/miniconda/envs/pgv/bin
ENV JAVA7_BIN /home/user/miniconda/envs/java7/bin

# No conda-libmamba-solver step is needed: Miniforge ships conda >= 23.10, which
# already uses the libmamba solver by default.

# install a bunch of bfx tools; gatk needs to be this version, latest doesn't work
# graphviz needed for DAG visualization
# ucsc-liftover for converting coverage bed files between various alignments
# java version specific to MuTect
# conda-forge is already Miniforge's default channel; bioconda goes on top of it.
RUN conda config --add channels bioconda && \
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
RUN conda create -n mhcflurry \
    python=3.7 \
    setuptools \
    cython \
    pip \
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
RUN wget https://github.com/Illumina/strelka/releases/download/v2.9.10/strelka-2.9.10.centos6_x86_64.tar.bz2 \
    && tar -xvf strelka-2.9.10.centos6_x86_64.tar.bz2 \
    && mv strelka-2.9.10.centos6_x86_64 $HOME/strelka \
    && rm strelka-2.9.10.centos6_x86_64.tar.bz2

ENV STRELKA_BIN $HOME/strelka/bin

# Python scripts setup, for things that are too small/simple to be their own modules
ENV SCRIPTS $HOME/pipeline/scripts

# snakemake logs get written here (hidden dir)
RUN mkdir -p $HOME/.snakemake && sudo chown -R $USER $HOME/.snakemake

# Hack to patch broken vaxrank after WUSTL server change.
# This can be removed once vaxrank is fixed (and we update this image to latest vaxrank).
# Replace specific exception handling with a generic "except Exception as e:" in report.py
RUN sed -i '/^\s*except requests\.exceptions\.ConnectionError as e:/s/except requests\.exceptions\.ConnectionError as e:/except Exception as e:/g' /home/user/miniconda/envs/mhcflurry/lib/python3.7/site-packages/vaxrank/report.py

ENTRYPOINT ["python", "run_snakemake.py"]
