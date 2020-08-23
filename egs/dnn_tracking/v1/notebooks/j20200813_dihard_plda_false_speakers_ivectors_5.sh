#!/bin/bash
#$ -cwd
#$ -j y -o 20200813_dihard_plda_false_speakers_ivectors_5.log
#$ -e 20200813_dihard_plda_false_speakers_ivectors_5.err
#$ -m eas
#$ -M carloscastillomvc@gmail.com
#$ -l mem_free=15G,ram_free=15G,hostname=b0[3]*|c0[3]*

python3 20200813_dihard_plda_false_speakers_ivectors_5.py
