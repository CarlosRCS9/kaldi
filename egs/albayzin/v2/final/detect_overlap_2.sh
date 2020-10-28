#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e

suffix=_EXP030
rtve_root=/export/corpora5/RTVE
nnet_dir=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/exp/sre19-av-models/xvector_nnet_5a.1.vcc.v2
plda_dir=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/exp/sre19-av-models/xvector_nnet_5a.1.vcc.v2/xvectors_rtve_2018_2020_janto5a_train
mfcc_conf=exp/sre19-av-models/mfcc_16k.conf

nj=9
stage=0

if [ $stage -le 0 ]; then
  # <speaker-overlap> <speaker-rename>
  #local/make_rtve_2018_dev2_2.sh eval $rtve_root/RTVE2018DB/dev2 data/rtve_2018${suffix} true false
  local/make_rtve_2020_dev_2.sh eval $rtve_root/RTVE2020DB/dev data/rtve_2020${suffix} true false
fi

if [ $stage -le 1 ]; then
  for name in rtve_2020${suffix}; do
    data_dir=data/$name

    steps/make_mfcc.sh \
      --cmd "$train_cmd" \
      --mfcc-config conf/mfcc_detect_overlaps.conf \
      --nj $nj \
      --write-utt2num-frames true \
      --write-utt2dur true \
      $data_dir

    steps/compute_cmvn_stats.sh \
      $data_dir

    utils/fix_data_dir.sh $data_dir
  done
fi

if [ $stage -le 2 ]; then
  for name in rtve_2020${suffix}; do
    data_dir=data/$name
    output_dir=exp/$name
    local/detect_overlaps.sh \
      --cmd "$train_cmd" \
      --nj 9 \
      $data_dir \
      exp/overlap_1a/tdnn_lstm_1a \
      $output_dir
  done
fi

exit 0

if [ $stage -le 1 ]; then
  for name in rtve_2018${suffix} rtve_2020${suffix}; do
    data_dir=data/$name
    steps/make_mfcc.sh \
      --cmd "$train_cmd --max-jobs-run 20" \
      --mfcc-config exp/0012_sad_v1/conf/mfcc_hires.conf \
      --nj 9 \
      --write-utt2num-frames true \
      --write-utt2dur true \
      $data_dir

    exp/0012_sad_v1/local/segmentation/detect_speech_activity.sh \
      --cmd "$train_cmd" \
      --nj 9 \
      $data_dir \
      exp/0012_sad_v1/exp/segmentation_1a/tdnn_stats_sad_1a \
      $data_dir/mfcc_hires \
      $data_dir \
      $data_dir

    utils/fix_data_dir.sh $data_dir
  done
fi

if [ $stage -le 2 ]; then
  # <speaker-overlap> <speaker-rename>
  local/make_rtve_2018_dev2_2.sh oracle $rtve_root/RTVE2018DB/dev2 data/rtve_2018${suffix}_eval true false
  local/make_rtve_2020_dev_2.sh oracle $rtve_root/RTVE2020DB/dev data/rtve_2020${suffix}_eval true false
fi

if [ $stage -le 3 ]; then
  for name in rtve_2018${suffix} rtve_2020${suffix}; do
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

  for name in rtve_2018${suffix} rtve_2020${suffix}; do
    dir=data/${name}_eval
    steps/make_mfcc.sh \
      --cmd "$train_cmd --max-jobs-run 20" \
      --mfcc-config $mfcc_conf \
      --nj 9 \
      --write-utt2dur true \
      --write-utt2num-frames true \
      $dir

    utils/fix_data_dir.sh $dir
  done
fi

if [ $stage -le 4 ]; then
  # Extract x-vectors for RTVE 2018 and 2020.
  for name in rtve_2018${suffix} rtve_2020${suffix}; do
    data_dir=data/${name}_eval
    output_dir=$nnet_dir/xvectors_${name}
    rm -rf $output_dir
    diarization/nnet3/xvector/extract_xvectors.sh \
      --cmd "$train_cmd --mem 5G" --nj 9 --window 1.5 --period 0.25 --apply-cmn false --min-segment 0.5 \
      $nnet_dir \
      $data_dir \
      $output_dir
  done
fi

# Train PLDA models
if [ $stage -le -5 ]; then
  for name in rtve_2018${suffix} rtve_2020${suffix}; do
    data_dir=$nnet_dir/xvectors_${name}
    # Train a PLDA model on VoxCeleb, using DIHARD 2018 development set to whiten.
    "queue.pl" $data_dir/log/plda.log \
      ivector-compute-plda ark:$data_dir/spk2utt \
        "ark:ivector-subtract-global-mean \
        scp:$data_dir/xvector.scp ark:- \
        | transform-vec $data_dir/transform.mat ark:- ark:- \
        | ivector-normalize-length ark:- ark:- |" \
      $data_dir/plda || exit 1;
  done
fi

if [ $stage -le -6 ]; then
  for name in rtve_2018${suffix} rtve_2020${suffix}; do
    echo data/${name}_eval
    echo $nnet_dir/xvectors_${name}
  done
fi

