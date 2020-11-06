#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0

. ./cmd.sh
. ./path.sh
set -e

mfcc_conf=../../callhome_diarization/v1/conf/mfcc.conf

stage=2
nj=50

if [ $stage -le 0 ]; then
  local/make_callhome.sh /export/corpora5/LDC/LDC2001S97/ data
fi

if [ $stage -le 1 ]; then
  for name in callhome1 callhome2; do
    data_dir=data/$name
    recording_ids=$(cat $data_dir/wav.scp | awk '{print $1}')
    recording_ids_grep=$(echo $recording_ids | sed --expression='s/ /\\|/g')
    grep "$recording_ids_grep" data/callhome/fullref.rttm > $data_dir/ref.rttm
  done

  for name in callhome1 callhome2; do
    data_dir=data/$name
    output_dir=data/${name}_oracle
    
    rm -rf $output_dir
    mkdir -p $output_dir

    cp $data_dir/{reco2num_spk,ref.rttm,wav.scp} $output_dir/

    cat $output_dir/wav.scp | awk '{print $1" "$1}' > $output_dir/utt2spk
    cp $output_dir/utt2spk $output_dir/spk2utt

    steps/make_mfcc.sh \
      --cmd "$train_cmd" \
      --mfcc-config $mfcc_conf \
      --nj $nj \
      --write-utt2num-frames true \
      --write-utt2dur true \
      $output_dir
  done
fi

if [ $stage -le 2 ]; then
  for name in callhome1 callhome2; do
    data_dir=data/${name}_oracle
    output_dir=data/${name}_oracle_segmented
    python3 python/rttm_to_vad.py $data_dir
    diarization/vad_to_segments.sh \
      --nj $nj \
      --cmd "$train_cmd" \
      --segmentation-opts '--silence-proportion 0.011' \
      $data_dir \
      $output_dir
  done
fi

