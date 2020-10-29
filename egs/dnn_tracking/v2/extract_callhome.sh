#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0

. ./cmd.sh
. ./path.sh
set -e

stage=2

# Make callhome datasets
if [ $stage -le 0 ]; then
  local/make_callhome.sh /export/corpora5/LDC/LDC2001S97/ data
fi

# Make callhome1 and callhome2 ref.rttm
if [ $stage -le 1 ]; then
  for name in callhome1 callhome2; do
    data_dir=data/$name
    recording_ids=$(cat $data_dir/wav.scp | awk '{print $1}')
    recording_ids_grep=$(echo $recording_ids | sed --expression='s/ /\\|/g')
    grep "$recording_ids_grep" data/callhome/fullref.rttm > $data_dir/ref.rttm
  done
fi

# Make callhome1 and callhome2 oracle data directories
if [ $stage -le 2 ]; then
  for name in callhome1 callhome2; do
    data_dir=data/$name
    output_dir=data/${name}_oracle
    rm -rf $output_dir
    mkdir -p $output_dir
    cp $data_dir/{reco2num_spk,ref.rttm,wav.scp} $output_dir/
  done

	for name in callhome1 callhome2; do
		python3 local/make_oracle_vad.py
	done
fi
