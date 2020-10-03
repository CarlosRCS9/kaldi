#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

if [ $# != 2 ]; then
  echo "Usage: $0 <path-to-rtve_2020_test_diarization> <path-to-output>"
  echo " e.g.: $0 /export/corpora5/RTVE/RTVE2020DB/test/audio/SD data/rtve_2020_test_diarization"
fi

data_dir=$1
output_dir=$2

rm -rf $output_dir
mkdir -p $output_dir

for filepath in $(ls -d $data_dir/*.aac); do
  name=$(basename $filepath .aac)

  # ------------------------- utt2spk ------------------------- #
  echo $name $name >> $output_dir/utt2spk

  # ------------------------- wav.scp ------------------------- #
  echo "${name} ffmpeg -i ${filepath} -f wav -ar 16000 -ac 1 - |" \
    >> $output_dir/wav.scp
done

# ------------------------- spk2utt ------------------------- #
cat $output_dir/utt2spk | utils/utt2spk_to_spk2utt.pl > $output_dir/spk2utt

utils/fix_data_dir.sh $output_dir
