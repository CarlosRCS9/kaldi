#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e

suffix=_EXP020
voxceleb1_root=/export/corpora5/VoxCeleb1_v1
voxceleb2_root=/export/corpora5/VoxCeleb2
musan_root=/export/corpora5/JHU/musan
nnet_dir=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/exp/sre19-av-models/xvector_nnet_4a.1.vcc
plda_dir=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/exp/sre19-av-models/xvector_nnet_4a.1.vcc/xvectors_voxceleb${suffix}
mfcc_conf=exp/sre19-av-models/mfcc_16k.conf

stage=3

if [ $stage -le 0 ]; then
  local/make_voxceleb1.pl $voxceleb1_root data

  local/make_voxceleb2.pl $voxceleb2_root dev data/voxceleb2_train
  local/make_voxceleb2.pl $voxceleb2_root test data/voxceleb2_test

  utils/combine_data.sh data/voxceleb${suffix} data/voxceleb1_train data/voxceleb2_train data/voxceleb2_test data/voxceleb1_train
fi

if [ $stage -le 1 ]; then
  for name in voxceleb${suffix}; do
    dir=data/$name
    steps/make_mfcc.sh \
      --cmd "$train_cmd" \
      --mfcc-config $mfcc_conf \
      --nj 40 \
      --write-utt2dur true \
      --write-utt2num-frames true \
      $dir

    utils/fix_data_dir.sh $dir
  done

  for name in voxceleb${suffix}; do
    dir=data/$name
    sid/compute_vad_decision.sh \
      --cmd "$train_cmd" \
      --nj 40 \
      $dir \
      $dir/log \
      $dir/vad

    utils/fix_data_dir.sh $dir
  done

  for name in voxceleb${suffix}; do
    dir=data/$name
    local/nnet3/xvector/prepare_feats.sh \
      --cmd "$train_cmd" \
      --nj 40 \
      $dir \
      ${dir}_cmn \
      exp/${name}_cmn
    if [ -f $dir/vad.scp ]; then
      cp $dir/vad.scp ${dir}_cmn/
    fi
    if [ -f $dir/segments ]; then
      cp $dir/segments ${dir}_cmn/
    fi

    utils/fix_data_dir.sh ${dir}_cmn
  done

  for name in voxceleb${suffix}; do
    dir=data/${name}_cmn
    echo "0.01" > $dir/frame_shift

    diarization/vad_to_segments.sh \
      --cmd "$train_cmd" \
      --nj 40 \
      $dir \
      ${dir}_segmented
  done
fi

if [ $stage -le 2 ]; then
  # Reduce the amount of training data for the PLDA training.
  data_dir=data/voxceleb${suffix}_cmn_segmented_128k
  output_dir=$nnet_dir/xvectors_voxceleb${suffix}_cmn_segmented_128k
  utils/subset_data_dir.sh data/voxceleb${suffix}_cmn_segmented 128000 $data_dir
  # Extract x-vectors for the VoxCeleb, which is our PLDA training
  # data.  A long period is used here so that we don't compute too
  # many x-vectors for each recording.
  diarization/nnet3/xvector/extract_xvectors.sh --cmd "$train_cmd --mem 10G" \
    --nj 40 --window 3.0 --period 10.0 --min-segment 1.5 --apply-cmn false \
    --hard-min true $nnet_dir \
    $data_dir $output_dir
fi

# Train PLDA models
if [ $stage -le 3 ]; then
  data_dir=$nnet_dir/xvectors_voxceleb${suffix}_cmn_segmented_128k
  # Train a PLDA model on VoxCeleb, using DIHARD 2018 development set to whiten.
  "queue.pl" $data_dir/log/plda.log \
    ivector-compute-plda ark:$data_dir/spk2utt \
      "ark:ivector-subtract-global-mean \
      scp:$data_dir/xvector.scp ark:- \
      | transform-vec $data_dir/transform.mat ark:- ark:- \
      | ivector-normalize-length ark:- ark:- |" \
    $data_dir/plda || exit 1;
fi

