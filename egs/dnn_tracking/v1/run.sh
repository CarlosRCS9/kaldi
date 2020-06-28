#!/bin/bash
# Copyright 2020 Carlos Castillo
# Apache 2.0.

. ./path.sh

data_folder=data/dihardii/
output_folder=/export/b03/carlosc/data/2020/augmented/dihardii/
mfcc_conf=conf/mfcc_ivectors_dihard.conf
extractor_model=/export/c03/carloscastillo/repos/kaldi_fix/egs/online_diarization/v1/exp/extractor_c2048_i400/extractor_c2048_i400

random_seed=0
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
    cat $output_folder$name/ref_augmented_$random_seed.rttm \
    | python3 scripts/rttm_split.py $length $overlap --min-length=$min_length \
    > $output_folder$name/ref_augmented_$random_seed'_'$length'_'$overlap'_'$min_length.rttm
  done
fi

# Extracting features
if [ $stage -le 3 ]; then
  echo run.sh stage 3
  for name in development evaluation; do
    cat $output_folder$name/ref_augmented_$random_seed'_'$length'_'$overlap'_'$min_length.rttm \
    | python3 scripts/rttm_extract.py \
    $output_folder$name/wav_augmented_$random_seed.scp \
    $output_folder$name/ \
    $mfcc_conf \
    $extractor_model
  done
fi

# Copying features
if [ $stage -le 4 ]; then
  echo run.sh stage 4
  for name in development evaluation; do
    copy-vector \
    scp:$output_folder$name/augmented_$random_seed/exp/make_ivectors/ivector.scp \
    ark,t:$output_folder$name/augmented_$random_seed/exp/make_ivectors/ivector.txt
  done
fi
