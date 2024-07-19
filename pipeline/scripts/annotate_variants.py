"""
Count the reads supporting reference and alternate alleles for given variants in BAM files.

Arguments:
variants_file : str : CSV file containing variants with columns: contig, start, ref, alt. You can give the "all passing
                    variants" file that vaxrank outputs here.
--bam : str, str    : Label and path to BAM file (can be repeated for multiple BAM files)
--output : str      : Output CSV file to save the results

Example:
python count_alleles_varcode_tqdm_rna.py \
    variants.csv \
    --bam normal_dna /path/to/tumor_rna.bam \
    --bam tumor_rna /path/to/tumor_rna.bam \
    --bam tumor_dna /path/to/tumor_dna.bam \
    --output output_with_counts.csv

Author: Tim O'Donnell, July 2024
"""

import pysam
import numpy as np
import pandas as pd
import argparse
from tqdm import tqdm

import pysam
import pandas as pd

def get_aligned_pairs_with_cigar(read):
    """
    Get aligned pairs with the CIGAR operation and read sequence at each position.

    Parameters:
    read (pysam.AlignedSegment): A read from a BAM file.

    Returns:
    pd.DataFrame: A DataFrame containing the reference position, read position, CIGAR operation, and read base.
    """
    aligned_pairs = read.get_aligned_pairs(with_seq=False)
    cigar_operations = read.cigartuples

    # Create lists to hold the result
    ref_positions = []
    read_positions = []
    cigar_ops = []
    read_bases = []

    # Variables to track the current position in the read and reference
    read_index = 0

    for operation, length in cigar_operations:
        for _ in range(length):
            if read_index < len(aligned_pairs):
                read_pos, ref_pos = aligned_pairs[read_index]

                if operation == 0:  # Match or mismatch
                    cigar_op = 'M'
                elif operation == 1:  # Insertion
                    cigar_op = 'I'
                elif operation == 2:  # Deletion
                    cigar_op = 'D'
                elif operation == 3:  # Skip (N)
                    cigar_op = 'N'
                elif operation == 4:  # Soft clipping
                    cigar_op = 'S'
                elif operation == 5:  # Hard clipping
                    cigar_op = 'H'
                elif operation == 6:  # Padding (P)
                    cigar_op = 'P'
                else:
                    cigar_op = None

                if read_pos is not None and read_pos < len(read.query_sequence):
                    read_base = read.query_sequence[read_pos]
                else:
                    read_base = None

                ref_positions.append(ref_pos)
                read_positions.append(read_pos)
                cigar_ops.append(cigar_op)
                read_bases.append(read_base)

                read_index += 1

    df = pd.DataFrame({
        'reference_position': ref_positions,
        'read_position': read_positions,
        'cigar_operation': cigar_ops,
        'read_base': read_bases
    })
    df['reference_position'] = df['reference_position'].astype(float)
    df['read_position'] = df['read_position'].astype(float)
    return df
