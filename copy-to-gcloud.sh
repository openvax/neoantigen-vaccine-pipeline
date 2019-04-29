#!/bin/bash

# Pass trial and patient ID as an arg to this script, which will be used to copy to
# a particular directory on gcloud.
#
# Example usage: ./copy-to-gcloud.sh pgv001-012 pgv001/pt012/snake

set -e

if [[ $# -lt 2 ]]; then
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


function copy_path_if_exists {
    # Two arguments
    # 1) local path to file
    # 2) remote name of file relative to GCLOUD_PATH
    SOURCE="$1"
    DEST="gs://$GCLOUD_PATH/$2"
    if [[ -f "$SOURCE" ]]; then
        gsutil -m cp "$SOURCE" "$DEST"
     else
        echo "Skipping $SOURCE, file not found"
    fi
}

function copy_local_file_if_exists {
    # Prepends $LOCAL_DIRNAME to first argument and then
    # calls copy_if_exists
    #
    # Two arguments:
    # 1) local name of file relative to LOCAL_DIRNAME
    # 2) remote name of file relative to GCLOUD_PATH
    SOURCE="$LOCAL_DIRNAME/$1"
    DEST="$2"
    copy_path_if_exists "$SOURCE" "$DEST"
}

function copy_directory_if_exists {
    # One argument:
    #   1) Local sub-directory relative to LOCAL_DIRNAME
    # Will be copied into GCLOUD_PATH
    SOURCE=$LOCAL_DIRNAME/$1
    # remove trailing slashes to avoid double slashes
    SOURCE=${SOURCE%/}
    DEST="gs://$GCLOUD_PATH/"
    if [[ -d FULL_DIRPATH ]]; then
        gsutil -m cp -r "$SOURCE/" "$DEST"
     else
        echo "Skipping $SOURCE, directory not found"
    fi
}

echo "=== Copying FastQC files ==="
copy_directory_if_exists "fastqc-output"

echo "=== Copying Picard metrics ==="
for f in "$LOCAL_DIRNAME"/*metrics*.txt; do
    copy_path_if_exists "$f" picard-metrics/`basename "$f"`
done

echo "=== Copying logs ==="
copy_directory_if_exists "logs"

echo "=== Copying VCF files ==="
for vcf in mutect.vcf mutect2.vcf strelka.vcf filtered_normal_germline_snps_indels.vcf filtered_covered_normal_germline_snps_indels.vcf
do
    copy_local_file_if_exists "$vcf" "$vcf"
done

echo "=== Copying Vaxrank output ==="
for f in "$LOCAL_DIRNAME"/vaccine-peptide-report*; do
    copy_path_if_exists "$f" `basename "$f"`
done
for f in "$LOCAL_DIRNAME"/all-passing-variants*.csv; do
    copy_local_file_if_exists "$f" `basename "$f"`
done

echo "=== Copying BAM files ==="
copy_local_file_if_exists normal_aligned_coordinate_sorted_dups_indelreal_bqsr.bam normal.bam
copy_local_file_if_exists normal_aligned_coordinate_sorted_dups_indelreal_bqsr.bai normal.bam.bai
copy_local_file_if_exists tumor_aligned_coordinate_sorted_dups_indelreal_bqsr.bam tumor.bam
copy_local_file_if_exists tumor_aligned_coordinate_sorted_dups_indelreal_bqsr.bai tumor.bam.bai
copy_local_file_if_exists rna_final_sorted.bam rna.bam
copy_local_file_if_exists rna_final_sorted.bam.bai rna.bam.bai

echo "Done."
