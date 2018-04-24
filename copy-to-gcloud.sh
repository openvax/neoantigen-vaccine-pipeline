#!/bin/bash

# Pass trial and patient ID as an arg to this script, which will be used to copy to
# a particular directory on gcloud.
#
# Example usage: ./copy-to-gcloud.sh pgv001/pt012

FOLDER=$1
gsutil -m cp normal_aligned_coordinate_sorted_dups_indelreal_bqsr.bam gs://$FOLDER/snake/normal.bam
gsutil -m cp normal_aligned_coordinate_sorted_dups_indelreal_bqsr.bai gs://$FOLDER/snake/normal.bam.bai
gsutil -m cp tumor_aligned_coordinate_sorted_dups_indelreal_bqsr.bam gs://$FOLDER/snake/tumor.bam
gsutil -m cp tumor_aligned_coordinate_sorted_dups_indelreal_bqsr.bai gs://$FOLDER/snake/tumor.bam.bai
gsutil -m cp rna_final_sorted.bam gs://$FOLDER/snake/rna.bam
gsutil -m cp rna_final_sorted.bam.bai gs://$FOLDER/snake/rna.bam.bai

gsutil -m cp mutect.vcf gs://$FOLDER/snake/mutect.vcf
gsutil -m cp strelka.vcf gs://$FOLDER/snake/strelka.vcf
gsutil -m cp mutect2.vcf gs://$FOLDER/snake/mutect2.vcf
gsutil -m cp vaccine-peptide-report.* gs://$FOLDER/snake/

echo "Done"
