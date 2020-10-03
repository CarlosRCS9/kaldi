#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e

if [ $# != 1 ]; then
  echo "Usage: $0 <file.scp>"
  exit 1
fi

file_scp=$1
output_file_scp=${file_scp%.*}.txt

copy-matrix \
  scp:$file_scp \
  ark,t:$output_file_scp
