#!/bin/bash

. ./cmd.sh
. ./path.sh
set -e

stage=0

if [ $stage -le 0 ]; then
  rm -rf exp/plda_scores
  ivector-plda-scoring \
    exp/plda \
    ark:$1 \
    ark:$2 \
    $3 \
    exp/plda_scores
  cat exp/plda_scores
fi
