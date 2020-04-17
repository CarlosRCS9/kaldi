#!/bin/bash

stage=2

if [ "$#" -ne 3 ]; then
  echo "Illegal number of parameters."
  echo "Usage: ./super_script /export/c03/carloscastillo/data/callhome1/augmented groundtruth/callhome1/ref.rttm data/callhome1/wav.scp"
  exit 1
fi

if [ $stage -le 1 ]; then
  cat $2 \
    | python3 scripts/rttm_remove_overlap.py --min-segment=0.0 --output-mode=json \
    | python3 scripts/json_augment_audio.py $3 $1/
fi

if [ $stage -le 2 ]; then
  cat $1/segments_augmented.json \
    | python3 split_segments.py json --length=1.0 --overlap=0.5 --min-segment=0.5 > $1/segments_augmented_1.0_0.5.json
  cat $1/segments_augmented.json \
    | python3 scripts/json_to_rttm.py --overlap-speaker=false > $1/segments_augmented.rttm
fi

if [ $stage -le 3 ]; then
  mkdir $1/json
  cat $1/segments_augmented_1.0_0.5.json \
    | python3 extract_features.py json $1 $1
fi
