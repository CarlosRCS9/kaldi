#!/bin/bash

# Copyright 2019 Carlos Castillo
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e
stage=0

extractor_model=$1
data_folder=$2

# Prepare features
if [ $stage -le 1 ]; then
  rm -rf $data_folder/make_mfcc

  steps/make_mfcc.sh --mfcc-config conf/mfcc_ivectors_dihard.conf --nj 40 \
    --cmd "$train_cmd" --write-utt2num-frames true --write-utt2dur true \
    $data_folder \
    $data_folder/make_mfcc \
    $data_folder/mfcc
  utils/fix_data_dir.sh $data_folder
fi

# Extract i-vectors
if [ $stage -le 2 ]; then
  rm -rf $data_folder/make_ivectors

  diarization/extract_ivectors.sh --cmd "$train_cmd --mem 20G" \
    --nj 40 --window 1.5 --period 0.75 --apply-cmn false \
    --min-segment 0.5 \
    $extractor_model \
    $data_folder \
    $data_folder/make_ivectors
fi
