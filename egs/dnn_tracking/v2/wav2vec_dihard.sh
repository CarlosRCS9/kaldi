#!/usr/bin/env bash

stage=0

dihard_2018_dev=/export/corpora5/LDC/LDC2018E31
dihard_2018_eval=/export/corpora5/LDC/LDC2018E32v1.1

if [ $stage -le 0 ]; then
  # Prepare the development and evaluation set for DIHARD 2018.
  mkdir -p data/dihard
  local/make_dihard_2018_dev.sh $dihard_2018_dev data/dihard_2018_dev
  local/make_dihard_2018_eval.sh $dihard_2018_eval data/dihard_2018_eval
fi
