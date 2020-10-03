#!/bin/bash
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

. ./cmd.sh
. ./path.sh
set -e

if [ $# != 1 ]; then
  echo "Usage: $0 <mode>"
  echo " e.g.: $0 vad.scp"
  exit 1
fi

vad_scp=$1

copy-vector scp:$vad_scp ark,t:-
