#!/bin/bash

. ./cmd.sh
. ./path.sh
set -e
num_components=2048
ivector_dim=128
stage=5

datadir=$1
outputdir=$2

# Prepare features
if [ $stage -le 1 ]; then
  steps/make_mfcc.sh --mfcc-config conf/mfcc_ivectors.conf --nj 40 --cmd "$train_cmd" --write-utt2num-frames true --write-utt2dur true \
    $datadir \
    $outputdir/make_mfcc \
    $mfccdir
  utils/fix_data_dir.sh $datadir
fi

# Extract i-vectors
if [ $stage -le 2 ]; then
  diarization/extract_ivectors.sh --cmd "$train_cmd --mem 20G" --nj 40 --window 1.5 --period 0.75 --apply-cmn false --min-segment 0.5 \
    exp/extractor_c${num_components}_i${ivector_dim} \
    $datadir \
    $outputdir/make_ivectors
  copy-vector \
    scp:$outputdir/make_ivectors/ivector.scp \
    ark,t:$outputdir/make_ivectors/ivector.txt
  echo $outputdir/make_ivectors/ivector.txt
fi

# Prepare features
if [ $stage -le 3 ]; then
  steps/make_mfcc.sh --mfcc-config conf/mfcc_xvectors.conf --nj 40 --cmd "$train_cmd" --write-utt2num-frames true --write-utt2dur true \
    $datadir \
    $outputdir/make_mfcc \
    $mfccdir
  utils/fix_data_dir.sh $datadir
fi

# Extract x-vectors
if [ $stage -le 4 ]; then
  diarization/nnet3/xvector/extract_xvectors.sh --cmd "$train_cmd --mem 5G" --nj 40 --window 1.5 --period 0.75 --apply-cmn false --min-segment 0.5 \
    exp/xvector_nnet_1a \
    $datadir \
    $outputdir/make_xvectors
  copy-vector \
    scp:$outputdir/make_xvectors/xvector.scp \
    ark,t:$outputdir/make_xvectors/xvector.txt
  echo $outputdir/make_xvectors/xvector.txt
fi
