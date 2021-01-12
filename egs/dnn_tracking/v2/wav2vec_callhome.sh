#!/usr/bin/env bash

. ./cmd.sh
. ./path.sh

stage=5

callhome_root=/export/corpora5/LDC/LDC2001S97
wav_dir=/export/b03/carlosc/data/wav
data_root=data/wav2vec

if [ $stage -le 0 ]; then
  # Prepare the Callhome portion of NIST SRE 2000.
  local/make_callhome.sh $callhome_root data
fi

# Write wav files to disk
if [ $stage -le 1 ]; then
  for name in callhome1 callhome2; do
    data_dir=data/$name
    output_dir=$wav_dir/$name
    mkdir -p $output_dir
    while IFS= read -r line; do
      recording_id=$(echo $line | cut -d " " -f1)
      command=$(echo $line | cut -d " " -f2-)
      filepath=$output_dir/${recording_id}.wav
      if [ ! -f $filepath ]; then
        command="${command::-2} $filepath"
        echo $command
        $command
      fi
    done < $data_dir/wav.scp    
  done
fi

# Write data directory content
if [ $stage -le 2 ]; then
  for name in callhome1 callhome2; do
    data_dir=$wav_dir/$name
    output_dir=$data_root/$name

    rm -rf $output_dir
    mkdir -p $output_dir

    for filepath in $(ls $data_dir/*.wav); do
      filename_no_extension=$(basename $filepath .wav)
      echo "$filename_no_extension $filepath" >> $output_dir/wav.scp
    done

    cat $output_dir/wav.scp | awk '{print $1" "$1}' > $output_dir/utt2spk
    cp data/$name/ref.rttm $output_dir/
    cp $output_dir/utt2spk $output_dir/spk2utt
    echo 0.01 > $output_dir/frame_shift
    local/get_utt2dur.sh $output_dir
  done
fi

if [ $stage -le 3 ]; then
  for name in callhome1 callhome2; do
    data_dir=$wav_dir/$name

    for filename in $(ls $data_dir); do
      filepath=$data_dir/$filename
      sample_rate=$(soxi -r $filepath)
      if [ $sample_rate != 16000 ]; then
        command="sox $filepath -r 16000 -e floating-point -b 32 ${filepath}.tmp.wav"
        echo $command
        $command
        echo mv ${filepath}.tmp.wav $filepath
      fi
    done
    
    for filepath in $(ls $data_dir/*tmp.wav); do
      original_filepath=${filepath::-8}
      command="mv $filepath $original_filepath"
      echo $command
      $command
    done
  done
fi

if [ $stage -le 4 ]; then
  for name in callhome1 callhome2; do
    data_dir=$data_root/$name
    output_dir=$data_root/ivectors_${name}
    python wav2vec_extract.py $data_dir $output_dir
    cat $output_dir/utt2spk | utils/utt2spk_to_spk2utt.pl > $output_dir/spk2utt

    echo "$0: Computing mean of iVectors"
    "queue.pl" $output_dir/log/mean.log \
      ivector-mean scp:$output_dir/ivector.scp $output_dir/mean.vec || exit 1;

    echo "$0: Computing whitening transform" 
    "queue.pl" $output_dir/log/transform.log \
      est-pca --read-vectors=true --normalize-mean=false \
        --normalize-variance=true --dim=-1 \
        scp:$output_dir/ivector.scp $output_dir/transform.mat || exit 1;
  done
fi

if [ $stage -le 5 ]; then
  #"queue.pl" $data_root/ivectors_callhome1/log/plda.log \
  #  ivector-compute-plda ark:$data_root/ivectors_callhome1/spk2utt \
  #    "ark:ivector-subtract-global-mean \
  #    scp:$data_root/ivectors_callhome1/ivector.scp ark:- \
  #    | transform-vec $data_root/ivectors_callhome1/transform.mat ark:- ark:- \
  #    | ivector-normalize-length ark:- ark:- |" \
  #  $data_root/ivectors_callhome1/plda || exit 1;

  #"queue.pl" $data_root/ivectors_callhome2/log/plda.log \
  #  ivector-compute-plda ark:$data_root/ivectors_callhome2/spk2utt \
  #    "ark:ivector-subtract-global-mean \
  #    scp:$data_root/ivectors_callhome2/ivector.scp ark:- \
  #    | transform-vec $data_root/ivectors_callhome2/transform.mat ark:- ark:- \
  #    | ivector-normalize-length ark:- ark:- |" \
  #  $data_root/ivectors_callhome2/plda || exit 1;

  "queue.pl" $data_root/ivectors_callhome1/log/plda.log \
    ivector-compute-plda --num-em-iters=5 \
      ark:$data_root/ivectors_callhome1/spk2utt \
      scp:$data_root/ivectors_callhome1/ivector.scp \
      $data_root/ivectors_callhome1/plda

  "queue.pl" $data_root/ivectors_callhome2/log/plda.log \
    ivector-compute-plda --num-em-iters=5 \
      ark:$data_root/ivectors_callhome2/spk2utt \
      scp:$data_root/ivectors_callhome2/ivector.scp \
      $data_root/ivectors_callhome2/plda
fi

if [ $stage -le 6 ]; then
  diarization/score_plda.sh --cmd "$train_cmd --mem 4G" \
    --nj 20 $data_root/ivectors_callhome2 $data_root/ivectors_callhome1 \
    $data_root/ivectors_callhome1/plda_scores

  diarization/score_plda.sh --cmd "$train_cmd --mem 4G" \
    --nj 20 $data_root/ivectors_callhome1 $data_root/ivectors_callhome2 \
    $data_root/ivectors_callhome2/plda_scores
fi

# Creating filtered rttm files
if [ $stage -le 7 ]; then
  for name in callhome1 callhome2; do
    data_dir=$data_root/ivectors_${name}
    cat $data_dir/segments | awk '{print $2}' | sort -u > $data_dir/recordings
    grep_or=""
    while IFS= read -r line; do
      grep_or="$grep_or$line\|"
    done < $data_dir/recordings
    grep_or=${grep_or::-2}
    cat $data_root/$name/wav.scp | grep "'$grep_or'" > $data_dir/wav.scp
    cat $data_root/$name/ref.rttm | python python/filter_rttm.py > $data_dir/ref.rttm
  done
fi

if [ $stage -le 8 ]; then
  for name in callhome1 callhome2; do
    data_dir=$data_root/ivectors_${name}
    tuning_dir=$data_root/ivectors_${name}/tuning
    rm -rf $tuning_dir
    mkdir -p $tuning_dir

    echo "Tuning clustering threshold for $name"
    best_der=100
    best_threshold=0

    for threshold in -0.3 -0.2 -0.1 -0.05 0 0.05 0.1 0.2 0.3; do
      diarization/cluster.sh --cmd "$train_cmd --mem 60G" --nj 20 \
        --threshold $threshold $data_dir/plda_scores \
        $data_dir/plda_scores_t$threshold

      md-eval.pl -1 -c 0.25 -r $data_dir/ref.rttm \
        -s $data_dir/plda_scores_t$threshold/rttm \
        2> $tuning_dir/${dataset}_t${threshold}.log \
        > $tuning_dir/${dataset}_t${threshold}

      der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
        $tuning_dir/${dataset}_t${threshold})
      if [ $(perl -e "print ($der < $best_der ? 1 : 0);") -eq 1 ]; then
        best_der=$der
        best_threshold=$threshold
      fi  
    done
    echo "$best_der" > $tuning_dir/best_der
    echo "$best_threshold" > $tuning_dir/best_threshold
  done

  diarization/cluster.sh --cmd "$train_cmd --mem 60G" --nj 20 \
    --threshold $(cat $data_root/ivectors_callhome2/tuning/best_threshold) \
    $data_root/ivectors_callhome1/plda_scores $data_root/ivectors_callhome1/plda_scores

  diarization/cluster.sh --cmd "$train_cmd --mem 60G" --nj 20 \
    --threshold $(cat $data_root/ivectors_callhome1/tuning/best_threshold) \
    $data_root/ivectors_callhome2/plda_scores $data_root/ivectors_callhome2/plda_scores

  results_dir=$data_root/results_callhome
  rm -rf $results_dir
  mkdir -p $results_dir
  cat $data_root/ivectors_callhome1/ref.rttm \
    $data_root/ivectors_callhome2/ref.rttm \
    > $results_dir/ref.rttm
  cat $data_root/ivectors_callhome1/plda_scores/rttm \
    $data_root/ivectors_callhome2/plda_scores/rtmm \
    | md-eval.pl -1 -c 0.25 -r $results_dir/ref.rttm -s - \
      2> $results_dir/threshold.log \
      > $results_dir/DER_threshold.txt
  der=$(grep -oP 'DIARIZATION\ ERROR\ =\ \K[0-9]+([.][0-9]+)?' \
    $results_dir/DER_threshold.txt)
  echo "Using supervised calibration, DER: $der%"
fi

echo "done"

