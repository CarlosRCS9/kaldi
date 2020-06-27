#!/bin/bash


stage=0

if [ $stage -le 0 ]; then
  cd ..
  . ./path.sh
  compute-eer $1
  cd notebooks
fi

