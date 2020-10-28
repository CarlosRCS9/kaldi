#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e

suffix=_EXP029
rtve_root=/export/corpora5/RTVE
nnet_dir=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/exp/sre19-av-models/xvector_nnet_5a.1.vcc.v2
plda_dir=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/exp/sre19-av-models/xvector_nnet_5a.1.vcc.v2/xvectors_rtve_2018_2020_janto5a_train
mfcc_conf=exp/sre19-av-models/mfcc_16k.conf

nj=9
stage=0

if [ $stage -le 0 ]; then
  # <speaker-overlap> <speaker-rename>
  #local/make_rtve_2018_dev2_2.sh eval $rtve_root/RTVE2018DB/dev2 data/rtve_2018${suffix} true false
  local/make_rtve_2020_dev_2.sh eval $rtve_root/RTVE2020DB/dev data/rtve_2020${suffix} true false
fi

if [ $stage -le 1 ]; then
  for name in rtve_2020${suffix}; do
    data_dir=data/$name

    steps/make_mfcc.sh \
      --cmd "$train_cmd" \
      --mfcc-config conf/mfcc_detect_overlaps.conf \
      --nj 9 \
      --write-utt2num-frames true \
      --write-utt2dur true \
      $data_dir

    steps/compute_cmvn_stats.sh \
      $data_dir

    utils/fix_data_dir.sh $data_dir
  done
fi

if [ $stage -le 2 ]; then
  for name in rtve_2020${suffix}; do
    data_dir=data/$name
    output_dir=exp/$name
    local/detect_overlaps.sh \
      --cmd "$train_cmd" \
      --nj 9 \
      $data_dir \
      exp/overlap_1a/tdnn_stats_1a \
      $output_dir
  done
fi
