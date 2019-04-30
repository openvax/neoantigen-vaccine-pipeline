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


function copy_to_gcloud_if_exists {
    # Copies file (or directory) to gcloud if it exists.
    #
    # Two arguments
    # 1) local name of file or directory, relative to $LOCAL_DIRNAME
    # 2) remote name of file or directory, relative to gs://$GCLOUD_PATH
    #
    # If second argument is omitted then remote file has same name as local
    # file.
    #
    # remove trailing slashes to avoid double slashes
    SOURCE_NAME=${1%/}
    DEST_NAME=${2%/}

    # if destination name isn't specified, use the same as the source name
    if [[ -z $DEST_NAME ]]; then
        DEST_NAME="$SOURCE_NAME"
    fi

    # prepend paths to filenames
    SOURCE_PATH="$LOCAL_DIRNAME/$SOURCE_NAME"
    DEST_PATH="gs://$GCLOUD_PATH/$DEST_NAME"

    if [[ -f "$SOURCE_PATH" ]]; then
        gsutil -m cp "$SOURCE_PATH" "$DEST_PATH"
     elif [[ -d "$SOURCE_PATH" ]]; then
        gsutil -m cp -r "$SOURCE_PATH/" "$DEST_PATH/"
     else
        echo "Skipping $1, file or directory not found"
    fi
}

function copy_pattern {
    # Loops over files matching a pattern and copies them to gcloud
    #
    # Two arguments
    #   1) Pattern (e.g. "dir/*.txt") relative to $LOCAL_DIRNAME
    #   2) Subdirectory on gcloud relative to $GCLOUD_PATH

    PATTERN="$1"
    # remove trailing slash so we can safely join
    # dir with remote file name
    DEST_SUBDIR=${2%/}
    for f in "$LOCAL_DIRNAME/"$PATTERN; do
        BASENAME=`basename "$f"`
        if [[ -z $DEST_SUBDIR ]]; then
            REMOTE_NAME="$BASENAME"
        else
            REMOTE_NAME="$DEST_SUBDIR/$BASENAME"
        fi
        copy_to_gcloud_if_exists "$BASENAME" "$REMOTE_NAME"
    done
}

echo "=== Copying FastQC files ==="
copy_to_gcloud_if_exists "fastqc-output/"

echo "=== Copying Picard metrics ==="
copy_pattern *metrics*.txt "picard-metrics/"

echo "=== Copying logs ==="
copy_to_gcloud_if_exists logs/

echo "=== Copying VCF files ==="
for vcf in mutect.vcf mutect2.vcf strelka.vcf filtered_normal_germline_snps_indels.vcf filtered_covered_normal_germline_snps_indels.vcf
do
    copy_to_gcloud_if_exists "$vcf"
done

echo "=== Copying Vaxrank output ==="
copy_pattern vaccine-peptide-report*
copy_pattern all-passing-variants*.csv

echo "=== Copying BAM files ==="
copy_to_gcloud_if_exists normal_aligned_coordinate_sorted_dups_indelreal_bqsr.bam normal.bam
copy_to_gcloud_if_exists normal_aligned_coordinate_sorted_dups_indelreal_bqsr.bai normal.bam.bai
copy_to_gcloud_if_exists tumor_aligned_coordinate_sorted_dups_indelreal_bqsr.bam tumor.bam
copy_to_gcloud_if_exists tumor_aligned_coordinate_sorted_dups_indelreal_bqsr.bai tumor.bam.bai
copy_to_gcloud_if_exists rna_final_sorted.bam rna.bam
copy_to_gcloud_if_exists rna_final_sorted.bam.bai rna.bam.bai

echo "Done."
