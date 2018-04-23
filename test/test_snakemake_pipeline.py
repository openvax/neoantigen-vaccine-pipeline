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
from os import chdir
from os.path import dirname, join
import tempfile

import snakemake

def _get_snakemake_dir_path():
    return join(dirname(__file__), '..', 'snakemake')

# This simulates a dry run on the test data, and mostly checks rule graph validity.
def test_workflow_compiles():
    chdir(_get_snakemake_dir_path())
    with tempfile.TemporaryDirectory() as tmpdirname:
        ok_(snakemake.snakemake(
            'Snakefile',
            cores=20,
            resources={'mem_mb': 160000},
            configfile='idh1_config.json',
            config={'workdir': tmpdirname},
            dryrun=True,
            printshellcmds=True,
            targets=[
                join(tmpdirname, 'idh1-test-sample',
                    'vaccine-peptide-report-mutect-strelka-mutect2.txt'),
                join(tmpdirname, 'idh1-test-sample',
                    'vaccine-peptide-report-mutect-strelka.txt'),
            ],
        ))
