#!/bin/bash

. ./cmd.sh
. ./path.sh
set -e
num_components=2048
ivector_dim=128
stage=0

# Prepare features
if [ $stage -le 1 ]; then
  for name in callhome1; do
    steps/make_mfcc.sh --mfcc-config conf/mfcc.conf --nj 40 \
      --cmd "$train_cmd" --write-utt2num-frames true --write-utt2dur true \
      data/$name exp/make_mfcc $mfccdir
    utils/fix_data_dir.sh data/$name
  done
fi

# Extract i-vectors
if [ $stage -le 1 ]; then
  diarization/extract_ivectors.sh --cmd "$train_cmd --mem 20G" \
    --nj 40 --window 1.5 --period 0.75 --apply-cmn false \
    --min-segment 0.5 exp/extractor_c${num_components}_i${ivector_dim} \
    data/callhome1 exp/ivectors_callhome1
fi

