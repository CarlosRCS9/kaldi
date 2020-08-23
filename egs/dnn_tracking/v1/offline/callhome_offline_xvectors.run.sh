#!/bin/bash
# Copyright 2020 Carlos Castillo
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e

data_folder=data/callhome/
mfcc_conf=conf/mfcc_xvectors_callhome.conf
extractor_dim=128
extractor_model=/export/c03/carloscastillo/repos/kaldi_fix/egs/online_diarization/v1/exp/xvector_nnet_1a_pre
plda_a=/export/c03/carloscastillo/repos/kaldi_fix/egs/online_diarization/v1/exp/xvector_nnet_1a_pre/xvectors_callhome1
plda_b=/export/c03/carloscastillo/repos/kaldi_fix/egs/online_diarization/v1/exp/xvector_nnet_1a_pre/xvectors_callhome2
output_folder=/export/b03/carlosc/data/2020/augmented/callhome_offline/

random_seed=0
length=1.0
overlap=0.5
min_length=0.5

stage=0

# By default the RTTM file contains the speaker overlaps implicitly,
# in the first stage we make these overlaps explicit.
if [ $stage -le 0 ]; then
  echo run.sh stage 0
  for name in callhome1 callhome2; do
    mkdir -p $output_folder$name

    cat $data_folder$name/ref.rttm \
    | python3 scripts/rttm_explicit_overlap.py \
    > $output_folder$name/ref_explicit_overlap.rttm
  done
fi

# Generating overlapping speech to augment the database.
if [ $stage -le 1 ]; then
  echo run.sh stage 1
  for name in callhome1 callhome2; do
    cat $output_folder$name/ref_explicit_overlap.rttm \
    | python3 scripts/rttm_augment.py \
    $data_folder$name/wav.scp \
    $output_folder$name/ \
    --random-seed=$random_seed
  done
fi

# Applying a sliding window to the segments.
if [ $stage -le 2 ]; then
  echo run.sh stage 2
  for name in callhome1 callhome2; do
    rm -rf $output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim
    mkdir -p $output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim

    cat $output_folder$name/ref_augmented_$random_seed.rttm \
    | python3 scripts/rttm_split_filter.py $length $overlap --max-file-speakers=2 --max-segment-speakers=1 --min-length=$min_length \
    > $output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim/ref.rttm
  done
fi

# Extracting features
if [ $stage -le 3 ]; then
  echo run.sh stage 3
  for name in callhome1 callhome2; do
    cat $output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim/ref.rttm \
    | python3 scripts/rttm_extract.py \
    $output_folder$name/wav_augmented_$random_seed.scp \
    $output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim/ \
    $mfcc_conf \
    'xvectors' \
    $extractor_model
  done
fi


# Perform PLDA scoring
if [ $stage -le 4 ]; then
  echo run.sh stage 4
  # Perform PLDA scoring on all pairs of segments for each recording.
  # The first directory contains the PLDA model that used callhome2
  # to perform whitening (recall that we're treating callhome2 as a
  # held-out dataset).  The second directory contains the xVectors
  # for callhome1.
  name=callhome1
  diarization/nnet3/xvector/score_plda.sh --cmd "$train_cmd --mem 4G" --nj 20 \
    $plda_b \
    $output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim/exp/make_xvectors \
    $output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim/exp/make_xvectors/plda_scores

  # Do the same thing for callhome2.
  name=callhome2
  diarization/nnet3/xvector/score_plda.sh --cmd "$train_cmd --mem 4G" --nj 20 \
    $plda_a \
    $output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim/exp/make_xvectors \
    $output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim/exp/make_xvectors/plda_scores
fi

# Cluster the PLDA scores using a stopping threshold.
if [ $stage -le 5 ]; then
  echo run.sh stage 5
  # First, we find the threshold that minimizes the DER on each partition of
  # callhome.
  # mkdir -p exp/tuning
  for name in callhome1 callhome2; do
    echo "Tuning clustering threshold for $dataset"
    folder=$output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim
    mkdir -p $folder/exp/tuning
    best_der=100
    best_threshold=0
    utils/filter_scp.pl -f 2 $folder/wav.scp \
      $folder/ref.rttm > $folder/ref_tuning.rttm

    # The threshold is in terms of the log likelihood ratio provided by the
    # PLDA scores.  In a perfectly calibrated system, the threshold is 0.
    # In the following loop, we evaluate the clustering on a heldout dataset
    # (callhome1 is heldout for callhome2 and vice-versa) using some reasonable
    # thresholds for a well-calibrated system.
    for threshold in -0.3 -0.2 -0.1 -0.05 0 0.05 0.1 0.2 0.3; do
      diarization/cluster.sh --cmd "$train_cmd --mem 4G" --nj 20 \
        --threshold $threshold $folder/exp/make_xvectors/plda_scores \
        $folder/exp/make_xvectors/plda_scores_t$threshold

      md-eval.pl -r $folder/ref_tuning.rttm \
       -s $folder/exp/make_xvectors/plda_scores_t$threshold/rttm \
       2> $folder/exp/tuning/t${threshold}.log \
       > $folder/exp/tuning/t${threshold}

      der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
        $folder/exp/tuning/t${threshold})
      if [ $(perl -e "print ($der < $best_der ? 1 : 0);") -eq 1 ]; then
        best_der=$der
        best_threshold=$threshold
      fi
    done
    echo "$best_threshold" > $folder/exp/tuning/best
  done
