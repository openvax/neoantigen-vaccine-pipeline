# local-wgs1 benchmark

This dataset contains small BAMs and FASTQs overlapping reasonably
high-confidence variants from a patient with high quality whole genome
sequencing. This can be used to measure sensitivity.

The data was derived from the guacamole cancer-wgs1 test data, which came from
an australian ovarian cancer study (AOCS) patient. It contains reads
overlapping ~320 called variants that were published with this dataset. The
AOCS uses their own pipeline: https://sourceforge.net/projects/adamajava/

The published calls are in [published_calls.csv](published_calls.csv) in
varlens format. These are mostly only the calls that were validated using an
orthogonal method, although the details of the validation are not clear. Many
other calls were made for this patient that were not attempted for validation
and are not included here.  Note this is whole genome sequencing.

Reads overlapping the selected variants were extracted from the original BAM
(aligned by the AOCS project) and written to the small BAMs included here.

There are two tumor samples (primary and recurrence) and one normal sample. The
published calls are a union of calls for both. It would probably be reasonable
to just merge the primary.fastq and recurrence.fastq into one file and use that
as the tumor sample. Or could call separately on each and merge. I created a
merged fastq for by running:

```
zcat primary.fastq.gz recurrence.fastq.gz | gzip - > tumor_combined.fastq.gz
```

The original AOCS data was aligned to a nonstandard reference that seems to be
b37 but with "chr" prefixes (but is not hg19 since mitochondria and some other
contigs are named as in b37).  This is an issue if we want to use this data to
run from the BAM file. Running variant calling using these BAMs against hg19
may work though, if we ignore mitochondrial variants.

FASTQs were generated from the BAMs using this
[bam2fastq](https://github.com/jts/bam2fastq) tool with `--all-to-stdout`
option. However, read mates were lost, so it is possible that some reads in
these FASTQs will not align to their correct locus.

## To get data

```
mkdir downloaded
wget https://www.dropbox.com/sh/naqgsi744z9ccqp/AADMEoLnHPupbXhLwHOz8MyDa?dl=1 -O downloaded/downloaded.zip
unzip downloaded/downloaded.zip -d downloaded/
```
