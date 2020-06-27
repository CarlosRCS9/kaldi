#!/bin/bash
# Copyright 2020 Carlos Castillo
# Apache 2.0.

data_folder=data/dihardii/
output_folder=/export/b03/carlosc/data/2020/augmented/dihardii/

stage=0

# By default the RTTM file contains the speaker overlaps implicitly,
# in the first stage we make these overlaps explicit.
if [ $stage -le 0 ]; then
  for name in development evaluation; do
    cat $data_folder$name/ref.rttm | python3 scripts/rttm_explicit_overlap.py \
    > $output_folder$name/ref_explicit_overlap.rttm
  done
fi

if [ $stage -le 1 ]; then
  for name in development evaluation; do
    cat $data_folder$name/ref_explicit_overlap.rttm | python3 scripts/rttm_augment.py \
    $data_folder$name/wav.scp \
    $output_folder$name
  done
fi
