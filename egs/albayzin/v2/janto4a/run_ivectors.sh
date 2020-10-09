#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e

suffix=_EXP006
nnet_dir=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/exp/sre19-av-models/xvector_nnet_4a.1.vcc
rtve_root=/export/corpora5/RTVE

num_components=2048
ivector_dim=128

stage=2

if [ $stage -le 0 ]; then
  # <speaker-overlap> <speaker-rename>
  local/make_rtve_2018_dev2.sh train $rtve_root/RTVE2018DB/dev2 data/rtve_2018${suffix}_train true true
  local/make_rtve_2020_dev.sh train $rtve_root/RTVE2020DB/dev data/rtve_2020${suffix}_train true true
fi

if [ $stage -le 1 ]; then
  for name in rtve_2018${suffix}_train rtve_2020${suffix}_train; do
    steps/make_mfcc.sh \
      --mfcc-config exp/sre19-av-models/mfcc_16k.conf \
      --nj 40 \
      --cmd "$train_cmd --max-jobs-run 20" \
      --write-utt2num-frames true \
      --write-utt2dur true \
     data/$name
    utils/fix_data_dir.sh data/$name
  done

  for name in rtve_2018${suffix}_train rtve_2020${suffix}_train; do
    mv data/$name/ref.rttm data/$name/ref.rttm.bak
    python3 scripts/segments_to_rttm.py data/$name > data/$name/ref.rttm
    python3 scripts/make_oracle_vad.py data/$name
  done

  for name in rtve_2018${suffix}_train rtve_2020${suffix}_train; do
    rm -rf data/${name}_cmn
    local/nnet3/xvector/prepare_feats.sh \
      --nj 40 \
      --cmd "$train_cmd" \
      data/$name \
      data/${name}_cmn \
      exp/${name}_cmn
    if [ -f data/$name/vad.scp ]; then
      cp data/$name/vad.scp data/${name}_cmn/
    fi
    if [ -f data/$name/segments ]; then
      cp data/$name/segments data/${name}_cmn/
    fi
    utils/fix_data_dir.sh data/${name}_cmn
  done

  echo "0.01" > data/rtve_2018${suffix}_train_cmn/frame_shift
  echo "0.01" > data/rtve_2020${suffix}_train_cmn/frame_shift

  for name in rtve_2018${suffix}_train rtve_2020${suffix}_train; do
    rm -rf data/${name}_cmn_segmented
    diarization/vad_to_segments.sh \
      --nj 40 \
      --cmd "$train_cmd" \
      data/${name}_cmn \
      data/${name}_cmn_segmented
  done
fi

# Train UBM and i-vector extractor
if [ $stage -le 2 ]; then
  utils/combine_data.sh data/train${suffix}_ivector  data/rtve_2018${suffix}_train_cmn_segmented data/rtve_2020${suffix}_train_cmn_segmented

  # Reduce the amount of training data for the UBM.
  utils/subset_data_dir.sh data/train${suffix}_ivector 3400 data/train${suffix}_ivector_3.4k
  #utils/subset_data_dir.sh data/train${suffix}_ivector 32000 data/train${suffix}_ivector_32k

  # Train UBM and i-vector extractor.
  sid/train_diag_ubm.sh \
    --cmd "$train_cmd --mem 20G" --nj 9 --num-threads 8 --delta-order 1 --apply-cmn false \
    data/train${suffix}_ivector_3.4k $num_components \
    exp/${suffix}_diag_ubm_$num_components

  sid/train_full_ubm.sh --nj 9 --remove-low-count-gaussians false --cmd "$train_cmd --mem 25G" --apply-cmn false \
    data/train${suffix}_ivector exp/${suffix}_diag_ubm_$num_components \
    exp/${suffix}_full_ubm_$num_components

  sid/train_ivector_extractor.sh \
    --cmd "$train_cmd --mem 35G" --nj 9 --ivector-dim $ivector_dim --num-iters 5 --apply-cmn false \
    exp/${suffix}_full_ubm_$num_components/final.ubm data/train${suffix}_ivector \
    exp/${suffix}_extractor_c${num_components}_i${ivector_dim}
fi

