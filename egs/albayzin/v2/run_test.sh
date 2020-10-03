#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e
mfccdir=`pwd`/mfcc
vaddir=`pwd`/mfcc

nnet_dir=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/exp/xvector_nnet_1a
plda_dir=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/exp/xvector_nnet_1a/xvectors_rtve_2018_eval
rtve_root=/export/corpora5/RTVE
suffix=_2020_test

stage=0

if [ $stage -le 0 ]; then
  # Prepare the RTVE 2018 development set for evaluation.
  local/make_rtve_2018_dev2.sh oracle $rtve_root/RTVE2018DB/dev2 data/rtve_2018${suffix} false
  local/make_rtve_2020_dev.sh oracle $rtve_root/RTVE2020DB/dev data/rtve_2020${suffix} false
  local/make_rtve_2020_test_diarization.sh $rtve_root/RTVE2020DB/test/audio/SD data/rtve_2020_test${suffix}
fi

if [ $stage -le 1 ]; then
  # Make MFCCs for each dataset.
  for name in rtve_2018${suffix} rtve_2020${suffix} rtve_2020_test${suffix}; do
    steps/make_mfcc.sh \
      --mfcc-config conf/mfcc.conf \
      --nj 9 \
      --cmd "$train_cmd --max-jobs-run 20" \
      --write-utt2num-frames true \
      --write-utt2dur true \
      data/$name
    utils/fix_data_dir.sh data/$name
  done

  for name in rtve_2018${suffix} rtve_2020${suffix}; do
    python3 scripts/make_oracle_vad.py data/$name
  done
  # Compute the energy-based VAD for each dataset.
  for name in rtve_2020_test${suffix}; do
   sid/compute_vad_decision.sh \
     --nj 9 \
     --cmd "$train_cmd" \
     data/$name \
     data/$name/make_vad \
     data/$name/data
    utils/fix_data_dir.sh data/$name
  done

  # Although this is somewhat wasteful in terms of disk space, for diarization
  # it ends up being preferable to performing the CMN in memory.  If the CMN
  # were performed in memory (e.g., we used --apply-cmn true in
  # diarization/nnet3/xvector/extract_xvectors.sh) it would need to be
  # performed after the subsegmentation, which leads to poorer results.
  for name in rtve_2018${suffix} rtve_2020${suffix} rtve_2020_test${suffix}; do
    rm -rf data/${name}_cmn
    local/nnet3/xvector/prepare_feats.sh \
      --nj 9 \
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

  echo "0.01" > data/rtve_2018${suffix}_cmn/frame_shift
  echo "0.01" > data/rtve_2020${suffix}_cmn/frame_shift
  echo "0.01" > data/rtve_2020_test${suffix}_cmn/frame_shift
  # Create segments to extract x-vectors from for data.
  # The segments are created using an energy-based speech activity
  # detection (SAD) system, but this is not necessary.  You can replace
  # this with segments computed from your favorite SAD.
  for name in rtve_2018${suffix} rtve_2020${suffix} rtve_2020_test${suffix}; do
    rm -rf data/${name}_cmn_segmented
    diarization/vad_to_segments.sh \
      --nj 9 \
      --cmd "$train_cmd" \
      data/${name}_cmn \
      data/${name}_cmn_segmented
  done
fi

if [ $stage -le 2 ]; then
  # Extract x-vectors for RTVE 2018 and 2020.
  for name in rtve_2018${suffix} rtve_2020${suffix} rtve_2020_test${suffix}; do
    rm -rf $nnet_dir/xvectors_${name}
    diarization/nnet3/xvector/extract_xvectors.sh \
      --cmd "$train_cmd --mem 5G" --nj 9 --window 1.5 --period 0.25 --apply-cmn false --min-segment 0.5 \
      $nnet_dir \
      data/${name}_cmn_segmented \
      $nnet_dir/xvectors_${name}
  done
fi

# Perform PLDA scoring
if [ $stage -le 3 ]; then
  # Perform PLDA scoring on all pairs of segments for each recording.
  for name in rtve_2018${suffix} rtve_2020${suffix} rtve_2020_test${suffix}; do
    diarization/nnet3/xvector/score_plda.sh \
      --cmd "$train_cmd --mem 4G" --nj 9 \
      $plda_dir \
      $nnet_dir/xvectors_${name} \
      $nnet_dir/xvectors_${name}/plda_scores
  done
fi

exit 1

# Cluster the PLDA scores using a stopping threshold.
if [ $stage -le 4 ]; then
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
if [ $stage -le 5 ]; then
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

