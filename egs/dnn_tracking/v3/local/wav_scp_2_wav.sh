#!/usr/bin/env bash

if [ $# -lt 2 ]; then
  echo "Usage: $0 <wav-scp> <output-dir> <audio-dir> <force>"
  echo " e.g.: $0 data/callhome1/wav.scp data/exp000_callhome1 audio false"
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

rm -rf $output_dir/wav_tmp.scp
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
done < $wav_scp

