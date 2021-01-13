#!/usr/bin/env bash
# Copyright 2021 Carlos Castillo
#
# Apache 2.0

if [ $# -lt 2 ]; then
  echo "Usage: $0 <wav-scp> <output-dir> <audio-dir> <force> <utt2dur>"
  echo " e.g.: $0 data/callhome1/wav.scp data/exp000_callhome1 audio false true"
  exit 1
fi

if [ ! -f $1 ]; then
  echo "$1 does not exist"
  exit 1
fi

if [ -f $2 ]; then
  echo "$2 must not be a regular file"
  exit 1
fi

wav_scp=$1
output_dir=$2
mkdir -p $output_dir
audio_dir=${3:-$2}

if [ -f $audio_dir ]; then
  echo "$audio_dir must not be a regular file"
  exit 1
fi

mkdir -p $audio_dir
force=$([ ${4:-false} = true ] && echo true || echo false)
utt2dur_flag=$([ ${5:-true} = true ] && echo true || echo false)

rm -rf $output_dir/wav_tmp.scp
if $utt2dur_flag; then
  rm -rf $output_dir/utt2spk
fi
while IFS= read -r line; do
  recording_id=$(echo $line | cut -d" " -f1)
  command=$(echo $line | cut -d" " -f2-)
  filepath=$audio_dir/${recording_id}.wav
  if $force || [ ! -f $filepath ]; then
    command="${command::-2} $filepath"
    echo $command
    $command
  fi
  echo "$recording_id $(realpath $filepath)" >> $output_dir/wav_tmp.scp
  if $utt2dur_flag; then
    echo "$recording_id $recording_id" >> $output_dir/utt2spk
  fi
done < $wav_scp
mv $output_dir/wav_tmp.scp $output_dir/wav.scp

if $force; then
  rm -rf $output_dir/utt2dur
fi
if $utt2dur_flag; then
 utils/data/get_utt2dur.sh $output_dir 
fi

