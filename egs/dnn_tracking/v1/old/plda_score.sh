#!/bin/bash

cd ..

. ./cmd.sh
. ./path.sh
set -e

stage=0

if [ $stage -le 0 ]; then
  echo reference $2 > exp/reference.1.ark
  echo test $3 > exp/test.1.ark
  echo reference test > exp/trials
fi

if [ $stage -le 1 ]; then
  ivector-plda-scoring --print-args=false \
    $1 \
    ark:exp/reference.1.ark \
    ark:exp/test.1.ark \
    exp/trials \
    exp/plda_scores
  cat exp/plda_scores
fi

cd notebooks
