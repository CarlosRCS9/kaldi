#!/bin/bash
#$ -cwd
#$ -j y -o 20200813_dihard_plda_false_speakers_xvectors_20.log
#$ -e 20200813_dihard_plda_false_speakers_xvectors_20.err
#$ -l mem_free=12G,ram_free=12G
#$ -V

python3 20200813_dihard_plda_false_speakers_xvectors_20.py
