#!/usr/bin/env bash
# Copyright 2021 Carlos Castillo
#
# Apache 2.0

if [ $# -lt 1 ]; then
  echo "Usage: $0 <data-dir> <output-dir> <audio-dir> <force>"
  echo " e.g.: $0 data/exp000_callhome1 wav2vec_audio data/exp000_wav2vec_callhome1 false"
  exit 1
fi

if [ ! -d $1 ]; then
  echo "$1 does not exist"
  exit 1
fi
data_dir=$1

output_dir=${2:-$data_dir}
if [ -f $output_dir ]; then
  echo "$output_dir must not be a regular file"
  exit 1
fi
mkdir -p $output_dir

audio_dir=${3:-$output_dir}
if [ -f $audio_dir ]; then
  echo "$audio_dir must not be a regular file"
  exit 1
fi
mkdir -p $audio_dir

force=$([ ${4:-false} = true ] && echo true || echo false)

rm -rf $output_dir/wav_tmp.scp
while IFS= read -r line; do
  recording_id=$(echo $line | cut -d" " -f1)
  original_wav_filepath=$(echo $line | cut -d" " -f2-)
  original_wav_filename=$(basename -- "$original_wav_filepath")
  original_wav_filename="${original_wav_filename%.*}"
  new_wav_filepath_no_ext=$audio_dir/$original_wav_filename
  if $force || [ ! -f ${new_wav_filepath_no_ext}.wav ]; then
    command="sox $original_wav_filepath -r 16000 -e floating-point -b 32 ${new_wav_filepath_no_ext}.tmp.wav"
    echo $command
    $command
    mv ${new_wav_filepath_no_ext}.tmp.wav ${new_wav_filepath_no_ext}.wav
  fi
  echo "$recording_id $(realpath ${new_wav_filepath_no_ext}.wav)" >> $output_dir/wav_tmp.scp
done < $data_dir/wav.scp
mv $output_dir/wav_tmp.scp $output_dir/wav.scp
