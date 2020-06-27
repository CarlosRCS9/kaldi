#!/bin/bash
# Copyright 2020 Carlos Castillo
# Apache 2.0.

data_folder=data/dihardii/
output_folder=/export/b03/carlosc/data/2020/augmented/dihardii/

random_seed=1
length=1.5
overlap=0.5
min_length=0.5

stage=0

# By default the RTTM file contains the speaker overlaps implicitly,
# in the first stage we make these overlaps explicit.
if [ $stage -le 0 ]; then
  echo run.sh stage 0
  for name in development evaluation; do
    cat $data_folder$name/ref.rttm \
    | python3 scripts/rttm_explicit_overlap.py \
    > $output_folder$name/ref_explicit_overlap.rttm
  done
fi

# Generating overlapping speech to augment the database.
if [ $stage -le 1 ]; then
  echo run.sh stage 1
  for name in development evaluation; do
    cat $data_folder$name/ref_explicit_overlap.rttm \
    | python3 scripts/rttm_augment.py \
    $data_folder$name/wav.scp \
    $output_folder$name/ \
    --random-seed=$random_seed
  done
fi

# Applying a sliding window to the segments.
if [ $stage -le 2 ]; then
  echo run.sh stage 2
  for name in development evaluation; do
    cat $data_folder$name/wav_augmented_$random_seed.scp
  done
fi
