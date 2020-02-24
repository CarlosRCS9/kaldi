#!/bin/bash

. ./cmd.sh
. ./path.sh
set -e
num_components=2048
ivector_dim=128
stage=0

mfccdir=$(pwd)/mfcc
datadir=$1
outputdir=$2

# Prepare features
if [ $stage -le 1 ]; then
  rm -rf $outputdir/make_mfcc
  steps/make_mfcc.sh --mfcc-config conf/mfcc_ivectors.conf --nj 40 --cmd "$train_cmd" --write-utt2num-frames true --write-utt2dur true \
    $datadir \
    $outputdir/make_mfcc \
    $mfccdir
  utils/fix_data_dir.sh $datadir
fi

# Extract i-vectors
if [ $stage -le 2 ]; then
  rm -rf $outputdir/make_ivectors
  diarization/extract_ivectors.sh --cmd "$train_cmd --mem 20G" --nj 40 --window 1.5 --period 0.75 --apply-cmn false --min-segment 0.5 \
    exp/extractor_c${num_components}_i${ivector_dim} \
    $datadir \
    $outputdir/make_ivectors
fi

if [ $stage -le 3 ]; then
  copy-vector \
    scp:$outputdir/make_ivectors/ivector.scp \
    ark,t:$outputdir/make_ivectors/ivector.txt
  echo $outputdir/make_ivectors/ivector.txt
fi

# Prepare features
if [ $stage -le 4 ]; then
  rm -rf $outputdir/make_mfcc
  steps/make_mfcc.sh --mfcc-config conf/mfcc_xvectors.conf --nj 40 --cmd "$train_cmd" --write-utt2num-frames true --write-utt2dur true \
    $datadir \
    $outputdir/make_mfcc \
    $mfccdir
  utils/fix_data_dir.sh $datadir
fi

# Extract x-vectors
if [ $stage -le 5 ]; then
  rm -rf $outputdir/make_xvectors
  diarization/nnet3/xvector/extract_xvectors.sh --cmd "$train_cmd --mem 20G" --nj 40 --window 1.5 --period 0.75 --apply-cmn false --min-segment 0.5 \
    exp/xvector_nnet_1a \
    $datadir \
    $outputdir/make_xvectors
fi

#if [ $stage -le 6 ]; then
#  "$train_cmd" $outputdir/make_xvectors/log/plda.log \
#    ivector-compute-plda ark:$outputdir/make_xvectors/spk2utt \
#      "ark:ivector-subtract-global-mean \
#      scp:$outputdir/make_xvectors/xvector.scp ark:- \
#      | transform-vec $outputdir/make_xvectors/transform.mat ark:- ark:- \
#      | ivector-normalize-length ark:- ark:- |" \
#    $outputdir/make_xvectors/plda || exit 1;
#fi

if [ $stage -le 7 ]; then
  copy-vector \
    scp:$outputdir/make_xvectors/xvector.scp \
    ark,t:$outputdir/make_xvectors/xvector.txt
  echo $outputdir/make_xvectors/xvector.txt
fi
