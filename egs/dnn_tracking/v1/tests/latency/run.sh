#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e

stage=3

recording_filepath=/export/b03/carlosc/data/2020/tests/iaaa.sph
ivector_mfcc_conf=conf/mfcc_callhome_ivectors.conf
ivector_extractor_model=exp/extractor_c2048_i128
xvector_mfcc_conf=conf/mfcc_callhome_xvectors.conf
xvector_extractor_model=exp/xvector_nnet_1a_pre

data_dir=data/tests/latency

for i in {1..100}; do
if [ $stage -le 3 ]; then
  rm -rf $data_dir
  mkdir -p $data_dir
  # segments
  echo test_utterance test_recording 0 1 > $data_dir/segments
  # utt2spk
  echo test_utterance test_speaker > $data_dir/utt2spk
  # spk2utt
  cat $data_dir/utt2spk | utils/utt2spk_to_spk2utt.pl > $data_dir/spk2utt
  # wav.scp
  #echo test_recording $recording_filepath > $data_dir/wav.scp
  echo "test_recording sph2pipe -f wav -p $recording_filepath |" > $data_dir/wav.scp
fi

if [ $stage -le 1 ]; then
  steps/make_mfcc.sh \
    --cmd "run.pl" \
    --mfcc-config $ivector_mfcc_conf \
    --nj 1 \
    --write-utt2dur true \
    --write-utt2num-frames true \
    $data_dir
  utils/fix_data_dir.sh $data_dir
fi

if [ $stage -le 2 ]; then
  diarization/extract_ivectors.sh \
    --apply-cmn false \
    --cmd "run.pl" \
    --min-segment 0.5 \
    --nj 1 \
    --period 0.75 \
    --window 1.5 \
    $ivector_extractor_model \
    $data_dir \
    $data_dir/make_ivectors
fi

if [ $stage -le 4 ]; then
  steps/make_mfcc.sh \
    --cmd "run.pl" \
    --mfcc-config $xvector_mfcc_conf \
    --nj 1 \
    --write-utt2dur true \
    --write-utt2num-frames true \
    $data_dir
  utils/fix_data_dir.sh $data_dir
fi

if [ $stage -le 5 ]; then
  diarization/nnet3/xvector/extract_xvectors.sh \
    --cmd "run.pl" \
    --nj 1 \
    --window 1.5 \
    --period 0.75 \
    --apply-cmn false \
    --min-segment 0.5 \
    $xvector_extractor_model \
    $data_dir \
    $data_dir/make_xvectors
fi

done
