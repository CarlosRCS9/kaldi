#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e

suffix=_EXP021
voxceleb1_root=/export/corpora5/VoxCeleb1_v1
voxceleb2_root=/export/corpora5/VoxCeleb2
musan_root=/export/corpora5/JHU/musan
nnet_dir=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/exp/sre19-av-models/xvector_nnet_4a.1.vcc
plda_dir=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/exp/sre19-av-models/xvector_nnet_4a.1.vcc/xvectors_voxceleb${suffix}
mfcc_conf=exp/sre19-av-models/mfcc_16k.conf

stage=0

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

# In this section, we augment the training data with reverberation,
# noise, music, and babble, and combine it with the clean data.
if [ $stage -le 2 ]; then
  dir=data/voxceleb${suffix}
  frame_shift=0.01
  awk -v frame_shift=$frame_shift '{print $1, $2*frame_shift;}' $dir/utt2num_frames > $dir/reco2dur

  if [ ! -d "RIRS_NOISES" ]; then
    # Download the package that includes the real RIRs, simulated RIRs, isotropic noises and point-source noises
    wget --no-check-certificate http://www.openslr.org/resources/28/rirs_noises.zip
    unzip rirs_noises.zip
  fi

  # Make a version with reverberated speech
  rvb_opts=()
  rvb_opts+=(--rir-set-parameters "0.5, RIRS_NOISES/simulated_rirs/smallroom/rir_list")
  rvb_opts+=(--rir-set-parameters "0.5, RIRS_NOISES/simulated_rirs/mediumroom/rir_list")

  # Make a reverberated version of the training data.  Note that we don't add any
  # additive noise here.
  steps/data/reverberate_data_dir.py \
    "${rvb_opts[@]}" \
    --speech-rvb-probability 1 \
    --pointsource-noise-addition-probability 0 \
    --isotropic-noise-addition-probability 0 \
    --num-replications 1 \
    --source-sampling-rate 16000 \
    $dir ${dir}_reverb
  cp $dir/vad.scp ${dir}_reverb/
  utils/copy_data_dir.sh --utt-suffix "-reverb" ${dir}_reverb ${dir}_reverb.new
  rm -rf ${dir}_reverb
  mv ${dir}_reverb.new ${dir}_reverb

  # Prepare the MUSAN corpus, which consists of music, speech, and noise
  # suitable for augmentation.
  steps/data/make_musan.sh --sampling-rate 16000 $musan_root data

  # Get the duration of the MUSAN recordings.  This will be used by the
  # script augment_data_dir.py.
  for name in speech noise music; do
    utils/data/get_utt2dur.sh data/musan_${name}
    mv data/musan_${name}/utt2dur data/musan_${name}/reco2dur
  done

  # Augment with musan_noise
  steps/data/augment_data_dir.py --utt-suffix "noise" --fg-interval 1 --fg-snrs "15:10:5:0" --fg-noise-dir "data/musan_noise" $dir ${dir}_noise
  # Augment with musan_music
  steps/data/augment_data_dir.py --utt-suffix "music" --bg-snrs "15:10:8:5" --num-bg-noises "1" --bg-noise-dir "data/musan_music" $dir ${dir}_music
  # Augment with musan_speech
  steps/data/augment_data_dir.py --utt-suffix "babble" --bg-snrs "20:17:15:13" --num-bg-noises "3:4:5:6:7" --bg-noise-dir "data/musan_speech" $dir ${dir}_babble

  # Combine reverb, noise, music, and babble into one directory.
  utils/combine_data.sh ${dir}_aug ${dir}_reverb ${dir}_noise ${dir}_music ${dir}_babble
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
if [ $stage -le 12 ]; then
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

