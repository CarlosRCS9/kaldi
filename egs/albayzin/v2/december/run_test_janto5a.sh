#!/usr/bin/env bash
# Copyright 2021 Carlos Castillo
#
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e
mfccdir=`pwd`/mfcc
vaddir=`pwd`/mfcc

suffix=_EXP000
nnet_dir=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/exp/sre19-av-models/xvector_nnet_5a.1.vcc.v2
plda_dir=$nnet_dir/xvectors_rtve_2018${suffix}_train
rtve_root=/export/corpora5/RTVE
rttm_filepath=december/test/RTVE2020-SDreference.rttm

nj=54
stage=2

if [ $stage -le 0 ]; then
  rm -rf data/rtve_2020_test_sd${suffix}
  local/make_rtve_2020_test_sd_2.sh oracle $rtve_root/RTVE2020DB/test/audio/SD $rttm_filepath data/rtve_2020_test_sd${suffix} true false
fi

if [ $stage -le 1 ]; then
  # Make MFCCs for each dataset.
  for name in rtve_2020_test_sd${suffix}; do
    steps/make_mfcc.sh \
      --mfcc-config exp/sre19-av-models/mfcc_16k.conf \
      --nj $nj \
      --cmd "$train_cmd --max-jobs-run 20" \
      --write-utt2num-frames true \
      --write-utt2dur true \
      data/$name
    utils/fix_data_dir.sh data/$name
  done

  for name in rtve_2020_test_sd${suffix}; do
    python3 scripts/make_oracle_vad.py data/$name
  done

  # Although this is somewhat wasteful in terms of disk space, for diarization
  # it ends up being preferable to performing the CMN in memory.  If the CMN
  # were performed in memory (e.g., we used --apply-cmn true in
  # diarization/nnet3/xvector/extract_xvectors.sh) it would need to be
  # performed after the subsegmentation, which leads to poorer results.
  for name in rtve_2020_test_sd${suffix}; do
    rm -rf data/${name}_cmn
    local/nnet3/xvector/prepare_feats.sh \
      --nj $nj \
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

  echo "0.01" > data/rtve_2020_test_sd${suffix}_cmn/frame_shift
  # Create segments to extract x-vectors from for data.
  # The segments are created using an energy-based speech activity
  # detection (SAD) system, but this is not necessary.  You can replace
  # this with segments computed from your favorite SAD.
  for name in rtve_2020_test_sd${suffix}; do
    rm -rf data/${name}_cmn_segmented
    diarization/vad_to_segments.sh \
      --nj $nj \
      --cmd "$train_cmd" \
      data/${name}_cmn \
      data/${name}_cmn_segmented
  done
fi

if [ $stage -le 2 ]; then
  for name in rtve_2020_test_sd${suffix}; do
    rm -rf $nnet_dir/xvectors_${name}
    diarization/nnet3/xvector/extract_xvectors.sh \
      --cmd "$train_cmd --mem 5G" --nj $nj --window 1.5 --period 0.25 --apply-cmn false --min-segment 0.5 \
      $nnet_dir \
      data/${name}_cmn_segmented \
      $nnet_dir/xvectors_${name}
  done
fi

echo "done"
exit 0

# Train PLDA models
if [ $stage -le 3 ]; then
  # Train a PLDA model on VoxCeleb, using DIHARD 2018 development set to whiten.
  "queue.pl" $nnet_dir/xvectors_rtve_2018${suffix}_train/log/plda.log \
    ivector-compute-plda ark:$nnet_dir/xvectors_rtve_2018${suffix}_train/spk2utt \
      "ark:ivector-subtract-global-mean \
      scp:$nnet_dir/xvectors_rtve_2018${suffix}_train/xvector.scp ark:- \
      | transform-vec $nnet_dir/xvectors_rtve_2018${suffix}_train/transform.mat ark:- ark:- \
      | ivector-normalize-length ark:- ark:- |" \
    $nnet_dir/xvectors_rtve_2018${suffix}_train/plda || exit 1;
fi

# Perform PLDA scoring
if [ $stage -le 4 ]; then
  # Perform PLDA scoring on all pairs of segments for each recording.
  for name in rtve_2018${suffix} rtve_2020${suffix}; do
    diarization/nnet3/xvector/score_plda.sh \
      --cmd "$train_cmd --mem 4G" --nj 9 \
      $plda_dir \
      $nnet_dir/xvectors_${name} \
      $nnet_dir/xvectors_${name}/plda_scores
  done
fi

