#!/usr/bin/env bash

. ./path.sh

callhome_root=/export/corpora5/LDC/LDC2001S97
prefix=exp000_
audio_dir=audio

stage=1

if [ $stage -le 0 ]; then
  local/make_callhome.sh $callhome_root data
fi

if [ $stage -le 1 ]; then
  for name in callhome1 callhome2; do
    data_dir=data/$name
    output_dir=data/$prefix$name
    echo "0.01" > $output_dir/frame_shift
    local/wav_scp_2_wav.sh $data_dir/wav.scp $output_dir $audio_dir false
    cp data/callhome/fullref.rttm $output_dir/ref.rttm
    python3 local/fix_ref_rttm.py $output_dir
  done
fi

#test
