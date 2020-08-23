#!/usr/bin/env bash
# Copyright 2017-2018  David Snyder
#           2017-2018  Matthew Maciejewski
#
# Apache 2.0.
#
# This recipe demonstrates the use of x-vectors for speaker diarization.
# The scripts are based on the recipe in ../v1/run.sh, but clusters x-vectors
# instead of i-vectors.  It is similar to the x-vector-based diarization system
# described in "Diarization is Hard: Some Experiences and Lessons Learned for
# the JHU Team in the Inaugural DIHARD Challenge" by Sell et al.  The main
# difference is that we haven't implemented the VB resegmentation yet.

. ./cmd.sh
. ./path.sh
set -e
mfccdir=`pwd`/mfcc
vaddir=`pwd`/mfcc
data_root=/export/corpora5/LDC
stage=0
nnet_dir=exp/xvector_nnet_1a/
num_components=1024 # the number of UBM components (used for VB resegmentation)
ivector_dim=128 # the dimension of i-vector (used for VB resegmentation)

extractor_model=/export/c03/carloscastillo/repos/kaldi_fix/egs/callhome_diarization/v2/exp/xvector_nnet_1a_pre
plda_a=/export/c03/carloscastillo/repos/kaldi_fix/egs/callhome_diarization/v2/exp/xvector_nnet_1a_pre/xvectors_callhome1
plda_b=/export/c03/carloscastillo/repos/kaldi_fix/egs/callhome_diarization/v2/exp/xvector_nnet_1a_pre/xvectors_callhome2

# Prepare features
if [ $stage -le 1 ]; then
  # The script local/make_callhome.sh splits callhome into two parts, called
  # callhome1 and callhome2.  Each partition is treated like a held-out
  # dataset, and used to estimate various quantities needed to perform
  # diarization on the other part (and vice versa).
  for name in train callhome1 callhome2 callhome; do
    steps/make_mfcc.sh --mfcc-config conf/mfcc.conf --nj 40 \
      --cmd "$train_cmd" --write-utt2num-frames true \
      data/$name exp/make_mfcc $mfccdir
    utils/fix_data_dir.sh data/$name
  done

  for name in train callhome1 callhome2; do
    sid/compute_vad_decision.sh --nj 40 --cmd "$train_cmd" \
      data/$name exp/make_vad $vaddir
    utils/fix_data_dir.sh data/$name
  done

  # The sre dataset is a subset of train
  cp data/train/{feats,vad}.scp data/sre/
  utils/fix_data_dir.sh data/sre

  # This writes features to disk after applying the sliding window CMN.
  # Although this is somewhat wasteful in terms of disk space, for diarization
  # it ends up being preferable to performing the CMN in memory.  If the CMN
  # were performed in memory (e.g., we used --apply-cmn true in
  # diarization/nnet3/xvector/extract_xvectors.sh) it would need to be
  # performed after the subsegmentation, which leads to poorer results.
  for name in sre callhome1 callhome2; do
    local/nnet3/xvector/prepare_feats.sh --nj 40 --cmd "$train_cmd" \
      data/$name data/${name}_cmn exp/${name}_cmn
    cp data/$name/vad.scp data/${name}_cmn/
    if [ -f data/$name/segments ]; then
      cp data/$name/segments data/${name}_cmn/
    fi
    utils/fix_data_dir.sh data/${name}_cmn
  done

  echo "0.01" > data/sre_cmn/frame_shift
  # Create segments to extract x-vectors from for PLDA training data.
  # The segments are created using an energy-based speech activity
  # detection (SAD) system, but this is not necessary.  You can replace
  # this with segments computed from your favorite SAD.
  diarization/vad_to_segments.sh --nj 40 --cmd "$train_cmd" \
    data/sre_cmn data/sre_cmn_segmented
fi

# Extract x-vectors
if [ $stage -le 7 ]; then
  # Extract x-vectors for the two partitions of callhome.
  diarization/nnet3/xvector/extract_xvectors.sh --cmd "$train_cmd --mem 5G" \
    --nj 40 --window 1.5 --period 0.75 --apply-cmn false \
    --min-segment 0.5 $extractor_model \
    data/callhome1_cmn $nnet_dir/xvectors_callhome1

  diarization/nnet3/xvector/extract_xvectors.sh --cmd "$train_cmd --mem 5G" \
    --nj 40 --window 1.5 --period 0.75 --apply-cmn false \
    --min-segment 0.5 $extractor_model \
    data/callhome2_cmn $nnet_dir/xvectors_callhome2
