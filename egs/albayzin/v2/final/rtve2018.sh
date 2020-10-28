#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e

suffix=_EXP032
rtve_root=/export/corpora5/RTVE

nnet_dir=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/exp/sre19-av-models/xvector_nnet_5a.1.vcc.v2

stage=3

if [ $stage -le 0 ]; then
  # <speaker-overlap> <speaker-rename>
  local/make_rtve_2018_dev2_2.sh train $rtve_root/RTVE2018DB/dev2 data/rtve_2018_dev2${suffix}_train false true
  local/make_rtve_2018_test_sd.sh train $rtve_root/RTVE2018DB/test data/rtve_2018_test_sd${suffix}_train false true

  utils/combine_data.sh data/rtve_2018${suffix}_train data/rtve_2018_dev2${suffix}_train data/rtve_2018_test_sd${suffix}_train
  echo "Training data directory: data/rtve_2018${suffix}_train"
fi

if [ $stage -le 1 ]; then
  for name in rtve_2018${suffix}_train; do
    data_dir=data/$name
    steps/make_mfcc.sh \
      --cmd "$train_cmd" \
      --mfcc-config exp/0012_sad_v1/conf/mfcc_hires.conf \
      --nj 40 \
      --write-utt2num-frames true \
      --write-utt2dur true \
      $data_dir

    exp/0012_sad_v1/local/segmentation/detect_speech_activity.sh \
      --cmd "$train_cmd" \
      --nj 40 \
      $data_dir \
      exp/0012_sad_v1/exp/segmentation_1a/tdnn_stats_sad_1a \
      $data_dir/mfcc_hires \
      $data_dir \
      $data_dir

    utils/fix_data_dir.sh $data_dir
  done
fi

if [ $stage -le 2 ]; then
  data_dir=data/rtve_2018${suffix}_train_seg
  output_dir=exp/xvectors_rtve_2018${suffix}_train

  rm -rf $output_dir
  diarization/nnet3/xvector/extract_xvectors.sh \
    --cmd "$train_cmd --mem 5G" --nj 40 --window 1.5 --period 0.25 --apply-cmn false --min-segment 0.5 \
    $nnet_dir \
    $data_dir \
    $output_dir
fi

# Train PLDA models
if [ $stage -le 3 ]; then
  # Train a PLDA model on VoxCeleb, using DIHARD 2018 development set to whiten.
  data_dir=exp/xvectors_rtve_2018${suffix}_train
  ls $data_dir
  "queue.pl" $data_dir/log/plda.log \
    ivector-compute-plda ark:$data_dir/spk2utt \
      "ark:ivector-subtract-global-mean \
      scp:$data_dir/xvector.scp ark:- \
      | transform-vec $data_dir/transform.mat ark:- ark:- \
      | ivector-normalize-length ark:- ark:- |" \
    $data_dir/plda || exit 1;
fi

exit 0

# Perform PLDA scoring
if [ $stage -le 13 ]; then
  # Perform PLDA scoring on all pairs of segments for each recording.
  diarization/nnet3/xvector/score_plda.sh --cmd "$train_cmd --mem 4G" \
    --nj 20 $nnet_dir/xvectors_rtve_2018_eval $nnet_dir/xvectors_rtve_2018_eval \
    $nnet_dir/xvectors_rtve_2018_eval/plda_scores

  diarization/nnet3/xvector/score_plda.sh --cmd "$train_cmd --mem 4G" \
    --nj 20 $nnet_dir/xvectors_rtve_2018_eval $nnet_dir/xvectors_rtve_2020_eval \
    $nnet_dir/xvectors_rtve_2020_eval/plda_scores
fi

# Cluster the PLDA scores using a stopping threshold.
if [ $stage -le 14 ]; then
  # First, we find the threshold that minimizes the DER on DIHARD 2018 development set.
  mkdir -p $nnet_dir/tuning
  echo "Tuning clustering threshold for DIHARD 2018 development set"
  best_der=100
  best_threshold=0

  # The threshold is in terms of the log likelihood ratio provided by the
  # PLDA scores.  In a perfectly calibrated system, the threshold is 0.
  # In the following loop, we evaluate DER performance on DIHARD 2018 development
  # set using some reasonable thresholds for a well-calibrated system.
  for threshold in -0.5 -0.4 -0.3 -0.2 -0.1 -0.05 0 0.05 0.1 0.2 0.3 0.4 0.5; do
    local/diarization_cluster.sh --cmd "$train_cmd --mem 60G" --nj 20 \
      --threshold $threshold --rttm-channel 1 $nnet_dir/xvectors_rtve_2018_eval/plda_scores \
      $nnet_dir/xvectors_rtve_2018_eval/plda_scores_t$threshold

    md-eval.pl -r data/rtve_2018_eval/ref.rttm \
     -s $nnet_dir/xvectors_rtve_2018_eval/plda_scores_t$threshold/rttm \
     2> $nnet_dir/tuning/rtve_2018_eval_t${threshold}.log \
     > $nnet_dir/tuning/rtve_2018_eval_t${threshold}

    der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
      $nnet_dir/tuning/rtve_2018_eval_t${threshold})
    if [ $(perl -e "print ($der < $best_der ? 1 : 0);") -eq 1 ]; then
      best_der=$der
      best_threshold=$threshold
    fi
  done
  echo "$best_threshold" > $nnet_dir/tuning/rtve_2018_eval_best

  local/diarization_cluster.sh --cmd "$train_cmd --mem 60G" --nj 20 \
    --threshold $(cat $nnet_dir/tuning/rtve_2018_eval_best) --rttm-channel 1 \
    $nnet_dir/xvectors_rtve_2018_eval/plda_scores $nnet_dir/xvectors_rtve_2018_eval/plda_scores

  # Cluster DIHARD 2018 evaluation set using the best threshold found for the DIHARD
  # 2018 development set. The DIHARD 2018 development set is used as the validation
  # set to tune the parameters.
  local/diarization_cluster.sh --cmd "$train_cmd --mem 60G" --nj 20 \
    --threshold $(cat $nnet_dir/tuning/rtve_2018_eval_best) --rttm-channel 1 \
    $nnet_dir/xvectors_rtve_2020_eval/plda_scores $nnet_dir/xvectors_rtve_2020_eval/plda_scores

  mkdir -p $nnet_dir/results
  # Compute the DER on the DIHARD 2018 evaluation set. We use the official metrics of
  # the DIHARD challenge. The DER is calculated with no unscored collars and including
  # overlapping speech.
  md-eval.pl -r data/rtve_2020_eval/ref.rttm \
    -s $nnet_dir/xvectors_rtve_2020_eval/plda_scores/rttm 2> $nnet_dir/results/threshold.log \
    > $nnet_dir/results/DER_threshold.txt
  der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
    $nnet_dir/results/DER_threshold.txt)
  # Using supervised calibration, DER: 26.30%
  echo "Using supervised calibration, DER: $der%"
fi

