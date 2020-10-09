#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e
mfccdir=`pwd`/mfcc
vaddir=`pwd`/mfcc

nnet_dir=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/exp/sre19-av-models/xvector_nnet_4a.1.vcc
plda_dir=$nnet_dir/xvectors_rtve_2018_2020_janto4a_train
rtve_root=/export/corpora5/RTVE
suffix=_EXP005

num_components=2048
ivector_dim=128

stage=0

if [ $stage -le 0 ]; then
  local/make_rtve_2018_dev2.sh train $rtve_root/RTVE2018DB/dev2 data/rtve_2018${suffix} false true
  local/make_rtve_2020_dev.sh train $rtve_root/RTVE2020DB/dev data/rtve_2020${suffix} false true
  local/make_rtve_2020_test_diarization.sh $rtve_root/RTVE2020DB/test/audio/SD data/rtve_2020_test${suffix}
fi

if [ $stage -le 1 ]; then
  for name in rtve_2018${suffix} rtve_2020${suffix} rtve_2020_test${suffix}; do
    steps/make_mfcc.sh \
      --mfcc-config exp/0012_sad_v1/conf/mfcc_hires.conf \
      --nj 9 \
      --cmd "$train_cmd --max-jobs-run 20" \
      --write-utt2num-frames true \
      --write-utt2dur true \
      data/$name
    utils/fix_data_dir.sh data/$name
  done

  for name in rtve_2018${suffix} rtve_2020${suffix} rtve_2020_test${suffix}; do
    exp/0012_sad_v1/local/segmentation/detect_speech_activity.sh \
      --cmd "$train_cmd" --nj 9 \
      data/$name \
      exp/0012_sad_v1/exp/segmentation_1a/tdnn_stats_sad_1a \
      data/$name/mfcc_hires \
      data/$name \
      data/$name
  done

  # Although this is somewhat wasteful in terms of disk space, for diarization
  # it ends up being preferable to performing the CMN in memory.  If the CMN
  # were performed in memory (e.g., we used --apply-cmn true in
  # diarization/nnet3/xvector/extract_xvectors.sh) it would need to be
  # performed after the subsegmentation, which leads to poorer results.
  #for name in rtve_2018${suffix} rtve_2020${suffix} rtve_2020_test${suffix}; do
  #  rm -rf data/${name}_cmn
  #  local/nnet3/xvector/prepare_feats.sh \
  #    --nj 9 \
  #    --cmd "$train_cmd" \
  #    data/${name}_seg \
  #    data/${name}_cmn \
  #    exp/${name}_cmn
  #  if [ -f data/$name/vad.scp ]; then
  #    cp data/$name/vad.scp data/${name}_cmn/
  #  fi
  #  if [ -f data/$name/segments ]; then
  #    cp data/$name/segments data/${name}_cmn/
  #  fi
  #  utils/fix_data_dir.sh data/${name}_cmn
  #done
fi

# Train UBM and i-vector extractor
if [ $stage -le 2 ]; then
  utils/combine_data.sh data/train${suffix}_ivector data/rtve_2018${suffix} data/rtve_2020${suffix}
  python3 scripts/make_oracle_vad.py data/train${suffix}_ivector

  # Reduce the amount of training data for the UBM.
  #utils/subset_data_dir.sh data/train${suffix}_ivector 16000 data/train${suffix}_ivector_16k
  #utils/subset_data_dir.sh data/train${suffix}_ivector 32000 data/train${suffix}_ivector_32k

  # Train UBM and i-vector extractor.
  sid/train_diag_ubm.sh \
    --cmd "$train_cmd --mem 20G" --nj 9 --num-threads 8 --delta-order 1 --apply-cmn false \
    data/train${suffix}_ivector $num_components \
    exp/${suffix}_diag_ubm_$num_components

  sid/train_full_ubm.sh --nj 9 --remove-low-count-gaussians false --cmd "$train_cmd --mem 25G" --apply-cmn false \
    data/train${suffix}_ivector exp/${suffix}_diag_ubm_$num_components \
    exp/${suffix}_full_ubm_$num_components

  sid/train_ivector_extractor.sh \
    --cmd "$train_cmd --mem 35G" --nj 9 --ivector-dim $ivector_dim --num-iters 5 --apply-cmn false \
    exp/${suffix}_full_ubm_$num_components/final.ubm data/train${suffix}_ivector \
    exp/${suffix}_extractor_c${num_components}_i${ivector_dim}
