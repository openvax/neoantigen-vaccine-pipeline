# Copyright (c) 2018. Mount Sinai School of Medicine
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

import json
from nose.tools import ok_

import snakemake

# This simulates a dry run on the test data, and mostly checks rule graph validity.
def test_workflow_compiles():
    ok_(snakemake.snakemake(
        'snakemake/fastq_fragment_Snakefile',
        cores=20,
        resources={'mem_mb': 160000},
        configfile='snakemake/idh1_config.json',
        dryrun=True,
        printshellcmds=True,
        targets=[
            '/data/pipeline/workdir/idh1-test-sample/mutect.vcf',
            '/data/pipeline/workdir/idh1-test-sample/mutect2.vcf',
            '/data/pipeline/workdir/idh1-test-sample/strelka.vcf',
        ],
    ))