# Cluster the PLDA scores using a stopping threshold.
if [ $stage -le 5 ]; then
  # First, we find the threshold that minimizes the DER on RTVE 2018 development set.
  mkdir -p $nnet_dir/tuning${suffix}
  echo "Tuning clustering threshold for RTVE 2018 development set"
  best_der=100
  best_threshold=0

  # The threshold is in terms of the log likelihood ratio provided by the
  # PLDA scores.  In a perfectly calibrated system, the threshold is 0.
  # In the following loop, we evaluate DER performance on DIHARD 2018 development
  # set using some reasonable thresholds for a well-calibrated system.
  for threshold in -0.5 -0.4 -0.3 -0.2 -0.1 -0.05 0 0.05 0.1 0.2 0.3 0.4 0.5; do
    local/diarization_cluster.sh \
      --cmd "$train_cmd --mem 60G" --nj 9 --threshold $threshold --rttm-channel 1 \
      $nnet_dir/xvectors_rtve_2018${suffix}/plda_scores \
      $nnet_dir/xvectors_rtve_2018${suffix}/plda_scores_t${threshold}

    md-eval.pl -r data/rtve_2018${suffix}/ref.rttm \
      -s $nnet_dir/xvectors_rtve_2018${suffix}/plda_scores_t${threshold}/rttm \
      2> $nnet_dir/tuning${suffix}/rtve_2018${suffix}_t${threshold}.log \
      > $nnet_dir/tuning${suffix}/rtve_2018${suffix}_t${threshold}

  der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
      $nnet_dir/tuning${suffix}/rtve_2018${suffix}_t${threshold})
    if [ $(perl -e "print ($der < $best_der ? 1 : 0);") -eq 1 ]; then
      best_der=$der
      best_threshold=$threshold
    fi
  done
  echo "$best_threshold" > $nnet_dir/tuning${suffix}/rtve_2018${suffix}_best

  local/diarization_cluster.sh \
    --cmd "$train_cmd --mem 60G" --nj 9 --threshold $(cat $nnet_dir/tuning${suffix}/rtve_2018${suffix}_best) --rttm-channel 1 \
    $nnet_dir/xvectors_rtve_2018${suffix}/plda_scores \
    $nnet_dir/xvectors_rtve_2018${suffix}/plda_scores

  # Cluster DIHARD 2018 evaluation set using the best threshold found for the DIHARD
  # 2018 development set. The DIHARD 2018 development set is used as the validation
  # set to tune the parameters.
  local/diarization_cluster.sh \
    --cmd "$train_cmd --mem 60G" --nj 9 --threshold $(cat $nnet_dir/tuning${suffix}/rtve_2018${suffix}_best) --rttm-channel 1 \
    $nnet_dir/xvectors_rtve_2020${suffix}/plda_scores \
    $nnet_dir/xvectors_rtve_2020${suffix}/plda_scores

  mkdir -p $nnet_dir/results${suffix}
  # Compute the DER on the DIHARD 2018 evaluation set. We use the official metrics of
  # the DIHARD challenge. The DER is calculated with no unscored collars and including
  # overlapping speech.
  md-eval.pl -r data/rtve_2020${suffix}/ref.rttm \
    -s $nnet_dir/xvectors_rtve_2020${suffix}/plda_scores/rttm 2> $nnet_dir/results${suffix}/threshold.log \
    > $nnet_dir/results${suffix}/DER_threshold.txt
  der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
    $nnet_dir/results${suffix}/DER_threshold.txt)
  # Using supervised calibration, DER: 26.30%
  echo "Using supervised calibration, DER: $der%"
fi

# Cluster the PLDA scores using the oracle number of speakers
if [ $stage -le 6 ]; then
  # In this section, we show how to do the clustering if the number of speakers
  # (and therefore, the number of clusters) per recording is known in advance.
  for name in rtve_2018${suffix} rtve_2020${suffix}; do
    local/diarization_cluster.sh \
      --cmd "$train_cmd --mem 60G" --nj 9 --reco2num-spk data/$name/reco2num_spk --rttm-channel 1 \
      $nnet_dir/xvectors_${name}/plda_scores \
      $nnet_dir/xvectors_${name}/plda_scores_num_spk

    mkdir -p $nnet_dir/results_${name}
    # Now combine the results for callhome1 and callhome2 and evaluate it together.
    md-eval.pl -r data/$name/ref.rttm \
      -s $nnet_dir/xvectors_${name}/plda_scores_num_spk/rttm 2> $nnet_dir/results_${name}/num_spk.log \
      > $nnet_dir/results_${name}/DER_num_spk.txt
    der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
      $nnet_dir/results_${name}/DER_num_spk.txt)
    # Using the oracle number of speakers, DER: 7.12%
    # Compare to 8.69% in ../v1/run.sh
    echo "Using the oracle number of speakers, DER: $der%"
  done
fi