fi

exit 1

# Perform xvectors extraction
if [ $stage -le 2 ]; then
  for name in rtve_2018${suffix} rtve_2020${suffix} rtve_2020_test${suffix}; do
    rm -rf $nnet_dir/xvectors_${name}
    diarization/nnet3/xvector/extract_xvectors.sh \
      --cmd "$train_cmd --mem 5G" --nj 9 --window 1.5 --period 0.25 --apply-cmn false --min-segment 0.5 \
      $nnet_dir \
      data/${name}_seg \
      $nnet_dir/xvectors_${name}
  done
fi

# Perform PLDA scoring
if [ $stage -le 3 ]; then
  for name in rtve_2018${suffix} rtve_2020${suffix} rtve_2020_test${suffix}; do
    diarization/nnet3/xvector/score_plda.sh \
      --cmd "$train_cmd --mem 4G" --nj 9 \
      $plda_dir \
      $nnet_dir/xvectors_${name} \
      $nnet_dir/xvectors_${name}/plda_scores
  done
fi

# Getting the best thresholds that minimizes the DER for each dataset
if [ $stage -le 4 ]; then
  for name in rtve_2018${suffix} rtve_2020${suffix}; do
    tuning_dir=$nnet_dir/tuning_$name
    rm -rf $tuning_dir
    mkdir -p $tuning_dir
    echo "Tuning clustering threshold for $name"
    best_der=100
    best_threshold=0

    for threshold in -0.5 -0.4 -0.3 -0.2 -0.1 -0.05 0 0.05 0.1 0.2 0.3 0.4 0.5; do
      local/diarization_cluster.sh \
        --cmd "$train_cmd --mem 60G" --nj 9 --threshold $threshold --rttm-channel 1 \
        $nnet_dir/xvectors_${name}/plda_scores \
        $nnet_dir/xvectors_${name}/plda_scores_t${threshold}

      md-eval.pl -r data/$name/speaker.rttm \
        -s $nnet_dir/xvectors_${name}/plda_scores_t${threshold}/rttm \
        2> $tuning_dir/t${threshold}.log \
        > $tuning_dir/t${threshold}

      der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
        $tuning_dir/t${threshold})
      if [ $(perl -e "print ($der < $best_der ? 1 : 0);") -eq 1 ]; then
        best_der=$der
        best_threshold=$threshold
      fi
    done
    echo "$best_threshold" > $tuning_dir/best

    local/diarization_cluster.sh \
      --cmd "$train_cmd --mem 60G" --nj 9 --threshold $(cat $tuning_dir/best) --rttm-channel 1 \
      $nnet_dir/xvectors_${name}/plda_scores \
      $nnet_dir/xvectors_${name}/plda_scores

    results_dir=$nnet_dir/results_$name
    rm -rf $results_dir
    mkdir -p $results_dir

    md-eval.pl -r data/$name/speaker.rttm \
      -s $nnet_dir/xvectors_${name}/plda_scores/rttm \
      2> $results_dir/threshold.log \
      > $results_dir/DER_threshold.txt
    der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
      $results_dir/DER_threshold.txt)
    echo "Using supervised calibration, DER: $der%"
fi

exit 1

# Cluster the PLDA scores using the oracle number of speakers
if [ $stage -le 8 ]; then
  # In this section, we show how to do the clustering if the number of speakers
  # (and therefore, the number of clusters) per recording is known in advance.
  for name in rtve_2018${suffix} rtve_2020${suffix}; do
    local/diarization_cluster.sh \
      --cmd "$train_cmd --mem 60G" --nj 9 --reco2num-spk data/$name/reco2num_spk --rttm-channel 1 \
      $nnet_dir/xvectors_${name}/plda_scores \
      $nnet_dir/xvectors_${name}/plda_scores_num_spk

    mkdir -p $nnet_dir/results_${name}
    # Now combine the results for callhome1 and callhome2 and evaluate it together.
    md-eval.pl -r data/$name/speaker.rttm \
      -s $nnet_dir/xvectors_${name}/plda_scores_num_spk/rttm 2> $nnet_dir/results_${name}/num_spk.log \
      > $nnet_dir/results_${name}/DER_num_spk.txt
    der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
      $nnet_dir/results_${name}/DER_num_spk.txt)
    # Using the oracle number of speakers, DER: 7.12%
    # Compare to 8.69% in ../v1/run.sh
    echo "Using the oracle number of speakers, DER: $der%"
  done
fi