fi

# Perform PLDA scoring
if [ $stage -le 9 ]; then
  # Perform PLDA scoring on all pairs of segments for each recording.
  # The first directory contains the PLDA model that used callhome2
  # to perform whitening (recall that we're treating callhome2 as a
  # held-out dataset).  The second directory contains the x-vectors
  # for callhome1.
  diarization/nnet3/xvector/score_plda.sh --cmd "$train_cmd --mem 4G" \
    --nj 20 $plda_b $nnet_dir/xvectors_callhome1 \
    $nnet_dir/xvectors_callhome1/plda_scores

  # Do the same thing for callhome2.
  diarization/nnet3/xvector/score_plda.sh --cmd "$train_cmd --mem 4G" \
    --nj 20 $plda_a $nnet_dir/xvectors_callhome2 \
    $nnet_dir/xvectors_callhome2/plda_scores
fi

# Cluster the PLDA scores using a stopping threshold.
if [ $stage -le 10 ]; then
  # First, we find the threshold that minimizes the DER on each partition of
  # callhome.
  mkdir -p $nnet_dir/tuning
  for dataset in callhome1 callhome2; do
    echo "Tuning clustering threshold for $dataset"
    best_der=100
    best_threshold=0
    utils/filter_scp.pl -f 2 data/$dataset/wav.scp \
      data/callhome/fullref.rttm > data/$dataset/ref.rttm

    # The threshold is in terms of the log likelihood ratio provided by the
    # PLDA scores.  In a perfectly calibrated system, the threshold is 0.
    # In the following loop, we evaluate the clustering on a heldout dataset
    # (callhome1 is heldout for callhome2 and vice-versa) using some reasonable
    # thresholds for a well-calibrated system.
    for threshold in -0.3 -0.2 -0.1 -0.05 0 0.05 0.1 0.2 0.3; do
      diarization/cluster.sh --cmd "$train_cmd --mem 4G" --nj 20 \
        --threshold $threshold $nnet_dir/xvectors_$dataset/plda_scores \
        $nnet_dir/xvectors_$dataset/plda_scores_t$threshold

      md-eval.pl -1 -c 0.25 -r data/$dataset/ref.rttm \
       -s $nnet_dir/xvectors_$dataset/plda_scores_t$threshold/rttm \
       2> $nnet_dir/tuning/${dataset}_t${threshold}.log \
       > $nnet_dir/tuning/${dataset}_t${threshold}

      der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
        $nnet_dir/tuning/${dataset}_t${threshold})
      if [ $(perl -e "print ($der < $best_der ? 1 : 0);") -eq 1 ]; then
        best_der=$der
        best_threshold=$threshold
      fi
    done
    echo "$best_threshold" > $nnet_dir/tuning/${dataset}_best
  done

  # Cluster callhome1 using the best threshold found for callhome2.  This way,
  # callhome2 is treated as a held-out dataset to discover a reasonable
  # stopping threshold for callhome1.
  diarization/cluster.sh --cmd "$train_cmd --mem 4G" --nj 20 \
    --threshold $(cat $nnet_dir/tuning/callhome2_best) \
    $nnet_dir/xvectors_callhome1/plda_scores $nnet_dir/xvectors_callhome1/plda_scores

  # Do the same thing for callhome2, treating callhome1 as a held-out dataset
  # to discover a stopping threshold.
  diarization/cluster.sh --cmd "$train_cmd --mem 4G" --nj 20 \
    --threshold $(cat $nnet_dir/tuning/callhome1_best) \
    $nnet_dir/xvectors_callhome2/plda_scores $nnet_dir/xvectors_callhome2/plda_scores

  mkdir -p $nnet_dir/results
  # Now combine the results for callhome1 and callhome2 and evaluate it
  # together.
  cat $nnet_dir/xvectors_callhome1/plda_scores/rttm \
    $nnet_dir/xvectors_callhome2/plda_scores/rttm | md-eval.pl -1 -c 0.25 -r \
    data/callhome/fullref.rttm -s - 2> $nnet_dir/results/threshold.log \
    > $nnet_dir/results/DER_threshold.txt
  der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
    $nnet_dir/results/DER_threshold.txt)
  # Using supervised calibration, DER: 8.39%
  # Compare to 10.36% in ../v1/run.sh
  echo "Using supervised calibration, DER: $der%"
