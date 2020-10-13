#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e

num_components=2048
ivector_dim=128

suffix=_EXP007
extractor_dir=exp/${suffix}_extractor_c${num_components}_i${ivector_dim}
rtve_root=/export/corpora5/RTVE

stage=0

if [ $stage -le 0 ]; then
  # <speaker-overlap> <speaker-rename>
  local/make_rtve_2018_dev2.sh train $rtve_root/RTVE2018DB/dev2 data/rtve_2018${suffix}_train false true
  local/make_rtve_2020_dev.sh train $rtve_root/RTVE2020DB/dev data/rtve_2020${suffix}_train false true
fi

if [ $stage -le 1 ]; then
  for name in rtve_2018${suffix}_train rtve_2020${suffix}_train; do
    steps/make_mfcc.sh \
      --mfcc-config exp/sre19-av-models/mfcc_16k.conf \
      --nj 40 \
      --cmd "$train_cmd --max-jobs-run 20" \
      --write-utt2num-frames true \
      --write-utt2dur true \
     data/$name
    utils/fix_data_dir.sh data/$name
  done

  for name in rtve_2018${suffix}_train rtve_2020${suffix}_train; do
    mv data/$name/ref.rttm data/$name/ref.rttm.bak
    python3 scripts/segments_to_rttm.py data/$name > data/$name/ref.rttm
    python3 scripts/make_oracle_vad.py data/$name
  done

  for name in rtve_2018${suffix}_train rtve_2020${suffix}_train; do
    rm -rf data/${name}_cmn
    local/nnet3/xvector/prepare_feats.sh \
      --nj 40 \
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

  echo "0.01" > data/rtve_2018${suffix}_train_cmn/frame_shift
  echo "0.01" > data/rtve_2020${suffix}_train_cmn/frame_shift

  for name in rtve_2018${suffix}_train rtve_2020${suffix}_train; do
    rm -rf data/${name}_cmn_segmented
    diarization/vad_to_segments.sh \
      --nj 40 \
      --cmd "$train_cmd" \
      data/${name}_cmn \
      data/${name}_cmn_segmented
  done
fi

# Train UBM and i-vector extractor
if [ $stage -le 2 ]; then
  utils/combine_data.sh \
    data/train${suffix}_ivector \
    data/rtve_2018${suffix}_train_cmn_segmented \
    data/rtve_2020${suffix}_train_cmn_segmented

  # Train UBM and i-vector extractor.
  sid/train_diag_ubm.sh \
    --cmd "$train_cmd --mem 20G" --nj 40 --num-threads 8 --delta-order 1 --apply-cmn false \
    data/train${suffix}_ivector $num_components \
    exp/${suffix}_diag_ubm_$num_components

  sid/train_full_ubm.sh --nj 40 --remove-low-count-gaussians false --cmd "$train_cmd --mem 25G" --apply-cmn false \
    data/train${suffix}_ivector exp/${suffix}_diag_ubm_$num_components \
    exp/${suffix}_full_ubm_$num_components

  sid/train_ivector_extractor.sh \
    --cmd "$train_cmd --mem 35G" --nj 10 --ivector-dim $ivector_dim --num-iters 5 --apply-cmn false \
    exp/${suffix}_full_ubm_$num_components/final.ubm data/train${suffix}_ivector \
    exp/${suffix}_extractor_c${num_components}_i${ivector_dim}
fi

if [ $stage -le 3 ]; then
  # <speaker-overlap> <speaker-rename>
  local/make_rtve_2018_dev2.sh train $rtve_root/RTVE2018DB/dev2 data/rtve_2018${suffix}_plda false true
  local/make_rtve_2020_dev.sh train $rtve_root/RTVE2020DB/dev data/rtve_2020${suffix}_plda false true
fi

if [ $stage -le 4 ]; then
  for name in rtve_2018${suffix}_plda rtve_2020${suffix}_plda; do
    steps/make_mfcc.sh \
      --mfcc-config exp/sre19-av-models/mfcc_16k.conf \
      --nj 40 \
      --cmd "$train_cmd --max-jobs-run 20" \
      --write-utt2num-frames true \
      --write-utt2dur true \
     data/$name
    utils/fix_data_dir.sh data/$name
  done

  for name in rtve_2018${suffix}_plda rtve_2020${suffix}_plda; do
    mv data/$name/ref.rttm data/$name/ref.rttm.bak
    python3 scripts/segments_to_rttm.py data/$name > data/$name/ref.rttm
    python3 scripts/make_oracle_vad.py data/$name
  done

  for name in rtve_2018${suffix}_plda rtve_2020${suffix}_plda; do
    rm -rf data/${name}_cmn
    local/nnet3/xvector/prepare_feats.sh \
      --nj 40 \
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

  echo "0.01" > data/rtve_2018${suffix}_plda_cmn/frame_shift
  echo "0.01" > data/rtve_2020${suffix}_plda_cmn/frame_shift

  for name in rtve_2018${suffix}_plda rtve_2020${suffix}_plda; do
    rm -rf data/${name}_cmn_segmented
    diarization/vad_to_segments.sh \
      --nj 40 \
      --cmd "$train_cmd" \
      data/${name}_cmn \
      data/${name}_cmn_segmented
  done
fi

if [ $stage -le 5 ]; then
  utils/combine_data.sh \
    data/train${suffix}_plda \
    data/rtve_2018${suffix}_plda_cmn_segmented \
    data/rtve_2020${suffix}_plda_cmn_segmented

  diarization/extract_ivectors.sh \
    --cmd "$train_cmd --mem 25G" --nj 40 --window 3.0 --period 10.0 --min-segment 1.5 --apply-cmn false --hard-min true \
    exp/${suffix}_extractor_c${num_components}_i${ivector_dim} \
    data/train${suffix}_plda \
    exp/ivectors_train${suffix}_plda
