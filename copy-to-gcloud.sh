#!/bin/bash

# Pass trial and patient ID as an arg to this script, which will be used to copy to
# a particular directory on gcloud.
#
# Example usage: ./copy-to-gcloud.sh pgv001-012 pgv001/pt012/snake

set -ex

if [ $# -lt 2 ]; then
    echo "Too few arguments supplied ($#), expected <output directory> <bucket path>";
    exit 1;
fi

LOCAL_DIRNAME=$1
GCLOUD_PATH=$2

# remove trailing slashes in arguments
LOCAL_DIRNAME=${LOCAL_DIRNAME%/}
GCLOUD_PATH=${GCLOUD_PATH%/}

echo "Arguments:"
echo "LOCAL_DIRNAME=$LOCAL_DIRNAME"
echo "GCLOUD_PATH=$GCLOUD_PATH"



echo "=== Copying FastQC files ===" 
if [ -d $LOCAL_DIRNAME/fastqc-output/ ]; then 
  gsutil -m cp -r $LOCAL_DIRNAME/fastqc-output/ gs://$GCLOUD_PATH/
else
  echo "Skipping $LOCAL_DIRNAME/fastqc-output, directory not found"
fi 

echo "=== Copying Picard metrics ==="
gsutil -m cp -R $LOCAL_DIRNAME/*metrics*.txt gs://$CLOUD_PATH/picard-metrics/

echo "=== Copying logs ==="
gsutil -m cp -R $LOCAL_DIRNAME/logs/ gs://$GCLOUD_PATH/

echo "=== Copying VCF files ==="
for vcf in mutect.vcf mutect2.vcf strelka.vcf filtered_normal_germline_snps_indels.vcf filtered_covered_normal_germline_snps_indels.vcf
do
    if [ -f $LOCAL_DIRNAME/$vcf ]
    then
        gsutil -m cp $LOCAL_DIRNAME/$vcf gs://$GCLOUD_PATH/$vcf
    else   
        echo "Skipping $LOCAL_DIRNAME/$vcf, does not exist"
    fi
done

echo "=== Copying Vaxrank output ==="
gsutil -m cp $LOCAL_DIRNAME/vaccine-peptide-report* gs://$GCLOUD_PATH/
gsutil -m cp $LOCAL_DIRNAME/all-passing-variants*.csv gs://$GCLOUD_PATH/

echo "=== Copying BAM files ==="
gsutil -m cp $LOCAL_DIRNAME/normal_aligned_coordinate_sorted_dups_indelreal_bqsr.bam gs://$GCLOUD_PATH/normal.bam
gsutil -m cp $LOCAL_DIRNAME/normal_aligned_coordinate_sorted_dups_indelreal_bqsr.bai gs://$GCLOUD_PATH/normal.bam.bai
gsutil -m cp $LOCAL_DIRNAME/tumor_aligned_coordinate_sorted_dups_indelreal_bqsr.bam gs://$GCLOUD_PATH/tumor.bam
gsutil -m cp $LOCAL_DIRNAME/tumor_aligned_coordinate_sorted_dups_indelreal_bqsr.bai gs://$GCLOUD_PATH/tumor.bam.bai
gsutil -m cp $LOCAL_DIRNAME/rna_final_sorted.bam gs://$GCLOUD_PATH/rna.bam
gsutil -m cp $LOCAL_DIRNAME/rna_final_sorted.bam.bai gs://$GCLOUD_PATH/rna.bam.bai
echo "Done."
