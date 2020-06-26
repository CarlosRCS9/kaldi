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