fi

if [ $stage -le 6 ]; then
  # Cluster callhome1 using the best threshold found for callhome2.  This way,
  # callhome2 is treated as a held-out dataset to discover a reasonable
  # stopping threshold for callhome1.
  name=callhome1
  name2=callhome2
  folder=$output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim
  folder2=$output_folder$name2/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim
  diarization/cluster.sh --cmd "$train_cmd --mem 4G" --nj 20 \
    --threshold $(cat $folder2/exp/tuning/best) \
    $folder/exp/make_xvectors/plda_scores $folder/exp/make_xvectors/plda_scores

  # Do the same thing for callhome2, treating callhome1 as a held-out dataset
  # to discover a stopping threshold.
  diarization/cluster.sh --cmd "$train_cmd --mem 4G" --nj 20 \
    --threshold $(cat $folder/exp/tuning/best) \
    $folder2/exp/make_xvectors/plda_scores $folder2/exp/make_xvectors/plda_scores

  mkdir -p exp/results
  cat $folder/ref.rttm $folder2/ref.rttm > exp/results/fullref.rttm
  # Now combine the results for callhome1 and callhome2 and evaluate it
  # together.
  cat $folder/exp/make_xvectors/plda_scores/rttm \
    $folder2/exp/make_xvectors/plda_scores/rttm | md-eval.pl -r \
    exp/results/fullref.rttm -s - 2> exp/results/threshold.log \
    > exp/results/DER_threshold.txt
  der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
    exp/results/DER_threshold.txt)
  # Using supervised calibration, DER: 10.36%
  echo "Using supervised calibration, DER: $der%"
fi

# Cluster the PLDA scores using the oracle number of speakers
if [ $stage -le 7 ]; then
  # In this section, we show how to do the clustering if the number of speakers
  # (and therefore, the number of clusters) per recording is known in advance.
  name=callhome1
  name2=callhome2
  folder=$output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim
  folder2=$output_folder$name2/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim
  diarization/cluster.sh --cmd "$train_cmd --mem 4G" \
    --reco2num-spk $data_folder$name/reco2num_spk_2 \
    $folder/exp/make_xvectors/plda_scores $folder/exp/make_xvectors/plda_scores_num_spk

  diarization/cluster.sh --cmd "$train_cmd --mem 4G" \
    --reco2num-spk $data_folder$name2/reco2num_spk_2 \
    $folder2/exp/make_xvectors/plda_scores $folder2/exp/make_xvectors/plda_scores_num_spk

  mkdir -p exp/callhome_offline_xvectors
  cat $folder/exp/make_xvectors/plda_scores_num_spk/rttm \
  $folder2/exp/make_xvectors/plda_scores_num_spk/rttm > exp/callhome_offline_xvectors/results.rttm
  cat exp/callhome_offline_xvectors/results.rttm | python3 scripts/rttm_filter.py callhome > exp/callhome_offline_xvectors/results_filtered.rttm
  cp exp/results/fullref.rttm exp/callhome_offline_xvectors/groundtruth.rttm
  cat exp/callhome_offline_xvectors/groundtruth.rttm | python3 scripts/rttm_filter.py callhome > exp/callhome_offline_xvectors/groundtruth_filtered.rttm
  # Now combine the results for callhome1 and callhome2 and evaluate it together.
  cat exp/callhome_offline_xvectors/results_filtered.rttm \
    | md-eval.pl -r exp/callhome_offline_xvectors/groundtruth_filtered.rttm -s - 2> exp/callhome_offline_xvectors/num_spk.log \
    > exp/callhome_offline_xvectors/DER_num_spk.txt
  der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
    exp/callhome_offline_xvectors/DER_num_spk.txt)
  # Using the oracle number of speakers, DER: 8.69%
  echo "Using the oracle number of speakers, DER: $der%"

  cat exp/callhome_offline_xvectors/DER_num_spk.txt
fi

