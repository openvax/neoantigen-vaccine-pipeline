#!/bin/bash

# Pass trial and patient ID as an arg to this script, which will be used to copy to
# a particular directory on gcloud.
#
# Example usage: ./copy-to-gcloud.sh pgv001-012 pgv001/pt012/snake

set -e

if [ $# -lt 2 ]; then
    echo "Too few arguments supplied ($#)";
    exit 1;
fi

DIRNAME=$1
FOLDER=$2
gsutil -m cp $DIRNAME/normal_aligned_coordinate_sorted_dups_indelreal_bqsr.bam gs://$FOLDER/normal.bam
gsutil -m cp $DIRNAME/normal_aligned_coordinate_sorted_dups_indelreal_bqsr.bai gs://$FOLDER/normal.bam.bai
gsutil -m cp $DIRNAME/tumor_aligned_coordinate_sorted_dups_indelreal_bqsr.bam gs://$FOLDER/tumor.bam
gsutil -m cp $DIRNAME/tumor_aligned_coordinate_sorted_dups_indelreal_bqsr.bai gs://$FOLDER/tumor.bam.bai
gsutil -m cp $DIRNAME/rna_final_sorted.bam gs://$FOLDER/rna.bam
gsutil -m cp $DIRNAME/rna_final_sorted.bam.bai gs://$FOLDER/rna.bam.bai

gsutil -m cp $DIRNAME/mutect.vcf gs://$FOLDER/mutect.vcf
gsutil -m cp $DIRNAME/strelka.vcf gs://$FOLDER/strelka.vcf
gsutil -m cp $DIRNAME/vaccine-peptide-report* gs://$FOLDER/
gsutil -m cp $DIRNAME/all-passing-variants*.csv gs://$FOLDER/

gsutil -m cp -r $DIRNAME/fastqc-output/ gs://$FOLDER/

# may or may not exist
gsutil -m cp $DIRNAME/mutect2.vcf gs://$FOLDER/mutect2.vcf

echo "Done"
