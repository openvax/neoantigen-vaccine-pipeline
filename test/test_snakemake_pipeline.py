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

import getpass
import json
from nose.tools import ok_
from os import chdir, symlink
from os.path import dirname, join
import tempfile

import snakemake

def _get_test_dir_path():
    return dirname(__file__)

def _get_snakemake_dir_path():
    return join(_get_test_dir_path(), '..', 'snakemake')

# This simulates a dry run on the test data, and mostly checks rule graph validity.
def test_workflow_compiles():
    with open(join(_get_test_dir_path(), 'idh1_config.json'), 'r') as idh1_config_file:
        config_file_contents = idh1_config_file.read()
    
    chdir(_get_snakemake_dir_path())

    with tempfile.TemporaryDirectory() as workdir:
        with tempfile.TemporaryDirectory() as referencedir:
            # populate reference files with random crap
            with open(join(referencedir, 'b37decoy.fasta'), 'w') as genome:
                genome.write('placeholder')
            with open(join(referencedir, 'transcripts.gtf'), 'w') as transcripts:
                transcripts.write('placeholder')
            with open(join(referencedir, 'dbsnp.vcf'), 'w') as dbsnp:
                dbsnp.write('placeholder')
            with open(join(referencedir, 'cosmic.vcf'), 'w') as cosmic:
                cosmic.write('placeholder')


            # kinda gross, but: replace /outputs, /reference-genome paths in config file with
            # temp dir locations; /inputs with the datagen location in this repo
            config_file_contents = config_file_contents.replace(
                '/outputs', workdir).replace(
                '/reference-genome/b37decoy', referencedir).replace(
                '/inputs', '../datagen')
            with tempfile.NamedTemporaryFile(mode='w') as config_tmpfile:
                config_tmpfile.write(config_file_contents)
                config_tmpfile.seek(0)
                ok_(snakemake.snakemake(
                    'Snakefile',
                    cores=20,
                    resources={'mem_mb': 160000},
                    configfile=config_tmpfile.name,
                    config={'num_threads': 22},
                    dryrun=True,
                    printshellcmds=True,
                    targets=[
                        join(
                            workdir, 
                            'idh1-test-sample',
                            'vaccine-peptide-report-mutect-strelka-mutect2.txt'),
                        join(
                            workdir,
                            'idh1-test-sample',
                            'vaccine-peptide-report-mutect-strelka.txt'),
                        ],
                    stats=join(workdir, 'idh1-test-sample', 'stats.json'),
                    printd3dag=True,
                    summary=True,
                ))
