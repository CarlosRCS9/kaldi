#!/bin/bash

# Copyright 2019 Carlos Castillo
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e
stage=0

data_folder=$1
output_folder=$data_folder/exp
mfcc_conf=$2
extractor_model=$3

mkdir -p output_folder

# Prepare features
if [ $stage -le 1 ]; then
  rm -rf $output_folder/make_mfcc
  steps/make_mfcc.sh --mfcc-config $mfcc_conf --nj 40 \
    --cmd "$train_cmd" --write-utt2num-frames true --write-utt2dur true \
    $data_folder \
    $output_folder/make_mfcc \
    $data_folder/mfcc
  utils/fix_data_dir.sh $data_folder
fi

# Extract x-vectors
if [ $stage -le 2 ]; then
  rm -rf $output_folder/make_xvectors
  diarization/nnet3/xvector/extract_xvectors.sh --cmd "$train_cmd --mem 5G" \
    --nj 40 --window 1.5 --period 0.75 --apply-cmn false \
    --min-segment 0.5 \
    $extractor_model \
    $data_folder \
    $output_folder/make_xvectors
fi
