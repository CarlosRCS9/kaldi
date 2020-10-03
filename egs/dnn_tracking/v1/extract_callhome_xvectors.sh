#!/bin/bash
# Copyright 2020 Carlos Castillo
# Apache 2.0.

. ./path.sh

data_folder=data/callhome/
mfcc_conf=conf/mfcc_callhome_xvectors.conf
extractor_dim=400
extractor_model=../../callhome_diarization/v2/exp/xvector_nnet_1a_${extractor_dim}

output_folder=/export/b03/carlosc/data/2020/augmented/callhome/

random_seed=0
length=1.0
overlap=0.5
min_length=0.5

stage=3

# By default the RTTM file contains the speaker overlaps implicitly,
# in the first stage we make these overlaps explicit.
if [ $stage -le 0 ]; then
  echo run.sh stage 0
  for name in callhome1 callhome2; do
    folder=$output_folder$name
    mkdir -p $folder

    cat $data_folder$name/ref.rttm \
    | python3 scripts/rttm_explicit_overlap.py \
    > $folder/ref_explicit_overlap.rttm
  done
fi

# Generating overlapping speech to augment the database.
if [ $stage -le 1 ]; then
  echo run.sh stage 1
  for name in callhome1 callhome2; do
    folder=$output_folder$name
    cat $folder/ref_explicit_overlap.rttm \
    | python3 scripts/rttm_augment.py \
    $data_folder$name/wav.scp \
    $folder/ \
    --random-seed=$random_seed
  done
fi

# Applying a sliding window to the segments.
if [ $stage -le 2 ]; then
  echo run.sh stage 2
  for name in callhome1 callhome2; do
    folder=$output_folder$name
    mkdir -p $folder/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim

    cat $folder/ref_augmented_$random_seed.rttm \
    | python3 scripts/rttm_split.py $length $overlap --min-length=$min_length \
    > $folder/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim/ref.rttm
  done
fi

# Extracting features
if [ $stage -le 3 ]; then
  echo run.sh stage 3
  for name in callhome1 callhome2; do
    folder=$output_folder$name
    cat $folder/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim/ref.rttm \
    | python3 scripts/rttm_extract.py \
    $folder/wav_augmented_$random_seed.scp \
    $folder/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim/ \
    $mfcc_conf \
    'xvectors' \
    $extractor_model
  done
fi

# Copying features
if [ $stage -le 4 ]; then
  echo run.sh stage 4
  for name in callhome1 callhome2; do
    folder=$output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim
    copy-vector \
    scp:$folder/exp/make_xvectors/xvector.scp \
    ark,t:$folder/exp/make_xvectors/xvector.txt
  done
fi
