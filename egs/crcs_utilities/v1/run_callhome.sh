#!/usr/bin/env bash
# Copyright 2017-2018  David Snyder
#           2017-2018  Matthew Maciejewski
# Apache 2.0.
#
# This is still a work in progress, but implements something similar to
# Greg Sell's and Daniel Garcia-Romero's iVector-based diarization system
# in 'Speaker Diarization With PLDA I-Vector Scoring And Unsupervised
# Calibration'.  The main difference is that we haven't implemented the
# VB resegmentation yet.

. ./cmd.sh
. ./path.sh
set -e
mfccdir=`pwd`/mfcc
vaddir=`pwd`/mfcc
data_root=/export/corpora5/LDC
num_components=2048
ivector_dim=128
stage=1

# Prepare datasets
if [ $stage -le 0 ]; then
  # Prepare a collection of NIST SRE data. This will be used to train the UBM,
  # iVector extractor and PLDA model.
  local/make_sre.sh $data_root data

  # Prepare SWB for UBM and iVector extractor training.
  local/make_swbd2_phase2.pl $data_root/LDC99S79 \
                           data/swbd2_phase2_train
  local/make_swbd2_phase3.pl $data_root/LDC2002S06 \
                           data/swbd2_phase3_train
  local/make_swbd_cellular1.pl $data_root/LDC2001S13 \
                             data/swbd_cellular1_train
  local/make_swbd_cellular2.pl $data_root/LDC2004S07 \
                             data/swbd_cellular2_train

  # Prepare the Callhome portion of NIST SRE 2000.
  local/make_callhome.sh $data_root/LDC2001S97/ data/

  utils/combine_data.sh data/train \
    data/swbd_cellular1_train data/swbd_cellular2_train \
    data/swbd2_phase2_train data/swbd2_phase3_train data/sre
fi

if [ $stage -le 1 ]; then
  for name in callhome1 callhome2; do
    data_dir=data/$name
    out_data_dir=data/${name}_oracle
    mkdir -p $out_data_dir
    cp $data_dir/wav.scp $out_data_dir/
    cat $out_data_dir/wav.scp | awk '{print $1, $1}' > $out_data_dir/spk2utt
    cp $out_data_dir/spk2utt $out_data_dir/utt2spk
  done

  for name in callhome1 callhome2; do
    data_dir=data/${name}_oracle
    steps/make_mfcc.sh --mfcc-config conf/mfcc.conf --nj 40 \
      --cmd "$train_cmd" --write-utt2num-frames true --write-utt2dur true \
      $data_dir exp/make_mfcc $mfccdir
    utils/fix_data_dir.sh $data_dir
  done 
fi