fi

# Train PLDA models
if [ $stage -le 6 ]; then
  "queue.pl" $extractor_dir/log/plda.log \
    ivector-compute-plda ark:exp/ivectors_train${suffix}_plda/spk2utt \
      "ark:ivector-subtract-global-mean \
      scp:exp/ivectors_train${suffix}_plda/ivector.scp ark:- \
      | transform-vec exp/ivectors_train${suffix}_plda/transform.mat ark:- ark:- \
      | ivector-normalize-length ark:- ark:- |" \
    $extractor_dir/plda || exit 1;
fi

if [ $stage -le 7 ]; then
  local/make_rtve_2018_dev2.sh oracle $rtve_root/RTVE2018DB/dev2 data/rtve_2018${suffix} false true
  local/make_rtve_2020_dev.sh oracle $rtve_root/RTVE2020DB/dev data/rtve_2020${suffix} false true
  local/make_rtve_2020_test_diarization.sh $rtve_root/RTVE2020DB/test/audio/SD data/rtve_2020_test${suffix}
fi

if [ $stage -le 8 ]; then
  # Make MFCCs for each dataset.
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

  for name in rtve_2018${suffix} rtve_2020${suffix}; do
    python3 scripts/make_oracle_vad.py data/$name
  done

  for name in rtve_2020_test${suffix}; do
    exp/0012_sad_v1/local/segmentation/detect_speech_activity.sh \
      --cmd "$train_cmd" --nj 9 \
      data/$name \
     exp/0012_sad_v1/exp/segmentation_1a/tdnn_stats_sad_1a \
      data/$name/mfcc_hires \
      data/$name \
      data/$name
  done

  for name in rtve_2018${suffix} rtve_2020${suffix} rtve_2020_test${suffix}_seg; do
    rm -rf data/${name}_cmn
    local/nnet3/xvector/prepare_feats.sh \
      --nj 9 \
      --cmd "$train_cmd" \
      data/${name} \
      data/${name}_cmn \
      exp/${name}_cmn
    if [ -f data/${name}/vad.scp ]; then
      cp data/${name}/vad.scp data/${name}_cmn/
    fi
    if [ -f data/${name}/segments ]; then
      cp data/${name}/segments data/${name}_cmn/
    fi
    utils/fix_data_dir.sh data/${name}_cmn
  done

  mv data/rtve_2020_test${suffix}_seg_cmn data/rtve_2020_test${suffix}_cmn

  echo "0.01" > data/rtve_2018${suffix}_cmn/frame_shift
  echo "0.01" > data/rtve_2020${suffix}_cmn/frame_shift
  echo "0.01" > data/rtve_2020_test${suffix}_cmn/frame_shift

  for name in rtve_2018${suffix} rtve_2020${suffix}; do
    rm -rf data/${name}_cmn_segmented
    diarization/vad_to_segments.sh \
     --nj 9 \
      --cmd "$train_cmd" \
      data/${name}_cmn \
      data/${name}_cmn_segmented
  done

  mv data/rtve_2020_test${suffix}_cmn data/rtve_2020_test${suffix}_cmn_segmented
fi

if [ $stage -le 9 ]; then
  for name in rtve_2018${suffix} rtve_2020${suffix} rtve_2020_test${suffix}; do
    diarization/extract_ivectors.sh \
      --cmd "$train_cmd --mem 25G" --nj 9 --window 3.0 --period 10.0 --min-segment 1.5 --apply-cmn false --hard-min true \
      $extractor_dir \
      data/${name}_cmn_segmented \
      exp/ivectors_${name}
  done
fi

if [ $stage -le 10 ]; then
  for name in rtve_2018${suffix} rtve_2020${suffix} rtve_2020_test${suffix}; do
     cp $extractor_dir/plda exp/ivectors_${name}/
     diarization/score_plda.sh --cmd "$train_cmd --mem 4G" --nj 9 \
      exp/ivectors_${name} \
      exp/ivectors_${name} \
      exp/ivectors_${name}/plda_scores
  done
fi

if [ $stage -le 11 ]; then
  for name in rtve_2018${suffix} rtve_2020${suffix}; do
    tuning_dir=$extractor_dir/tuning_$name
    rm -rf $tuning_dir
    mkdir -p $tuning_dir

    echo "Tuning clustering threshold $tuning_dir"
    best_der=100
    best_threshold=0
    for threshold in -0.5 -0.4 -0.3 -0.2 -0.1 -0.05 0 0.05 0.1 0.2 0.3 0.4 0.5; do
      local/diarization_cluster.sh \
        --cmd "$train_cmd --mem 60G" --nj 3 --threshold $threshold --rttm-channel 1 \
        exp/ivectors_${name}/plda_scores \
        exp/ivectors_${name}/plda_scores_t${threshold}

      md-eval.pl -r data/$name/ref.rttm \
        -s exp/ivectors_${name}/plda_scores_t${threshold}/rttm \
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
      --cmd "$train_cmd --mem 60G" --nj 3 --threshold $(cat $tuning_dir/best) --rttm-channel 1 \
      exp/ivectors_${name}/plda_scores \
      exp/ivectors_${name}/plda_scores

    results_dir=$extractor_dir/results_$name
    rm -rf $results_dir
    mkdir -p $results_dir

    md-eval.pl -r data/$name/ref.rttm \
      -s exp/ivectors_${name}/plda_scores/rttm \
      2> $results_dir/threshold.log \
      > $results_dir/DER_threshold.txt

    der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
      $results_dir/DER_threshold.txt)
    echo "Using supervised calibration, DER: $der%"
  done
fi
