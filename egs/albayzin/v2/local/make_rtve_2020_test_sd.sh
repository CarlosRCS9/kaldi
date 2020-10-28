#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

if [ $# != 2 ]; then
  echo "Usage: $0 <path-to-rtve_2020_test_sd> <path-to-output>"
  echo " e.g.: $0 /export/corpora5/RTVE/RTVE2020DB/test/audio/SD data/rtve_2020_test_sd"
fi

data_dir=$1
output_dir=$2
audio_dir=/export/b03/carlosc/repositories/kaldi/egs/albayzin/v2/data/audio

rm -rf $output_dir
mkdir -p $output_dir

for filepath in $(ls -d $data_dir/*.aac); do
  name=$(basename $filepath .aac)

  # ------------------------- utt2spk ------------------------- #
  echo $name $name >> $output_dir/utt2spk

  # ------------------------- wav.scp ------------------------- #
  mkdir -p $audio_dir
  filepath_new=$audio_dir/${name}.wav
  if [ -f $filepath_new ]; then
    echo "$name $filepath_new" \
      >> $output_dir/wav.scp
  else
    echo "$name ffmpeg -i $filepath -f wav -ar 16000 -ac 1 $filepath_new; cat $filepath_new |" \
      >> $output_dir/wav.scp
  fi
done

# ------------------------- spk2utt ------------------------- #
cat $output_dir/utt2spk | utils/utt2spk_to_spk2utt.pl > $output_dir/spk2utt

utils/fix_data_dir.sh $output_dir
