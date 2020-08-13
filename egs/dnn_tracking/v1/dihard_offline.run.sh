#!/bin/bash
# Copyright 2020 Carlos Castillo
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e

data_folder=data/dihardii/
mfcc_conf=conf/mfcc_ivectors_dihard.conf
extractor_dim=400
extractor_model=/export/c03/carloscastillo/repos/kaldi_fix/egs/online_diarization/v1/exp/extractor_c2048_i400/extractor_c2048_i400
plda_a=/export/b02/jiaminx/kaldi-dihard2/egs/babyCry2/i_vector/exp/extractor_c2048_i400/ivectors_dihard_2018_dev
plda_b=/export/b02/jiaminx/kaldi-dihard2/egs/babyCry2/i_vector/exp/extractor_c2048_i400/ivectors_dihard_2018_dev
output_folder=/export/b03/carlosc/data/2020/augmented/dihard_offline/

random_seed=0
length=1.0
overlap=0.5
min_length=0.5

stage=2

# By default the RTTM file contains the speaker overlaps implicitly,
# in the first stage we make these overlaps explicit.
if [ $stage -le 0 ]; then
  echo run.sh stage 0
  for name in development evaluation; do
    mkdir -p $output_folder$name

    cat $data_folder$name/ref.rttm \
    | python3 scripts/rttm_explicit_overlap.py \
    > $output_folder$name/ref_explicit_overlap.rttm
  done
fi

# Generating overlapping speech to augment the database.
if [ $stage -le 1 ]; then
  echo run.sh stage 1
  for name in development evaluation; do
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
  for name in development evaluation; do
    mkdir -p $output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim

    cat $output_folder$name/ref_augmented_$random_seed.rttm \
    | python3 scripts/rttm_split_filter.py $length $overlap --max-file-speakers=2 --max-segment-speakers=1 --min-length=$min_length \
    > $output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim/ref.rttm
  done
fi

# Extracting features
if [ $stage -le 3 ]; then
  echo run.sh stage 3
  for name in development evaluation; do
    cat $output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim/ref.rttm \
    | python3 scripts/rttm_extract.py \
    $output_folder$name/wav_augmented_$random_seed.scp \
    $output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim/ \
    $mfcc_conf \
    $extractor_model
  done
fi


# Perform PLDA scoring
if [ $stage -le 4 ]; then
  echo run.sh stage 4
  # Perform PLDA scoring on all pairs of segments for each recording.
  # The first directory contains the PLDA model that used evaluation
  # to perform whitening (recall that we're treating evaluation as a
  # held-out dataset).  The second directory contains the iVectors
  # for development.
  name=development
  diarization/score_plda.sh --cmd "$train_cmd --mem 4G" --nj 20 \
    $plda_b \
    $output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim/exp/make_ivectors \
    $output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim/exp/make_ivectors/plda_scores

  # Do the same thing for evaluation.
  name=evaluation
  diarization/score_plda.sh --cmd "$train_cmd --mem 4G" --nj 20 \
    $plda_a \
    $output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim/exp/make_ivectors \
    $output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim/exp/make_ivectors/plda_scores
fi

# Cluster the PLDA scores using a stopping threshold.
if [ $stage -le 5 ]; then
  echo run.sh stage 5
  # First, we find the threshold that minimizes the DER on each partition of
  # callhome.
  # mkdir -p exp/tuning
  for name in development evaluation; do
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
    # (development is heldout for evaluation and vice-versa) using some reasonable
    # thresholds for a well-calibrated system.
    for threshold in -0.3 -0.2 -0.1 -0.05 0 0.05 0.1 0.2 0.3; do
      diarization/cluster.sh --cmd "$train_cmd --mem 4G" --nj 20 \
        --threshold $threshold $folder/exp/make_ivectors/plda_scores \
        $folder/exp/make_ivectors/plda_scores_t$threshold

      md-eval.pl -r $folder/ref_tuning.rttm \
       -s $folder/exp/make_ivectors/plda_scores_t$threshold/rttm \
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
  # Cluster development using the best threshold found for evaluation.  This way,
  # evaluation is treated as a held-out dataset to discover a reasonable
  # stopping threshold for development.
  name=development
  name2=evaluation
  folder=$output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim
  folder2=$output_folder$name2/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim
  diarization/cluster.sh --cmd "$train_cmd --mem 4G" --nj 20 \
    --threshold $(cat $folder2/exp/tuning/best) \
    $folder/exp/make_ivectors/plda_scores $folder/exp/make_ivectors/plda_scores

  # Do the same thing for evaluation, treating development as a held-out dataset
  # to discover a stopping threshold.
  diarization/cluster.sh --cmd "$train_cmd --mem 4G" --nj 20 \
    --threshold $(cat $folder/exp/tuning/best) \
    $folder2/exp/make_ivectors/plda_scores $folder2/exp/make_ivectors/plda_scores

  mkdir -p exp/results
  cat $folder/ref.rttm $folder2/ref.rttm > exp/results/fullref.rttm
  # Now combine the results for development and evaluation and evaluate it
  # together.
  cat $folder/exp/make_ivectors/plda_scores/rttm \
    $folder2/exp/make_ivectors/plda_scores/rttm | md-eval.pl -r \
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
  name=development
  name2=evaluation
  folder=$output_folder$name/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim
  folder2=$output_folder$name2/augmented_$random_seed/$length'_'$overlap'_'$min_length/$extractor_dim
  diarization/cluster.sh --cmd "$train_cmd --mem 4G" \
    --reco2num-spk $data_folder$name/reco2num_spk_2 \
    $folder/exp/make_ivectors/plda_scores $folder/exp/make_ivectors/plda_scores_num_spk

  diarization/cluster.sh --cmd "$train_cmd --mem 4G" \
    --reco2num-spk $data_folder$name2/reco2num_spk_2 \
    $folder2/exp/make_ivectors/plda_scores $folder2/exp/make_ivectors/plda_scores_num_spk

  mkdir -p exp/results
  # Now combine the results for development and evaluation and evaluate it together.
  cat $folder/exp/make_ivectors/plda_scores_num_spk/rttm \
  $folder2/exp/make_ivectors/plda_scores_num_spk/rttm \
    | md-eval.pl -r exp/results/fullref.rttm -s - 2> exp/results/num_spk.log \
    > exp/results/DER_num_spk.txt
  der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
    exp/results/DER_num_spk.txt)
  # Using the oracle number of speakers, DER: 8.69%
  echo "Using the oracle number of speakers, DER: $der%"
fi