def count_alleles(bam_file, variants_df, label, min_mapq=10):
    """
    Function to count reads supporting reference and alternate alleles for given variants in a BAM file.

    Parameters:
    bam_file (str): Path to the BAM file.
    variants_df (pd.DataFrame): DataFrame containing variants with columns 'contig', 'start', 'ref', 'alt'.
    label (str): Label for the BAM file (used to name the count columns).

    Returns:
    pd.DataFrame: DataFrame with additional columns for read counts and depth.
    """
    # Open the BAM file
    bam = pysam.AlignmentFile(bam_file, "rb")

    # index the bam if needed
    if not bam.has_index():
        print(f"Indexing {bam_file}")
        pysam.index(bam_file)
        bam = pysam.AlignmentFile(bam_file, "rb")

    # Initialize new columns in the DataFrame
    variants_df[f'{label}_ref_count'] = 0
    variants_df[f'{label}_alt_count'] = 0
    variants_df[f'{label}_depth'] = 0
    variants_df[f'{label}_vaf'] = np.nan

    # Iterate over each variant
    for idx, row in tqdm(variants_df.iterrows(), total=variants_df.shape[0],
            desc=f"Annotating {label}"):
        contig = row['contig']
        start = row['start']
        ref = row['ref']
        alt = row['alt']

        ref_count = 0
        alt_count = 0
        total_depth = 0

        # Deal with varcode name mangling
        possible_contigs = [contig, "chr" + contig]
        if contig == "MT":
            possible_contigs.append("M")
            possible_contigs.append("chrM")

        correct_contig = None
        reads = None
        for possible_contig in possible_contigs:
            try:
                reads = bam.fetch(possible_contig, start - 1, start)
                correct_contig = possible_contig
                break
            except ValueError:
                pass
        if correct_contig is None:
            raise ValueError(
                f"Could not find any of {possible_contigs} in BAM file {bam_file}. Valid contigs are: {bam.references}")

        variants_df.at[idx, 'unmangled_contig'] = correct_contig

        # Exclude reads with very low mapping quality or that are marked as duplicates.
        reads = [read for read in reads if read.mapping_quality >= min_mapq]
        reads = [read for read in reads if not read.is_duplicate]

        if alt == "":
            # Handle deletion
            num_bases_deleted = len(ref)
            for read in reads:
                read_positions = get_aligned_pairs_with_cigar(read)
                read_positions = read_positions.loc[
                    (~read_positions.cigar_operation.isin(['N', 'S']))
                ]

                try:
                    relevant_read_positions = read_positions.set_index("reference_position").loc[
                        start - 1 :
                        start - 1 + num_bases_deleted - 1
                    ]
                except KeyError:
                    continue

                if len(relevant_read_positions) > 0:
                    total_depth += 1
                    if relevant_read_positions.read_position.isnull().all():
                        alt_count += 1
                    elif (~relevant_read_positions.read_position.isnull()).all():
                        ref_count += 1

        elif ref == "":
            # Handle insertion
            for read in reads:
                read_positions = get_aligned_pairs_with_cigar(read)
                read_positions["reference_position"] = read_positions["reference_position"].fillna(method="ffill")
                relevant_read_positions = read_positions.loc[
                    (~read_positions.cigar_operation.isin(['N', 'S'])) &
                    (read_positions.reference_position == start - 1)
                ]
                if len(relevant_read_positions) > 0:
                    total_depth += 1
                    read_sequence = "".join(relevant_read_positions.iloc[1:].read_base.fillna(""))
                    if read_sequence == alt:
                        alt_count += 1
                    elif read_sequence == ref:
                        ref_count += 1

        else:
            np.testing.assert_equal(len(ref), len(alt))
            # Handle substitution
            for read in reads:
                read_positions = get_aligned_pairs_with_cigar(read)
                read_positions["reference_position"] = read_positions["reference_position"].fillna(method="ffill")
                relevant_read_positions = read_positions.loc[
                    (~read_positions.cigar_operation.isin(['N', 'S'])) &
                    (read_positions.reference_position >= start - 1) &
                    (read_positions.reference_position < start - 1 + len(ref))
                ]

                if len(relevant_read_positions) > 0:
                    total_depth += 1
                    read_sequence = "".join(relevant_read_positions.read_base.fillna(""))
                    if read_sequence == alt:
                        alt_count += 1
                    elif read_sequence == ref:
                        ref_count += 1

        # Update the counts and depth in the DataFrame
        variants_df.at[idx, f'{label}_ref_count'] = ref_count
        variants_df.at[idx, f'{label}_alt_count'] = alt_count
        variants_df.at[idx, f'{label}_depth'] = total_depth
        if total_depth > 0:
            variants_df.at[idx, f'{label}_vaf'] = alt_count / total_depth

    # Close the BAM file
    bam.close()

    return variants_df

disclaimer = ("""
*****************************
Note: this script is a useful first-pass for annotating VAFs, but it is simplistic. It works directly with the
alignments in the BAM and does not attempt to do any kind of realignment. That means it's not "seeing" the realigned version
that e.g. mutect2 will be operating from. Especially for indels or variants with unexpectedly low VAFs you should
manually check the results yourself in IGV. Also note that there may be discrepancies between what this script outputs
and what you see in IGV due to differences in filters. This script counts reads with mapping quality at least 10 that
are not marked as duplicates.
*****************************
""".strip())

def main(variants_file, bam_files, output_file):
    print(disclaimer)

    # Load the variants DataFrame
    variants_df = pd.read_csv(variants_file)

    variants_df["contig"] = variants_df["contig"].astype(str)
    variants_df["ref"] = variants_df["ref"].fillna("").astype(str)
    variants_df["alt"] = variants_df["alt"].fillna("").astype(str)

    if "gene_name" in variants_df.columns:
        variants_df["gene_name"] = variants_df["gene_name"].fillna("").astype(str)

    if "unmangled_contig" not in variants_df.columns:
        variants_df["unmangled_contig"] = None

    # Process each BAM file
    for label, bam_path in bam_files:
        variants_df = count_alleles(bam_path, variants_df, label)

    # Save the updated DataFrame to the specified output file
    variants_df.to_csv(output_file, index=False)
    print(f'Wrote: {output_file}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Count alleles in BAM files for given variants.')
    parser.add_argument('variants_file', type=str,
        help='CSV file containing variants with columns: contig, start, ref, alt')
    parser.add_argument('--bam', type=str, nargs=2, action='append',
        required=True, help='Label and path to BAM file. Example: --bam tumor_rna /path/to/tumor.bam')
    parser.add_argument('--output', type=str, required=True,
        help='Output CSV file to save the results')

    args = parser.parse_args()

    main(args.variants_file, args.bam, args.output)
