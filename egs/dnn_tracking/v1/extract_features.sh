#!/bin/bash

. ./cmd.sh
. ./path.sh
set -e
stage=0

mfccdir=$(pwd)/mfcc
datadir=$1
outputdir=$2

if [[ $datadir == *"callhome"* ]]; then
  ivector_mfcc_conf=conf/mfcc_ivectors.conf
  xvector_mfcc_conf=conf/mfcc_xvectors.conf
  ivector_extractor=exp/extractor_c2048_i128
  xvector_extractor=exp/xvector_nnet_1a_pre
elif [[ $datadir == *"dihard_2019"* ]]; then
  ivector_mfcc_conf=conf/mfcc_ivectors_dihard.conf
  xvector_mfcc_conf=conf/mfcc_xvectors_dihard.conf
  ivector_extractor=exp/extractor_c2048_i400/extractor_c2048_i400
  xvector_extractor=exp/xvector_nnet_1a_dihard
fi

# Prepare features
if [ $stage -le 1 ]; then
  rm -rf $outputdir/make_mfcc

  steps/make_mfcc.sh --mfcc-config $ivector_mfcc_conf --nj 40 \
    --cmd "$train_cmd" --write-utt2num-frames true --write-utt2dur true \
    $datadir \
    $outputdir/make_mfcc \
    $mfccdir
  utils/fix_data_dir.sh $datadir
fi

# Extract i-vectors
if [ $stage -le 2 ]; then
  rm -rf $outputdir/make_ivectors

  diarization/extract_ivectors.sh --cmd "$train_cmd --mem 20G" \
    --nj 40 --window 1.5 --period 0.75 --apply-cmn false \
    --min-segment 0.5 \
    $ivector_extractor \
    $datadir \
    $outputdir/make_ivectors
fi

# Copy vectors
if [ $stage -le 3 ]; then
  copy-vector \
    scp:$outputdir/make_ivectors/ivector.scp \
    ark,t:$outputdir/make_ivectors/ivector.txt
  echo $outputdir/make_ivectors/ivector.txt
fi

# Prepare features
if [ $stage -le 4 ]; then
  rm -rf $outputdir/make_mfcc

  steps/make_mfcc.sh --mfcc-config $xvector_mfcc_conf --nj 40 \
    --cmd "$train_cmd" --write-utt2num-frames true --write-utt2dur true \
    $datadir \
    $outputdir/make_mfcc \
    $mfccdir
  utils/fix_data_dir.sh $datadir
fi

# Extract x-vectors
if [ $stage -le 5 ]; then
  rm -rf $outputdir/make_xvectors

  diarization/nnet3/xvector/extract_xvectors.sh --cmd "$train_cmd --mem 5G" \
    --nj 40 --window 1.5 --period 0.75 --apply-cmn false \
    --min-segment 0.5 \
    $xvector_extractor \
    $datadir \
    $outputdir/make_xvectors
fi

# Normalize x-vectors
if [ $stage -le 6 ]; then
  ivector-subtract-global-mean \
    scp:$outputdir/make_xvectors/xvector.scp ark:- \
    | transform-vec $outputdir/make_xvectors/transform.mat ark:- ark:- \
    | ivector-normalize-length ark:- ark:$outputdir/make_xvectors/norm_xvector.ark
fi

# Copy vectors
if [ $stage -le 7 ]; then
  copy-vector \
    ark:$outputdir/make_xvectors/norm_xvector.ark \
    ark,t:$outputdir/make_xvectors/xvector.txt
  echo $outputdir/make_xvectors/xvector.txt
fi
