#!/usr/bin/env bash
# Copyright   2017   Johns Hopkins University (Author: Daniel Garcia-Romero)
#             2017   Johns Hopkins University (Author: Daniel Povey)
#        2017-2018   David Snyder
#             2018   Ewald Enzinger
#             2018   Zili Huang
# Apache 2.0.
#
# See ../README.txt for more info on data required.
# Results (diarization error rate) are inline in comments below.

. ./cmd.sh
. ./path.sh
set -e
mfccdir=`pwd`/mfcc
vaddir=`pwd`/mfcc

voxceleb1_root=/export/corpora5/VoxCeleb1_v1
voxceleb2_root=/export/corpora5/VoxCeleb2
nnet_dir=exp/xvector_nnet_1a
musan_root=/export/corpora5/JHU/musan
dihard_2018_dev=/export/corpora5/LDC/LDC2018E31
dihard_2018_eval=/export/corpora5/LDC/LDC2018E32v1.1

stage=0

if [ $stage -le 0 ]; then
  local/make_voxceleb2.pl $voxceleb2_root dev data/voxceleb2_train
  local/make_voxceleb2.pl $voxceleb2_root test data/voxceleb2_test

  # Now prepare the VoxCeleb1 train and test data.  If you downloaded the corpus soon
  # after it was first released, you may need to use an older version of the script, which
  # can be invoked as follows:
  local/make_voxceleb1.pl $voxceleb1_root data
  # local/make_voxceleb1_v2.pl $voxceleb1_root dev data/voxceleb1_train
  # local/make_voxceleb1_v2.pl $voxceleb1_root test data/voxceleb1_test

  # We'll train on all of VoxCeleb2, plus the training portion of VoxCeleb1.
  # This should give 7,351 speakers and 1,277,503 utterances.
  utils/combine_data.sh data/train data/voxceleb2_train data/voxceleb2_test data/voxceleb1_train

  # Prepare the development and evaluation set for DIHARD 2018.
  # local/make_dihard_2018_dev.sh $dihard_2018_dev data/dihard_2018_dev
  # local/make_dihard_2018_eval.sh $dihard_2018_eval data/dihard_2018_eval
fi
