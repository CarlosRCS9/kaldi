#!/bin/bash

. ./cmd.sh
. ./path.sh
set -e

stage=0

if [ $stage -le 0 ]; then
  echo reference $1 > exp/reference.1.ark
  echo test $2 > exp/test.1.ark
fi

if [ $stage -le 1 ]; then
  ivector-plda-scoring --print-args=false \
    exp/plda \
    ark:exp/reference.1.ark \
    ark:exp/test.1.ark \
    exp/trials \
    exp/plda_scores
  cat exp/plda_scores
fi
