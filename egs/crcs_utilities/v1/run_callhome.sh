#!/usr/bin/env bash
# Copyright 2017-2018  David Snyder
#           2017-2018  Matthew Maciejewski
#
# Apache 2.0.
#
# This recipe demonstrates the use of x-vectors for speaker diarization.
# The scripts are based on the recipe in ../v1/run.sh, but clusters x-vectors
# instead of i-vectors.  It is similar to the x-vector-based diarization system
# described in "Diarization is Hard: Some Experiences and Lessons Learned for
# the JHU Team in the Inaugural DIHARD Challenge" by Sell et al.  The main
# difference is that we haven't implemented the VB resegmentation yet.

. ./cmd.sh
. ./path.sh
set -e
mfccdir=`pwd`/mfcc
vaddir=`pwd`/mfcc
data_root=/export/corpora5/LDC
stage=0
nnet_dir=exp/xvector_nnet_1a/
num_components=1024 # the number of UBM components (used for VB resegmentation)
ivector_dim=400 # the dimension of i-vector (used for VB resegmentation)

# Prepare datasets
if [ $stage -le 0 ]; then
  # Prepare a collection of NIST SRE data. This will be used to train,
  # x-vector DNN and PLDA model.
  local/make_sre.sh $data_root data

  # Prepare SWB for x-vector DNN training.
  local/make_swbd2_phase1.pl /export/corpora/LDC/LDC98S75 \
    data/swbd2_phase1_train
  local/make_swbd2_phase2.pl $data_root/LDC99S79 \
                           data/swbd2_phase2_train
  local/make_swbd2_phase3.pl $data_root/LDC2002S06 \
                           data/swbd2_phase3_train
  local/make_swbd_cellular1.pl $data_root/LDC2001S13 \
                             data/swbd_cellular1_train
  local/make_swbd_cellular2.pl $data_root/LDC2004S07 \
                             data/swbd_cellular2_train

  # Prepare the Callhome portion of NIST SRE 2000.
  local/make_callhome.sh /export/corpora/NIST/LDC2001S97/ data/

  utils/combine_data.sh data/train \
    data/swbd_cellular1_train data/swbd_cellular2_train \
    data/swbd2_phase1_train \
    data/swbd2_phase2_train data/swbd2_phase3_train data/sre
fi

