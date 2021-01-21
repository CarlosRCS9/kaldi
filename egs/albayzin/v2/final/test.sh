#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e

suffix=_EXP028
rtve_root=/export/corpora5/RTVE
nnet_dir=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/exp/sre19-av-models/xvector_nnet_5a.1.vcc.v2
plda_dir=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/exp/sre19-av-models/xvector_nnet_5a.1.vcc.v2/xvectors_rtve_2018_2020_janto5a_train
mfcc_conf=exp/sre19-av-models/mfcc_16k.conf

stage=5

if [ $stage -le 0 ]; then
  local/make_rtve_2020_test_sd.sh $rtve_root/RTVE2020DB/test/audio/SD data/rtve_2020_test_sd${suffix}
fi

if [ $stage -le 1 ]; then
  for name in rtve_2020_test_sd${suffix}; do
    data_dir=data/$name
    steps/make_mfcc.sh \
      --cmd "$train_cmd --max-jobs-run 20" \
      --mfcc-config exp/0012_sad_v1/conf/mfcc_hires.conf \
      --nj 54 \
      --write-utt2num-frames true \
      --write-utt2dur true \
      $data_dir

    utils/fix_data_dir.sh $data_dir
  done
fi

if [ $stage -le 2 ]; then
  for name in rtve_2020_test_sd${suffix}; do
    data_dir=data/$name
    exp/0012_sad_v1/local/segmentation/detect_speech_activity.sh \
      --cmd "$train_cmd" \
      --nj 54 \
      $data_dir \
      exp/0012_sad_v1/exp/segmentation_1a/tdnn_stats_sad_1a \
      $data_dir/mfcc_hires \
      $data_dir \
      $data_dir

    utils/fix_data_dir.sh $data_dir
  done
fi

if [ $stage -le 3 ]; then
  local/make_rtve_2020_test_sd.sh $rtve_root/RTVE2020DB/test/audio/SD data/rtve_2020_test_sd${suffix}_eval
fi

if [ $stage -le 4 ]; then
  for name in rtve_2020_test_sd${suffix}; do
    data_dir=data/${name}_seg
    output_dir=data/${name}_eval
    if [ -f $data_dir/segments ]; then
      cp $data_dir/segments $output_dir/
      #cat $output_dir/segments | sed --expression='s/-/_/1' > $output_dir/segments_tmp
      #mv $output_dir/segments $output_dir/segments.bak
      #mv $output_dir/segments_tmp $output_dir/segments
    fi
    if [ -f $data_dir/utt2spk ]; then
      cp $data_dir/utt2spk $output_dir/
      #cat $output_dir/utt2spk | sed --expression='s/-/_/1' > $output_dir/utt2spk_tmp
      #mv $output_dir/utt2spk $output_dir/utt2spk.bak
      #mv $output_dir/utt2spk_tmp $output_dir/utt2spk
    fi
    if [ -f $data_dir/spk2utt ]; then
      cp $data_dir/spk2utt $output_dir/
      #cp $data_dir/spk2utt $output_dir/spk2utt.bak
      #cat cp $data_dir/utt2spk | utils/utt2spk_to_spk2utt.pl > $output_dir/spk2utt
    fi

    utils/fix_data_dir.sh $output_dir
  done

  for name in rtve_2020_test_sd${suffix}; do
    dir=data/${name}_eval
    steps/make_mfcc.sh \
      --cmd "$train_cmd --max-jobs-run 20" \
      --mfcc-config $mfcc_conf \
      --nj 54 \
      --write-utt2dur true \
      --write-utt2num-frames true \
      $dir

    utils/fix_data_dir.sh $dir
  done
fi

if [ $stage -le 5 ]; then
  for name in rtve_2020_test_sd${suffix}; do
    data_dir=data/${name}_eval
    output_dir=$nnet_dir/xvectors_${name}
    rm -rf $output_dir
    diarization/nnet3/xvector/extract_xvectors.sh \
      --cmd "$train_cmd --mem 5G" --nj 54 --window 1.5 --period 0.25 --apply-cmn false --min-segment 0.5 \
      $nnet_dir \
      $data_dir \
      $output_dir
  done
fi

if [ $stage -le 6 ]; then
  # Perform PLDA scoring on all pairs of segments for each recording.
  for name in rtve_2020_test_sd${suffix}; do
    data_dir=$nnet_dir/xvectors_${name}
    output_dir=$nnet_dir/xvectors_${name}/plda_scores
    diarization/nnet3/xvector/score_plda.sh \
      --cmd "$train_cmd --mem 4G" --nj 54 \
      $plda_dir \
      $data_dir \
      $output_dir
  done
fi

if [ $stage -le 7 ]; then
  for name in rtve_2020_test_sd${suffix}; do
    data_dir=$nnet_dir/xvectors_${name}/plda_scores
    output_dir=$nnet_dir/xvectors_${name}/plda_scores
    local/diarization_cluster.sh \
      --cmd "$train_cmd --mem 60G" --nj 54 --threshold 0.05 --rttm-channel 1 \
      $data_dir \
      $output_dir
    echo "rttm on $output_dir"
  done
fi