fi

# Cluster the PLDA scores using the oracle number of speakers
if [ $stage -le 11 ]; then
  # In this section, we show how to do the clustering if the number of speakers
  # (and therefore, the number of clusters) per recording is known in advance.
  diarization/cluster.sh --cmd "$train_cmd --mem 4G" \
    --reco2num-spk data/callhome1/reco2num_spk \
    $nnet_dir/xvectors_callhome1/plda_scores $nnet_dir/xvectors_callhome1/plda_scores_num_spk

  diarization/cluster.sh --cmd "$train_cmd --mem 4G" \
    --reco2num-spk data/callhome2/reco2num_spk \
    $nnet_dir/xvectors_callhome2/plda_scores $nnet_dir/xvectors_callhome2/plda_scores_num_spk

  mkdir -p $nnet_dir/results
  # Now combine the results for callhome1 and callhome2 and evaluate it together.
  cat $nnet_dir/xvectors_callhome1/plda_scores_num_spk/rttm \
  $nnet_dir/xvectors_callhome2/plda_scores_num_spk/rttm \
    | md-eval.pl -1 -c 0.25 -r data/callhome/fullref.rttm -s - 2> $nnet_dir/results/num_spk.log \
    > $nnet_dir/results/DER_num_spk.txt
  der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
    $nnet_dir/results/DER_num_spk.txt)
  # Using the oracle number of speakers, DER: 7.12%
  # Compare to 8.69% in ../v1/run.sh
  echo "Using the oracle number of speakers, DER: $der%"
fi

# Variational Bayes resegmentation using the code from Brno University of Technology
# Please see https://speech.fit.vutbr.cz/software/vb-diarization-eigenvoice-and-hmm-priors 
# for details
if [ $stage -le 12 ]; then
  utils/subset_data_dir.sh data/train 32000 data/train_32k
  # Train the diagonal UBM.
  sid/train_diag_ubm.sh --cmd "$train_cmd --mem 20G" \
    --nj 40 --num-threads 8 --subsample 1 --delta-order 0 --apply-cmn false \
    data/train_32k $num_components exp/diag_ubm_$num_components

  # Train the i-vector extractor. The UBM is assumed to be diagonal.
  diarization/train_ivector_extractor_diag.sh \
    --cmd "$train_cmd --mem 35G" \
    --ivector-dim $ivector_dim --num-iters 5 --apply-cmn false \
    --num-threads 1 --num-processes 1 --nj 40 \
    exp/diag_ubm_$num_components/final.dubm data/train \
    exp/extractor_diag_c${num_components}_i${ivector_dim}
fi

if [ $stage -le 13 ]; then
  output_rttm_dir=exp/VB/rttm
  mkdir -p $output_rttm_dir || exit 1;
  cat $nnet_dir/xvectors_callhome1/plda_scores/rttm \
    $nnet_dir/xvectors_callhome2/plda_scores/rttm > $output_rttm_dir/x_vector_rttm
  init_rttm_file=$output_rttm_dir/x_vector_rttm

  # VB resegmentation. In this script, I use the x-vector result to 
  # initialize the VB system. You can also use i-vector result or random 
  # initize the VB system. The following script uses kaldi_io. 
  # You could use `sh ../../../tools/extras/install_kaldi_io.sh` to install it
  diarization/VB_resegmentation.sh --nj 20 --cmd "$train_cmd --mem 10G" \
    --initialize 1 data/callhome $init_rttm_file exp/VB \
    exp/diag_ubm_$num_components/final.dubm exp/extractor_diag_c${num_components}_i${ivector_dim}/final.ie || exit 1; 

  # Compute the DER after VB resegmentation
  mkdir -p exp/VB/results || exit 1;
  md-eval.pl -1 -c 0.25 -r data/callhome/fullref.rttm -s $output_rttm_dir/VB_rttm 2> exp/VB/log/VB_DER.log \
    > exp/VB/results/VB_DER.txt
  der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
    exp/VB/results/VB_DER.txt)
  # After VB resegmentation, DER: 6.48%
  echo "After VB resegmentation, DER: $der%"
fi
