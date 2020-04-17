#!/bin/bash
# Copyright 2020 Carlos Castillo
# Apache 2.0.

datadir=data2
augmentdir=/export/c03/carloscastillo/data/augmented
stage=4

if [ $stage -le 0 ]; then
  for name in callhome1 callhome2 dihard_2019_dev dihard_2019_eval; do
    cat $datadir/$name/ref.rttm | python3 scripts/rttm_explicit_overlaps.py \
      --min-segment=0.1 \
      --output-mode=json \
      > $datadir/$name/explicit_overlaps.json
  done
fi

if [ $stage -le 1 ]; then
  for name in callhome1 callhome2 dihard_2019_dev dihard_2019_eval; do
    mkdir -p $augmentdir/$name
    cat $datadir/$name/explicit_overlaps.json | python3 scripts/json_augment_audio.py \
      $datadir/$name/wav.scp \
      $augmentdir/$name/
  done
fi

if [ $stage -le 2 ]; then
  for name in callhome1 callhome2 dihard_2019_dev dihard_2019_eval; do
    cat $augmentdir/$name/segments_augmented.json | python3 scripts/json_to_rttm.py \
      --overlap-speaker=false \
      > $augmentdir/$name/segments_augmented.rttm
  done
fi

if [ $stage -le 3 ]; then
  for name in callhome1 callhome2 dihard_2019_dev dihard_2019_eval; do
    cat $augmentdir/$name/segments_augmented.json | python3 scripts/split_segments.py \
      json \
      --length=1.0 \
      --overlap=0.5 \
      --min-segment=0.5 \
      > $augmentdir/$name/segments_augmented_1.0_0.5.json
  done
fi

if [ $stage -le 4 ]; then
  for name in dihard_2019_dev dihard_2019_eval; do
    mkdir -p $augmentdir/$name/json
    cat $augmentdir/$name/segments_augmented_1.0_0.5.json | python3 scripts/extract_features.py \
    json \
    $augmentdir/$name \
    $augmentdir/$name
  done
fi

