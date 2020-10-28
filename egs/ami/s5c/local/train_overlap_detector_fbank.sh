#!/usr/bin/env bash

# Copyright  2020  Desh Raj (Johns Hopkins University)
# Apache 2.0

# This script trains an overlap detector. It is based on the Aspire
# speech activity detection system. Essentially this overlap
# detector is trained on whole recordings so it can be used to
# decode entire recordings without any SAD. We train with 3 targets:
# silence, single, and overlap. As such, at decode time, this
# can also be used as an SAD system.

affix=1c

train_stage=-10
stage=0
nj=50
test_nj=10

test_sets="dev test" # These are the simulated LibriCSS test sets

. ./cmd.sh

if [ -f ./path.sh ]; then . ./path.sh; fi

set -e -u -o pipefail
. utils/parse_options.sh 

train_set=train
dir=exp/overlap_${affix}

train_data_dir=data/${train_set}
whole_data_dir=data/${train_set}_whole_fbank
whole_data_id=$(basename $train_set)

fbankdir=fbank

mkdir -p $dir

if [ $stage -le 1 ]; then
  # The training data may already be segmented, so we first prepare
  # a "whole" training data (not segmented) for training the overlap
  # detector.
  utils/data/convert_data_dir_to_whole.sh $train_data_dir $whole_data_dir
  local/overlap/get_overlap_segments.py $train_data_dir/rttm.annotation > $whole_data_dir/overlap.rttm
fi

###############################################################################
# Extract features for the whole data directory. We extract 40-dim MFCCs to 
# train the NN-based overlap detector.
###############################################################################
if [ $stage -le 2 ]; then
  steps/make_fbank.sh --nj $nj --cmd "$train_cmd"  --write-utt2num-frames true \
    --fbank-config conf/fbank.conf ${whole_data_dir}
  steps/compute_cmvn_stats.sh ${whole_data_dir}
  utils/fix_data_dir.sh ${whole_data_dir}
fi

###############################################################################
# Prepare targets for training the overlap detector
###############################################################################
if [ $stage -le 3 ]; then
  frame_shift=$( cat ${whole_data_dir}/frame_shift ) 
  local/overlap/get_overlap_targets.py \
    --frame-shift $frame_shift \
    ${whole_data_dir}/utt2num_frames ${whole_data_dir}/overlap.rttm - |\
    copy-feats ark,t:- ark,scp:$dir/targets.ark,$dir/targets.scp
fi

###############################################################################
# Train neural network for overlap detector
###############################################################################
if [ $stage -le 4 ]; then
  # Train a STATS-pooling network for SAD
  local/overlap/train_tdnn_1a.sh \
    --targets-dir $dir --dir exp/overlap_$affix/tdnn_stats \
    --data-dir ${whole_data_dir} --affix "1a" || exit 1
fi

################################################################################
# Decoding dev and test sets
################################################################################
if [ $stage -le 5 ]; then
  # Finally we perform decoding with the overlap detector
  for dataset in $test_sets; do
    echo "$0: performing overlap detection on $dataset"
    local/detect_overlaps_fbank.sh --convert_data_dir_to_whole true \
      data/${dataset} \
      exp/overlap_$affix/tdnn_stats_1a exp/overlap_$affix/$dataset

    echo "$0: evaluating output.."
    local/overlap/get_overlap_segments.py data/$dataset/rttm.annotation | grep "overlap" |\
      md-eval.pl -r - -s exp/overlap_$affix/$dataset/rttm_overlap |\
      awk 'or(/MISSED SPEAKER TIME/,/FALARM SPEAKER TIME/)'
  done
fi

exit 0;