if [ $stage -le 7 ]; then
  # Perform PLDA scoring on all pairs of segments for each recording.
  #for name in rtve_2018${suffix} rtve_2020${suffix}; do
  for name in rtve_2020${suffix}; do
    data_dir=$nnet_dir/xvectors_${name}
    output_dir=$nnet_dir/xvectors_${name}/plda_scores
    diarization/nnet3/xvector/score_plda.sh \
      --cmd "$train_cmd --mem 4G" --nj 9 \
      $plda_dir \
      $data_dir \
      $output_dir
  done
fi

if [ $stage -le 8 ]; then
  # First, we find the threshold that minimizes the DER on RTVE 2018 development set.
  #for name in rtve_2018${suffix} rtve_2020${suffix}; do
  for name in rtve_2020${suffix}; do
    data_dir=$nnet_dir/xvectors_${name}/plda_scores
    output_dir=$nnet_dir/tuning_${name}
    rm -rf $output_dir
    mkdir -p $output_dir

    echo "Tuning clustering threshold for $name"
    best_der=100
    best_threshold=0

    # The threshold is in terms of the log likelihood ratio provided by the
    # PLDA scores.  In a perfectly calibrated system, the threshold is 0.
    # In the following loop, we evaluate DER performance on DIHARD 2018 development
    # set using some reasonable thresholds for a well-calibrated system.
    for threshold in -0.5 -0.4 -0.3 -0.2 -0.1 -0.05 0 0.05 0.1 0.2 0.3 0.4 0.5; do
      local/diarization_cluster.sh \
        --cmd "$train_cmd --mem 60G" --nj 9 --threshold $threshold --rttm-channel 1 \
        $data_dir \
        $output_dir/plda_scores_t${threshold}

      md-eval.pl \
        -r data/${name}_eval/ref.rttm \
        -s $output_dir/plda_scores_t${threshold}/rttm \
        2> $output_dir/${suffix}_t${threshold}.log \
        > $output_dir/${suffix}_t${threshold}

      der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
        $output_dir/${suffix}_t${threshold})
      if [ $(perl -e "print ($der < $best_der ? 1 : 0);") -eq 1 ]; then
        best_der=$der
        best_threshold=$threshold
      fi
    done
    echo "$best_threshold" > $output_dir/best
  done

  #for name in rtve_2018${suffix} rtve_2020${suffix}; do
  for name in rtve_2020${suffix}; do
    data_dir=$nnet_dir/xvectors_${name}/plda_scores
    output_dir=$nnet_dir/xvectors_${name}/plda_scores
    results_dir=$nnet_dir/xvectors_${name}/results
    mkdir -p $results_dir
    local/diarization_cluster.sh \
      --cmd "$train_cmd --mem 60G" --nj 9 --threshold $(cat $nnet_dir/tuning_${name}/best) --rttm-channel 1 \
      $data_dir \
      $output_dir

    # Compute the DER on the DIHARD 2018 evaluation set. We use the official metrics of
    # the DIHARD challenge. The DER is calculated with no unscored collars and including
    # overlapping speech.
    md-eval.pl \
      -r data/${name}_eval/ref.rttm \
      -s $output_dir/rttm \
      2> $results_dir/threshold.log \
      > $results_dir/DER_threshold.txt

    der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
      $results_dir/DER_threshold.txt)
    echo "Using supervised calibration, DER: $der%"
  done
fi

if [ $stage -le 9 ]; then
  #for name in rtve_2018${suffix} rtve_2020${suffix}; do
  for name in rtve_2020${suffix}; do
    data_dir=$nnet_dir/xvectors_${name}/plda_scores
    output_dir=$nnet_dir/xvectors_${name}/plda_scores_num_spk
    results_dir=$nnet_dir/xvectors_${name}/results_num_spk
    mkdir -p $results_dir
    local/diarization_cluster.sh \
      --cmd "$train_cmd --mem 60G" --nj 9 --reco2num-spk data/${name}_eval/reco2num_spk --rttm-channel 1 \
      $data_dir \
      $output_dir

    md-eval.pl \
      -r data/${name}_eval/ref.rttm \
      -s $output_dir/rttm \
      2> $results_dir/threshold.log \
      > $results_dir/DER_threshold.txt

    der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
      $results_dir/DER_threshold.txt)
    echo "Using oracle number of speakers, DER: $der%"
  done
fi

if [ $stage -le 10 ]; then
  #for name in rtve_2018${suffix} rtve_2020${suffix}; do
  for name in rtve_2020${suffix}; do
    data_dir=$nnet_dir/xvectors_${name}/plda_scores
    echo "------------------------- threshold -------------------------"
    python3 tests/rttm_speaker_accuracy.py data/${name}_eval/ref.rttm $data_dir/rttm
    echo "------------------------- speakers -------------------------"
    python3 tests/rttm_speaker_accuracy.py data/${name}_eval/ref.rttm ${data_dir}_num_spk/rttm
  done
fi

if [ $stage -le 11 ]; then
  #for name in rtve_2018${suffix} rtve_2020${suffix}; do
  for name in rtve_2020${suffix}; do
    echo $nnet_dir/xvectors_${name}/results/DER_threshold.txt
    echo $nnet_dir/xvectors_${name}/results_num_spk/DER_threshold.txt
  done
fi
