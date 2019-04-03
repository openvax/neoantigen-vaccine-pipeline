# Copyright (c) 2019. Mount Sinai School of Medicine
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from argparse import ArgumentParser
import pandas as pd
import yaml

import sys


parser = ArgumentParser()

parser.add_argument(
    "--normal-hs-metrics",
    default="",
    help="Path to Picard's CollectHsMetrics run for the normal DNA BAM")

parser.add_argument(
    "--tumor-hs-metrics",
    default="",
    help="Path to Picard's CollectHsMetrics run for the tumor DNA BAM")

parser.add_argument(
    "--normal-duplication-metrics",
    default="",
    help="Path to Picard's MarkDups metrics output for the normal DNA BAM")

parser.add_argument(
    "--tumor-duplication-metrics",
    default="",
    help="Path to Picard's MarkDups metrics output for the tumor DNA BAM")

parser.add_argument(
    "--metrics-spec-file",
    default="",
    help="Path to YAML file specifying Picard QC related metrics to run and check")

parser.add_argument(
    "--out",
    default="",
    help="Output file path to which to write any failed tests")


def get_metrics(path):
    df = pd.read_csv(path, sep='\t', comment='#')
    return df.head(1).to_dict(orient='records')[0]


def get_coverage_metrics(path):
    metrics = get_metrics(path)
    return {k: metrics[k] for k in ('MEAN_TARGET_COVERAGE', 'MEAN_BAIT_COVERAGE')}


def main(args_list=None):
    if args_list is None:
        args_list = sys.argv[1:]
    args = parser.parse_args(args_list)

    # map file types to input metric file names
    metrics_file_to_path = {
        'normal_dna_hs_metrics': args.normal_hs_metrics,
        'tumor_dna_hs_metrics': args.tumor_hs_metrics,
        'normal_dna_duplication_metrics': args.normal_duplication_metrics,
        'tumor_dna_duplication_metrics': args.tumor_duplication_metrics,
    }

    with open(args.metrics_spec_file) as metrics_spec_file:
        metrics = yaml.load(metrics_spec_file)
        for file_type in metrics:
            print(file_type)

    with open(args.out, 'w') as f:
        f.write('placeholder')


if __name__ == "__main__":
    main()
