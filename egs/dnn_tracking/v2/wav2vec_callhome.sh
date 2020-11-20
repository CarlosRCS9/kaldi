#!/usr/bin/env bash

. ./cmd.sh
. ./path.sh

stage=3

callhome_root=/export/corpora5/LDC/LDC2001S97
wav_dir=/export/b03/carlosc/data/wav
data_root=data/wav2vec

if [ $stage -le 0 ]; then
  # Prepare the Callhome portion of NIST SRE 2000.
  local/make_callhome.sh $callhome_root data
fi

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

if [ $stage -le 2 ]; then
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

    output_dir=$data_root/$name
    mkdir -p $output_dir
    rm -f $output_dir/wav.scp
    for filepath in $(ls $data_dir/*.wav); do
      filename_no_extension=$(basename $filepath .wav)
      echo "$filename_no_extension $filepath" >> $output_dir/wav.scp
    done
  done
fi

if [ $stage -le 3 ]; then
  for name in callhome1 callhome2; do
    data_dir=$data_root/$name
    python wav2vec_extract.py $data_dir
  done
fi

echo "done"

