#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e

suffix=_EXP010
rtve_root=/export/corpora5/RTVE

stage=2

if [ $stage -le 0 ]; then
  # <speaker-overlap> <speaker-rename>
  local/make_rtve_2018_dev2_2.sh oracle $rtve_root/RTVE2018DB/dev2 data/rtve_2018${suffix}_oracle true true
  local/make_rtve_2020_dev_2.sh oracle $rtve_root/RTVE2020DB/dev data/rtve_2020${suffix}_oracle true true
fi

if [ $stage -le 1 ]; then
  for name in rtve_2018${suffix} rtve_2020${suffix}; do
    steps/make_mfcc.sh \
      --mfcc-config exp/0012_sad_v1/conf/mfcc_hires.conf \
      --nj 9 \
      --cmd "$train_cmd --max-jobs-run 20" \
      --write-utt2num-frames true \
      --write-utt2dur true \
      data/${name}_oracle
    utils/fix_data_dir.sh data/${name}_oracle
  done

  for name in rtve_2018${suffix} rtve_2020${suffix}; do
    python3 scripts/make_oracle_vad.py data/${name}_oracle
    copy-vector \
      scp:data/${name}_oracle/vad.scp \
      ark,scp:data/${name}_oracle/vad.ark,data/${name}_oracle/vad_tmp.scp
    mv data/${name}_oracle/vad_tmp.scp data/${name}_oracle/vad.scp
  done

  #for name in rtve_2018${suffix} rtve_2020${suffix}; do
  #  rm -rf data/${name}_oracle_cmn
  #  local/nnet3/xvector/prepare_feats.sh \
  #    --nj 9 \
  #    --cmd "$train_cmd" \
  #    data/${name}_oracle \
  #    data/${name}_oracle_cmn \
  #    exp/${name}_oracle_cmn
  #  if [ -f data/${name}_oracle/vad.scp ]; then
  #    cp data/${name}_oracle/vad.scp data/${name}_oracle_cmn/
  #  fi
  #  if [ -f data/${name}_oracle/segments ]; then
  #    cp data/${name}_oracle/segments data/${name}_oracle_cmn/
  #  fi
  #  utils/fix_data_dir.sh data/${name}_oracle_cmn
  #done

  #for name in rtve_2018${suffix} rtve_2020${suffix}; do
  #  echo "0.01" > data/${name}_oracle/frame_shift
  #done

  for name in rtve_2018${suffix} rtve_2020${suffix}; do
    rm -rf data/${name}_oracle_segmented
    cp -r data/${name}_oracle data/${name}_oracle_segmented
    python3 scripts/vad_to_segments.py data/${name}_oracle_segmented > data/${name}_oracle_segmented/segments
    #diarization/vad_to_segments.sh \
    #  --nj 9 \
    #  --cmd "$train_cmd" \
    #  data/${name}_oracle \
    #  data/${name}_oracle_segmented
  done
fi

if [ $stage -le 2 ]; then
  for name in rtve_2018${suffix} rtve_2020${suffix}; do
    python3 scripts/oracle_clustering.py data/${name}_oracle/ref.rttm data/${name}_oracle_segmented/segments > data/${name}_oracle_segmented/rttm

    md-eval.pl \
      -r data/${name}_oracle/ref.rttm \
      -s data/${name}_oracle_segmented/rttm \
      2> data/${name}_oracle_segmented/threshold.log \
      > data/${name}_oracle_segmented/DER_threshold.txt

    der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
      data/${name}_oracle_segmented/DER_threshold.txt)

    echo "data/${name}_oracle_segmented/DER_threshold.txt DER: $der%"
  done
fi
