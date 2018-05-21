# User must:
# - copy GenomeAnalysisTK.jar to this directory: need to download GATK 3.7
# - copy mutect-1.1.7.jar to this directory: can download from https://software.broadinstitute.org/gatk/download/archive

# Build with: docker build -t pipeline/base:<tag> docker/base/

FROM ubuntu:16.04

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
        make \
        perl \
        pkg-config \
        python-tk \
        python2.7-dev \
        python3.5-dev \
        rsync \
        sudo \
        tcsh \
        wget \
        xvfb \
        zlib1g-dev && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

# install wkhtmltopdf from source, this version comes with patched QT necessary for PDF gen
RUN cd /tmp && \
    wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz && \
    tar xvfJ wkhtmltox-0.12.4_linux-generic-amd64.tar.xz && \
    cd /tmp/wkhtmltox/bin && sudo chown root:root wkhtmltopdf && \
    sudo cp /tmp/wkhtmltox/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf && \
    rm -rf /tmp/*

RUN useradd --create-home --home-dir /home/user --shell /bin/bash -G sudo user && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER user
ENV HOME=/home/user
ENV SHELL=/bin/bash
ENV USER=user
WORKDIR /home/user

# Install the Perl vcftools
RUN cd /tmp && wget https://kent.dl.sourceforge.net/project/vcftools/vcftools_0.1.13.tar.gz && \
    tar xvfz vcftools_0.1.13.tar.gz && cd vcftools_0.1.13/ && make && \
    sudo cp -r /tmp/vcftools_0.1.13/bin/* /usr/local/bin && \
    sudo cp -r /tmp/vcftools_0.1.13/lib/perl5/site_perl/* /usr/local/lib && \
    rm -rf /tmp/*

ENV PERL5LIB /usr/local/lib

# Install Strelka
RUN mkdir $HOME/strelka && \
    cd /tmp && wget ftp://strelka:%27%27@ftp.illumina.com/v1-branch/v1.0.14/strelka_workflow-1.0.14.tar.gz && \
    tar xvfz strelka_workflow-1.0.14.tar.gz && \
    cd strelka_workflow-1.0.14 && \
    ./configure prefix=$HOME/strelka && \
    make && \
    chmod -R a+rx ./* && \
    make install && \
    rm -rf /tmp/*

ENV STRELKA_BIN $HOME/strelka/bin

# Install Miniconda
RUN wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh && \
    bash miniconda.sh -b -p $HOME/miniconda
ENV PATH $HOME/miniconda/bin:$PATH

ENV PGV_BIN /home/user/miniconda/envs/pgv/bin
ENV JAVA7_BIN /home/user/miniconda/envs/java7/bin

# install a bunch of bfx tools; gatk needs to be this version, latest doesn't work
# graphviz needed for DAG visualization
# ucsc-liftover for converting coverage bed files between various alignments
# java version specific to MuTect
RUN conda config --add channels r && \
    conda config --add channels defaults && \
    conda config --add channels conda-forge && \
    conda config --add channels bioconda && \
    conda create -n pgv \
    bwa \
    cython \
    gatk==3.7 \
    java-jdk==8.0.92 \
    picard \
    pip \
    sambamba \
    snakemake \
    star \
    vcftools && \
    conda clean --all -y

# most of the tools we're using are in the pgv environment; adding to PATH for convenience
ENV PATH $PGV_BIN:$PATH

# MuTect needs Java 1.7, while GATK and other things need Java 1.8.
# Dealing with this by setting up a separate Conda environment, specifically for Java 7
RUN conda create -n java7 java-jdk==7.0.91 && conda clean --all -y

# Special sauce stuff
RUN pip install --ignore-installed vaxrank==0.7.12

# needed for vaxrank reports to be reasonably formatted, otherwise kerning is off
RUN curl https://pastebin.com/raw/AmfYN3er > $HOME/.fonts.conf

# Copy the current directory contents into the container
ADD . $HOME

# set up Strelka config
COPY strelka_config.txt $HOME/
ENV STRELKA_CONFIG $HOME/strelka_config.txt

ENV PYENSEMBL_CACHE_DIR /tool-cache/pyensembl
ENV VAXRANK_REF_PEPTIDES_DIR /tool-cache/reference-peptides

######## THESE ARE LAB-SPECIFIC BITS ########

# need to link GATK
COPY GenomeAnalysisTK.jar $HOME/GenomeAnalysisTK.jar
RUN $PGV_BIN/gatk-register $HOME/GenomeAnalysisTK.jar

# MuTect setup
COPY mutect-1.1.7.jar $HOME/
ENV MUTECT $HOME/mutect-1.1.7.jar

# NetMHC setup
ARG MHCBUNDLE_PASS
RUN git clone https://mhcbundle:$MHCBUNDLE_PASS@github.com/openvax/netmhc-bundle.git && mkdir tmp
ENV NETMHC_BUNDLE_TMPDIR $HOME/tmp
ENV NETMHC_BUNDLE_HOME $HOME/netmhc-bundle
ENV PATH $PATH:$NETMHC_BUNDLE_HOME/bin
ENV KERAS_BACKEND tensorflow

ENTRYPOINT ["./run.sh"]
